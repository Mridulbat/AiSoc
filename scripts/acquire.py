"""Setup-time downloads only. Never called by the application."""

import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

SOURCES = {
    "sms": ("https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip", "SMSSpamCollection"),
    "url": (
        "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip",
        "PhiUSIIL_Phishing_URL_Dataset.csv",
    ),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=SOURCES)
    parser.add_argument("--output", default="data")
    args = parser.parse_args()
    url, name = SOURCES[args.kind]
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=120) as response:
        raw = response.read(100_000_001)
    if len(raw) > 100_000_000:
        raise ValueError("Download exceeds 100 MB")
    with ZipFile(io.BytesIO(raw)) as archive:
        member = next(n for n in archive.namelist() if n.endswith(name))
        if archive.getinfo(member).file_size > 150_000_000:
            raise ValueError("Dataset exceeds unpacked limit")
        (target / name).write_bytes(archive.read(member))
    (target / (args.kind + "-source.json")).write_text(
        json.dumps(
            dict(
                source=url,
                archive_sha256=hashlib.sha256(raw).hexdigest(),
                file_sha256=hashlib.sha256((target / name).read_bytes()).hexdigest(),
                license="CC BY 4.0 (UCI listing)",
                file=name,
            ),
            indent=2,
        )
    )
    print("Downloaded", name)


if __name__ == "__main__":
    main()
