#!/usr/bin/env python3
"""Privacy and confidentiality check for this public repo.

Looks for things a secret scanner does not: personal home-folder paths, email
addresses, confidential or NDA material, signing keys and local config files,
and very large files. Run it with no arguments to scan every tracked file, or
pass file paths to scan only those (CI passes the files a pull request
changes).

A line can opt out with the marker `privacy-check: allow` in a comment, for a
match that has been checked and is fine to publish.

Exit code 1 means at least one problem was found.
"""
import os
import re
import subprocess
import sys

ALLOW_MARKER = "privacy-check: allow"
MAX_BYTES = 20 * 1024 * 1024  # GitHub warns at 50 MB; anything this big deserves a look

# This script and the security docs describe the patterns, so skip them.
SKIP_FILES = {
    ".github/scripts/privacy-check.py",
    "SECURITY.md",
    "docs/security.md",
}

# File names that should never be committed.
BAD_NAMES = [
    (re.compile(r"(^|/)\.env(\..*)?$"), "environment file (may hold secrets)"),
    (re.compile(r"\.(pem|key|p12|pfx|jks|keystore|p8|ppk|asc|gpg)$", re.I), "key or certificate file"),
    (re.compile(r"(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$"), "SSH key"),
    (re.compile(r"(^|/)local\.properties$"), "local Android SDK config (contains a home path)"),
    (re.compile(r"(^|/)google-services\.json$"), "Firebase config"),
    (re.compile(r"(^|/)\.kicad_prl$|\.kicad_prl$"), "KiCad per-user settings"),
    (re.compile(r"(confidential|\bnda\b|under[-_ ]nda)", re.I), "file name says confidential/NDA"),
    (re.compile(r"datasheet.*\.pdf$|(^|/)DS[-_ ]?\d+.*\.pdf$|_DS\d+.*\.pdf$", re.I),
     "vendor datasheet PDF (often licensed or confidential; link to it instead)"),
]

# Text patterns checked line by line.
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_OK = re.compile(
    r"(noreply|no-reply)@|@users\.noreply\.github\.com$|@example\.(com|org|net)$|"
    r"@localhost$|@\d+x\.(png|jpg)$|\.(png|jpg|svg|gif)$",
    re.I,
)
TEXT_RULES = [
    (re.compile(r"/Users/(?!Shared/)[A-Za-z0-9._-]+/"), "macOS home-folder path (shows a user name)"),
    (re.compile(r"/home/(?!runner/|user/|ubuntu/)[A-Za-z0-9._-]+/"), "Linux home-folder path (shows a user name)"),
    (re.compile(r"[A-Za-z]:\\+Users\\+(?!Public\\)[A-Za-z0-9._ -]+\\", re.I), "Windows home-folder path (shows a user name)"),
    (re.compile(r"CloudStorage/|SynologyDrive|OneDrive -|Dropbox/|Google Drive/"), "path into a personal cloud drive"),
    (re.compile(r"\b(CONFIDENTIAL|PROPRIETARY|NOT FOR (PUBLIC )?DISTRIBUTION|UNDER NDA)\b"),
     "confidentiality marking (check the source allows publishing)"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\b(storePassword|keyPassword|signingConfigs?\s*\{[^}]*password)\s*[=:]?\s*[\"'][^\"']+[\"']"),
     "signing password in build file"),
]


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def is_binary(data):
    return b"\0" in data[:8192]


def annotate(path, line, msg):
    # GitHub Actions turns this into an inline annotation on the PR.
    loc = f"file={path}" + (f",line={line}" if line else "")
    print(f"::error {loc}::{msg}")


def check(path):
    problems = 0
    if path in SKIP_FILES or not os.path.isfile(path):
        return 0
    for rx, why in BAD_NAMES:
        if rx.search(path):
            annotate(path, None, why)
            problems += 1
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        annotate(path, None, f"large file ({size // (1024 * 1024)} MB): check it belongs in git")
        problems += 1
    with open(path, "rb") as f:
        data = f.read()
    if is_binary(data):
        # Binary files (PDF, PNG, STEP...) can still carry a user name in metadata.
        for rx, why in TEXT_RULES[:4]:
            if re.search(rx.pattern.encode(), data):
                annotate(path, None, f"{why} inside binary file metadata")
                problems += 1
        return problems
    for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
        if ALLOW_MARKER in line:
            continue
        # KiCad files embed base64 images; skip very long lines with no spaces.
        if len(line) > 400 and " " not in line.strip():
            continue
        for rx, why in TEXT_RULES:
            if rx.search(line):
                annotate(path, n, why)
                problems += 1
        for m in EMAIL.finditer(line):
            if not EMAIL_OK.search(m.group(0)):
                annotate(path, n, "email address (use a GitHub noreply address or remove it)")
                problems += 1
    return problems


def main(argv):
    files = argv[1:] or tracked_files()
    total = sum(check(p) for p in files)
    print(f"privacy-check: scanned {len(files)} file(s), {total} problem(s)")
    if total:
        print("Fix the lines above, or add 'privacy-check: allow' on a line that is fine to publish.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
