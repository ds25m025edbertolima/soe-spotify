#!/usr/bin/env python
"""Verify ETL setup and dependencies."""

import sys
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Load config directly to handle directory naming issues
config_path = PROJECT_ROOT / "soe-spotify" / "config.py"
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


def check_csv_files() -> bool:
    print("Checking CSV files...")
    files = {
        "Albums": config.CSV_ALBUMS,
        "Artists": config.CSV_ARTISTS,
        "Tracks": config.CSV_TRACKS,
        "Audio Features": config.CSV_AUDIO_FEATURES,
        "Lyrics Features": config.CSV_LYRICS_FEATURES,
    }

    all_exist = True
    for name, path in files.items():
        exists = path.exists()
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status} ({path})")
        all_exist = all_exist and exists

    return all_exist


def check_firebase_credentials() -> bool:
    print("\nChecking Firebase credentials...")
    exists = config.FIREBASE_CREDENTIALS.exists()
    status = "OK" if exists else "MISSING"
    print(f"  Service Account: {status} ({config.FIREBASE_CREDENTIALS})")
    return exists


def check_dependencies() -> bool:
    print("\nChecking Python dependencies...")
    dependencies = {
        "pyspark": "PySpark",
        "firebase_admin": "Firebase Admin",
        "pandas": "Pandas",
        "pyarrow": "PyArrow",
    }

    all_installed = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  {name}: OK")
        except ImportError:
            print(f"  {name}: MISSING")
            all_installed = False

    return all_installed


def main() -> int:
    print("=" * 60)
    print("ETL Setup Verification")
    print("=" * 60)

    csv_ok = check_csv_files()
    firebase_ok = check_firebase_credentials()
    deps_ok = check_dependencies()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  CSV Files: {'OK' if csv_ok else 'FAILED'}")
    print(f"  Firebase: {'OK' if firebase_ok else 'FAILED'}")
    print(f"  Dependencies: {'OK' if deps_ok else 'FAILED'}")
    print("=" * 60)

    if csv_ok and firebase_ok and deps_ok:
        print("\nSetup verified! Ready to run ETL pipeline.")
        print("  $ make etl")
        return 0
    else:
        print("\nSetup incomplete. Please fix the issues above.")
        if not deps_ok:
            print("  $ make requirements")
        return 1


if __name__ == "__main__":
    sys.exit(main())
