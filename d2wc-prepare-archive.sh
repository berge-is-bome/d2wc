#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/berge-is-bome/d2wc.git}"
BRANCH="${BRANCH:-main}"
WORKDIR="${WORKDIR:-$HOME/d2wc}"
ARCHIVE="${ARCHIVE:-/tmp/d2wc.tgz}"
INSTALLER_COPY="${INSTALLER_COPY:-/tmp/d2wc-installation.sh}"

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git fetch origin --prune
  git switch "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  rm -rf -- "$WORKDIR"
  git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$WORKDIR"
  cd "$WORKDIR"
fi

git archive --format=tar --prefix=d2wc/ HEAD | gzip > "$ARCHIVE"
cp -- d2wc-installation.sh "$INSTALLER_COPY"

cat <<EOF
Prepared d2wc archive and dom0 installer copy.

Archive:
  $ARCHIVE

Installer script:
  $INSTALLER_COPY

In dom0, copy the installer from this VM, edit the VM value if needed, then run it.
EOF
