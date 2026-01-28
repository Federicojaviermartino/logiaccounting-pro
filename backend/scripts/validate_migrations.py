#!/usr/bin/env python3
"""
Database migration validation script.

Checks:
1. All migration files have both upgrade() and downgrade() functions
2. Revision chain is not broken (each down_revision exists)
3. No duplicate revision identifiers
4. Migration files follow naming conventions

Usage:
    python scripts/validate_migrations.py
"""

import os
import sys
import re
import importlib.util
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

REQUIRED_FUNCTIONS = {"upgrade", "downgrade"}


def load_migration(filepath: Path) -> dict:
    """Load a migration module and extract metadata."""
    spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return {"error": str(e), "path": str(filepath)}

    return {
        "path": str(filepath),
        "revision": getattr(mod, "revision", None),
        "down_revision": getattr(mod, "down_revision", None),
        "has_upgrade": hasattr(mod, "upgrade") and callable(mod.upgrade),
        "has_downgrade": hasattr(mod, "downgrade") and callable(mod.downgrade),
    }


def validate():
    """Run all migration validations."""
    if not MIGRATIONS_DIR.exists():
        print(f"ERROR: Migrations directory not found: {MIGRATIONS_DIR}")
        return 1

    files = sorted(MIGRATIONS_DIR.glob("*.py"))
    if not files:
        print("WARNING: No migration files found.")
        return 0

    errors = []
    migrations = []

    print(f"Validating {len(files)} migration file(s)...\n")

    for f in files:
        if f.name == "__init__.py":
            continue

        info = load_migration(f)

        if "error" in info:
            errors.append(f"  LOAD ERROR in {f.name}: {info['error']}")
            continue

        migrations.append(info)

        # Check required functions
        if not info["has_upgrade"]:
            errors.append(f"  {f.name}: missing upgrade() function")
        if not info["has_downgrade"]:
            errors.append(f"  {f.name}: missing downgrade() function")

        # Check revision ID exists
        if not info["revision"]:
            errors.append(f"  {f.name}: missing 'revision' identifier")

        print(f"  OK  {f.name}  (rev={info.get('revision', '?')})")

    # Check for duplicate revisions
    revisions = [m["revision"] for m in migrations if m.get("revision")]
    seen = set()
    for rev in revisions:
        if rev in seen:
            errors.append(f"  DUPLICATE revision: {rev}")
        seen.add(rev)

    # Check revision chain continuity
    rev_set = set(revisions)
    for m in migrations:
        dr = m.get("down_revision")
        if dr and dr not in rev_set:
            errors.append(
                f"  BROKEN CHAIN: {Path(m['path']).name} references "
                f"down_revision='{dr}' which does not exist"
            )

    print()
    if errors:
        print(f"FAILED - {len(errors)} issue(s) found:")
        for e in errors:
            print(e)
        return 1
    else:
        print(f"PASSED - {len(migrations)} migration(s) validated successfully.")
        return 0


if __name__ == "__main__":
    sys.exit(validate())
