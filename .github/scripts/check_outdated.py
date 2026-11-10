"""Fail when the Gradle dependency report lists outdated (non-prerelease) dependencies."""
import json
import sys

report = json.load(open(sys.argv[1]))
outdated = report.get("outdated", {}).get("dependencies", [])
for d in outdated:
    print(f"::error::Outdated: {d['group']}:{d['name']} {d['version']} -> {d['available'].get('release') or d['available'].get('milestone')}")
print(f"{len(outdated)} outdated dependencies")
sys.exit(1 if outdated else 0)
