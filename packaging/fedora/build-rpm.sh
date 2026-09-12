#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="$(sed -n 's/^__version__ = "\([^"]*\)"/\1/p' "$project_dir/src/voxtype/__init__.py")"
topdir="$project_dir/packaging/fedora/rpmbuild"
model="$topdir/SOURCES/ggml-base.en.bin"
model_metadata="$project_dir/packaging/models.json"
model_url="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["base.en"]["url"])' "$model_metadata")"
model_sha256="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["base.en"]["sha256"])' "$model_metadata")"

mkdir -p "$topdir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

tar \
    --exclude='.git' \
    --exclude='dist' \
    --exclude='packaging/fedora/rpmbuild' \
    --transform="s,^,voxtype-$version/," \
    -czf "$topdir/SOURCES/voxtype-$version.tar.gz" \
    -C "$project_dir" .

if ! test -f "$model" || ! printf '%s  %s\n' "$model_sha256" "$model" | sha256sum --check --status; then
    curl --fail --location --retry 3 --output "$model" "$model_url"
fi
printf '%s  %s\n' "$model_sha256" "$model" | sha256sum --check
sed "s/@VERSION@/$version/" \
    "$project_dir/packaging/fedora/voxtype.spec.in" > "$topdir/SPECS/voxtype.spec"

if command -v toolbox >/dev/null && toolbox list 2>/dev/null | grep -q fedora-toolbox-43; then
    toolbox run -c fedora-toolbox-43 sudo dnf install -y \
        python3-devel python3-dbus-next python3-hatchling pyproject-rpm-macros \
        rpm-build systemd-rpm-macros
    toolbox run -c fedora-toolbox-43 rpmbuild --define "_topdir $topdir" -ba "$topdir/SPECS/voxtype.spec"
else
    rpmbuild --define "_topdir $topdir" -ba "$topdir/SPECS/voxtype.spec"
fi

app_rpm="$(find "$topdir/RPMS" -type f -name "voxtype-$version-*.rpm" -print -quit)"
model_rpm="$(find "$topdir/RPMS" -type f -name "voxtype-model-base-en-$version-*.rpm" -print -quit)"
source_rpm="$(find "$topdir/SRPMS" -type f -name "voxtype-$version-*.src.rpm" -print -quit)"

# Keep the build output unambiguous: one application RPM, one model RPM, and
# one source RPM for the version that was just built.
find "$topdir/RPMS" -type f -name 'voxtype-*.rpm' \
    ! -path "$app_rpm" ! -path "$model_rpm" -delete
find "$topdir/SRPMS" -type f -name 'voxtype-*.src.rpm' \
    ! -path "$source_rpm" -delete

current_dir="$topdir/RPMS/current"
mkdir -p "$current_dir"
ln -sfn "$(realpath --relative-to="$current_dir" "$app_rpm")" "$current_dir/voxtype.rpm"
ln -sfn "$(realpath --relative-to="$current_dir" "$model_rpm")" \
    "$current_dir/voxtype-model-base-en.rpm"

printf '%s\n' \
    "$current_dir/voxtype.rpm" \
    "$current_dir/voxtype-model-base-en.rpm" \
    "$source_rpm"
