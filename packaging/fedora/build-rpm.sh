#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="$(sed -n 's/^version = "\([^"]*\)"/\1/p' "$project_dir/pyproject.toml" | head -n1)"
topdir="$project_dir/packaging/fedora/rpmbuild"
model="$topdir/SOURCES/ggml-base.en.bin"
model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/5359861c739e955e79d9a303bcbc70fb988958b1/ggml-base.en.bin"
model_sha256="a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002"

mkdir -p "$topdir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

tar \
    --exclude='.git' \
    --exclude='dist' \
    --exclude='native/voxtype-ctl/target' \
    --exclude='packaging/fedora/rpmbuild' \
    --transform="s,^,voxtype-$version/," \
    -czf "$topdir/SOURCES/voxtype-$version.tar.gz" \
    -C "$project_dir" .

if ! test -f "$model" || ! printf '%s  %s\n' "$model_sha256" "$model" | sha256sum --check --status; then
    curl --fail --location --retry 3 --output "$model" "$model_url"
fi
printf '%s  %s\n' "$model_sha256" "$model" | sha256sum --check
install -m 0644 "$project_dir/packaging/fedora/voxtype.spec" "$topdir/SPECS/voxtype.spec"

if command -v toolbox >/dev/null && toolbox list 2>/dev/null | grep -q fedora-toolbox-43; then
    toolbox run -c fedora-toolbox-43 sudo dnf install -y \
        cargo python3-devel python3-dbus-next python3-hatchling pyproject-rpm-macros \
        rpm-build rust systemd-rpm-macros
    toolbox run -c fedora-toolbox-43 rpmbuild --define "_topdir $topdir" -ba "$topdir/SPECS/voxtype.spec"
else
    rpmbuild --define "_topdir $topdir" -ba "$topdir/SPECS/voxtype.spec"
fi

find "$topdir/RPMS" "$topdir/SRPMS" -type f -name '*.rpm' -print
