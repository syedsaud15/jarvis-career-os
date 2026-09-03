"""Run from repository root: python -m scripts.export_backup --output FILE"""
import argparse
from app.backup import build_backup, write_backup
from app.config import get_settings
from app.store import Store

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export career data, never OAuth credentials")
    parser.add_argument("--output", required=True)
    parser.add_argument("--sender", default="dashboard-user")
    args = parser.parse_args()
    settings = get_settings()
    write_backup(build_backup(Store(settings.database_path, settings.database_url), args.sender), args.output)
    print("Career backup exported. Store this file privately.")
