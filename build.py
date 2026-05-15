#!/usr/bin/env python3

from pathlib import Path
from urllib.request import urlopen
import re


SOURCE_URL = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"

ROOT = Path(__file__).resolve().parent
GROUPS_FILE = ROOT / "groups.txt"

DIST_DIR = ROOT / "dist"
RUSSIA_INSIDE_OUT_FILE = DIST_DIR / "russia-inside-custom.lst"


GROUP_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def normalize_domain(value: str) -> str | None:
    value = value.strip().lower()

    if not value:
        return None

    if value.startswith("#") or value.startswith("//"):
        return None

    if "#" in value:
        value = value.split("#", 1)[0].strip()

    if "//" in value:
        value = value.split("//", 1)[0].strip()

    value = value.lstrip(".")

    return value or None


def normalize_group_name(value: str) -> str:
    value = value.strip().lower()

    if value.endswith(":"):
        value = value[:-1].strip()

    if not GROUP_NAME_RE.match(value):
        raise ValueError(
            f"Invalid group name: {value!r}. "
            "Use only letters, numbers, dash and underscore."
        )

    return value


def load_groups() -> dict[str, set[str]]:
    if not GROUPS_FILE.exists():
        raise FileNotFoundError(f"Missing file: {GROUPS_FILE}")

    groups: dict[str, set[str]] = {}
    current_group: str | None = None

    for line_number, raw_line in enumerate(
        GROUPS_FILE.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#") or line.startswith("//"):
            continue

        if line.endswith(":"):
            current_group = normalize_group_name(line)
            groups.setdefault(current_group, set())
            continue

        if current_group is None:
            raise ValueError(
                f"Domain without group at line {line_number}: {raw_line!r}"
            )

        domain = normalize_domain(line)

        if domain:
            groups[current_group].add(domain)

    return groups


def should_remove_from_russia_inside(domain: str, special_domains: set[str]) -> bool:
    for special_domain in special_domains:
        if domain == special_domain:
            return True

        if domain.endswith("." + special_domain):
            return True

    return False


def fetch_russia_inside_domains() -> set[str]:
    with urlopen(SOURCE_URL, timeout=60) as response:
        source_text = response.read().decode("utf-8", errors="replace")

    domains = set()

    for line in source_text.splitlines():
        domain = normalize_domain(line)

        if domain:
            domains.add(domain)

    return domains


def write_list(path: Path, domains: set[str]) -> None:
    content = "\n".join(sorted(domains))

    if content:
        content += "\n"

    path.write_text(content, encoding="utf-8")


def clean_old_generated_lists() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    for path in DIST_DIR.glob("*.lst"):
        path.unlink()


def main() -> None:
    groups = load_groups()
    original_domains = fetch_russia_inside_domains()

    all_special_domains = set()

    for domains in groups.values():
        all_special_domains.update(domains)

    custom_russia_inside = {
        domain
        for domain in original_domains
        if not should_remove_from_russia_inside(domain, all_special_domains)
    }

    removed_domains = original_domains - custom_russia_inside

    clean_old_generated_lists()

    for group_name, domains in sorted(groups.items()):
        write_list(DIST_DIR / f"{group_name}.lst", domains)

    write_list(RUSSIA_INSIDE_OUT_FILE, custom_russia_inside)

    print("Build complete")
    print(f"Original Russia inside domains: {len(original_domains)}")
    print(f"Groups: {len(groups)}")
    print(f"Special domains total: {len(all_special_domains)}")
    print(f"Removed from Russia inside: {len(removed_domains)}")
    print(f"Custom Russia inside domains: {len(custom_russia_inside)}")
    print("")

    print("Created group lists:")
    for group_name, domains in sorted(groups.items()):
        print(f"- dist/{group_name}.lst: {len(domains)} domains")

    print("")
    print(f"Created: {RUSSIA_INSIDE_OUT_FILE}")

    if removed_domains:
        print("")
        print("Removed domains from Russia inside:")
        for domain in sorted(removed_domains):
            print(f"- {domain}")


if __name__ == "__main__":
    main()
