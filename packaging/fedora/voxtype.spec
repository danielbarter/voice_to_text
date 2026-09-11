Name:           voxtype
Version:        0.2.0
Release:        1%{?dist}
Summary:        Private local voice typing for the COSMIC desktop

License:        MIT
Source0:        %{name}-%{version}.tar.gz
Source1:        ggml-base.en.bin

BuildRequires:  cargo
BuildRequires:  python3-devel
BuildRequires:  python3-dbus-next
BuildRequires:  python3-hatchling
BuildRequires:  pyproject-rpm-macros
BuildRequires:  rust
BuildRequires:  systemd-rpm-macros

Requires:       libcanberra-gtk3
Requires:       pipewire-utils
Requires:       python3-dbus-next
Requires:       python3-pywhispercpp
Requires:       wtype
Recommends:     %{name}-model-base-en = %{version}-%{release}
Suggests:       cosmic-settings

%description
VoxType provides low-latency, entirely local dictation on COSMIC and other
Wayland desktops. A native shortcut client controls a warm Whisper daemon,
which records from PipeWire and types through the Wayland virtual keyboard.

%package model-base-en
Summary:        Offline base.en speech model for VoxType
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}

%description model-base-en
The quantized Whisper base.en model used for offline English dictation.

%prep
%autosetup -n %{name}-%{version}

%build
%pyproject_wheel
cargo build --release --locked --offline --manifest-path native/voxtype-ctl/Cargo.toml

%install
%pyproject_install
%pyproject_save_files voxtype
install -Dpm0755 native/voxtype-ctl/target/release/voxtype-ctl \
    %{buildroot}%{_bindir}/voxtype-ctl
install -Dpm0644 data/dev.voxtype.VoxType.desktop \
    %{buildroot}%{_datadir}/applications/dev.voxtype.VoxType.desktop
install -Dpm0644 packaging/voxtype.service \
    %{buildroot}%{_userunitdir}/voxtype.service
install -Dpm0644 %{SOURCE1} \
    %{buildroot}%{_datadir}/voxtype/models/ggml-base.en.bin

%check
%pyproject_check_import

%post
%systemd_user_post voxtype.service

%preun
%systemd_user_preun voxtype.service

%postun
%systemd_user_postun_with_restart voxtype.service

%files -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/voxtype
%{_bindir}/voxtype-ctl
%{_datadir}/applications/dev.voxtype.VoxType.desktop
%{_userunitdir}/voxtype.service

%files model-base-en
%license LICENSE
%{_datadir}/voxtype/

%changelog
* Fri Sep 11 2026 VoxType maintainers - 0.2.0-1
- Initial Fedora package
