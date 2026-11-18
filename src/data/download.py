"""Download raw data into data/raw/. Owner: Yifan."""
import subprocess
import requests
from src.config import RAW, SOURCES

# BLS and DOL reject requests without a browser-like User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0 (CS6140 student project)"}


def fetch(url: str, name: str | None = None) -> None:
    name = name or url.rsplit("/", 1)[-1]
    dest = RAW / name
    if dest.exists():
        print(f"skip {name} (exists)")
        return
    print(f"downloading {url}")
    r = requests.get(url, headers=HEADERS, timeout=600)
    r.raise_for_status()
    dest.write_bytes(r.content)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    o = SOURCES["oews"]
    fetch(o["url"], o["file"])
    fetch(o["area_definitions_url"], o["area_definitions_file"])
    for url in SOURCES["lca"]["train_urls"] + SOURCES["lca"]["shift_urls"]:
        fetch(url)
    fetch(SOURCES["onet"]["url"], SOURCES["onet"]["file"])
    subprocess.run(["kaggle", "datasets", "download", "-d", SOURCES["kaggle"]["dataset"],
                    "-p", str(RAW / "linkedin"), "--unzip"], check=True)


if __name__ == "__main__":
    main()
