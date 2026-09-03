"""Offline recovery drill; deliberately cannot overwrite or connect to production."""
import argparse
import json
from pathlib import Path
from app.backup import restore_backup

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore version 2 backup into a NEW local SQLite database")
    parser.add_argument("backup")
    parser.add_argument("--destination", required=True)
    args = parser.parse_args()
    restore_backup(json.loads(Path(args.backup).read_text(encoding="utf-8")), args.destination)
    print("Career data restored and integrity checked. Google credentials were not restored.")
