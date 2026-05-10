#!/usr/bin/env python3

from pathlib import Path
from urllib.request import urlopen


SOURCE_URL = "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst"

ROOT = Path(__file__).resolve().parent
SPECIAL_FILE = ROOT / "special.txt"

DIST_DIR = ROOT / "dist"
SPECIAL_OUT_FILE = DIST_DIR / "special.lst"
RUSSIA_INSIDE_OUT_FILE = DIST_DIR / "russia-inside-custom.lst"


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


def load_special_domains() -> set[str]:
    if not SPECIAL_FILE.exists():
        return set()

    domains = set()

    for line in SPECIAL_FILE.read_text(encoding="utf-8").splitlines():
        domain = normalize_domain(line)

        if domain:
            domains.add(domain)

    return domains


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


def main() -> None:
    special_domains = load_special_domains()
    original_domains = fetch_russia_inside_domains()

    custom_russia_inside = {
        domain
        for domain in original_domains
        if not should_remove_from_russia_inside(domain, special_domains)
    }

    removed_domains = original_domains - custom_russia_inside

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    write_list(SPECIAL_OUT_FILE, special_domains)
    write_list(RUSSIA_INSIDE_OUT_FILE, custom_russia_inside)

    print("Build complete")
    print(f"Original Russia inside domains: {len(original_domains)}")
    print(f"Special domains: {len(special_domains)}")
    print(f"Removed from Russia inside: {len(removed_domains)}")
    print(f"Custom Russia inside domains: {len(custom_russia_inside)}")
    print(f"Created: {SPECIAL_OUT_FILE}")
    print(f"Created: {RUSSIA_INSIDE_OUT_FILE}")

    if removed_domains:
        print("")
        print("Removed domains:")
        for domain in sorted(removed_domains):
            print(f"- {domain}")


if __name__ == "__main__":
    main()
