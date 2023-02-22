#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	doc		# build without docs

Summary:	Cross-platform, fast, feature full, GPU based terminal emulator
Name:		kitty
Version:	0.27.1
Release:	1
# BSD:          docs/_templates/searchbox.html
# zlib:         glfw/
License:	GPLv3 and zlib and BSD
Source0:	https://github.com/kovidgoyal/kitty/releases/download/v%{version}/%{name}-%{version}.tar.xz
# Source0-md5:	3e24876ca288589dfab398de81b02614
# Add AppData manifest file
# * https://github.com/kovidgoyal/kitty/pull/2088
Source1:	%{name}.appdata.xml
Source2:	%{name}.sh
Source3:	%{name}.fish
%if 0
go mod vendor
tar -caf ~/kitty-vendor.tar.xz vendor
%endif
Source4:	%{name}-%{version}-vendor.tar.xz
# Source4-md5:	f6aac2e7f2b6a58e468a160899d823c2
Patch0:		num-workers.patch
Patch1:		go-vendor.patch
URL:		https://sw.kovidgoyal.net/kitty
BuildRequires:	appstream-glib
BuildRequires:	dbus-devel
BuildRequires:	desktop-file-utils
BuildRequires:	fontconfig-devel
BuildRequires:	gcc
BuildRequires:	gnupg2
BuildRequires:	golang >= 1.20
BuildRequires:	harfbuzz-devel >= 2.2
BuildRequires:	lcms2-devel
BuildRequires:	libcanberra-devel
BuildRequires:	libglvnd-libGL-devel
BuildRequires:	libpng-devel
BuildRequires:	librsync-devel
BuildRequires:	ncurses
BuildRequires:	openssl-devel
BuildRequires:	python3-devel >= 1:3.8
BuildRequires:	python3dist(setuptools)
BuildRequires:	rpm-build >= 4.6
BuildRequires:	rpmbuild(macros) >= 2.023
BuildRequires:	wayland-devel
BuildRequires:	wayland-protocols
BuildRequires:	xorg-lib-libXcursor-devel
BuildRequires:	xorg-lib-libXi-devel
BuildRequires:	xorg-lib-libXinerama-devel
BuildRequires:	xorg-lib-libXrandr-devel
BuildRequires:	xorg-lib-libxkbcommon-x11-devel
BuildRequires:	zlib-devel
%if %{with docs}
BuildRequires:	python3dist(sphinx)
BuildRequires:	python3dist(sphinx-copybutton)
BuildRequires:	python3dist(sphinx-inline-tabs)
# Missing in pld
#BuildRequires:	python3dist(sphinxext-opengraph)
%endif
%if %{with tests}
BuildRequires:	/usr/bin/getent
BuildRequires:	/usr/bin/ssh
%endif
Requires:	hicolor-icon-theme
Requires:	python3
Suggests:	%{name}-bash-integration
Suggests:	%{name}-fish-integration
# Terminfo file has been split from the main program and is required for use
# without errors. It has been separated to support SSH into remote machines using
# kitty as per the maintainers suggestion. Install the terminfo file on the remote
# machine.
Requires:	%{name}-terminfo = %{version}-%{release}
# Very weak dependencies, these are required to enable all features of kitty's
# "kittens" functions install separately
Recommends:	python3-pygments
Suggests:	ImageMagick
ExclusiveArch:	%go_arches
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define	specflags	-Wno-array-bounds

%description
- Offloads rendering to the GPU for lower system load and buttery
  smooth scrolling. Uses threaded rendering to minimize input latency.
- Supports all modern terminal features: graphics (images), unicode,
  true-color, OpenType ligatures, mouse protocol, focus tracking,
  bracketed paste and several new terminal protocol extensions.
- Supports tiling multiple terminal windows side by side in different
  layouts without needing to use an extra program like tmux.
- Can be controlled from scripts or the shell prompt, even over SSH.
- Has a framework for Kittens, small terminal programs that can be
  used to extend kitty's functionality. For example, they are used for
  Unicode input, Hints and Side-by-side diff.
- Supports startup sessions which allow you to specify the window/tab
  layout, working directories and programs to run on startup.
- Cross-platform: kitty works on Linux and macOS, but because it uses
  only OpenGL for rendering, it should be trivial to port to other
  Unix-like platforms.
- Allows you to open the scrollback buffer in a separate window using
  arbitrary programs of your choice. This is useful for browsing the
  history comfortably in a pager or editor.
- Has multiple copy/paste buffers, like vim.

%package bash-integration
Summary:	Automatic Bash integration for Kitty Terminal
BuildArch:	noarch

%description bash-integration
Cross-platform, fast, feature full, GPU based terminal emulator.

Bash integration for Kitty Terminal.

%package fish-integration
Summary:	Automatic Fish integration for Kitty Terminal
BuildArch:	noarch

%description fish-integration
Cross-platform, fast, feature full, GPU based terminal emulator.

Fish integration for Kitty Terminal.

%package terminfo
Summary:	The terminfo file for Kitty Terminal
Requires:	ncurses
BuildArch:	noarch

%description    terminfo
Cross-platform, fast, feature full, GPU based terminal emulator.

The terminfo file for Kitty Terminal.

%package doc
Summary:	Documentation for %{name}

%description doc
This package contains the documentation for %{name}.

%prep
%autosetup -p1 -a4

# Changing sphinx theme to classic
sed "s/html_theme = 'furo'/html_theme = 'classic'/" -i docs/conf.py

find -type f -name "*.py" | xargs sed -i \
	-e 's|%{_bindir}/env python3|%{__python3}|g' \
	-e 's|%{_bindir}/env python|%{__python3}|g' \
	-e 's|%{_bindir}/env -S kitty|%{_bindir}/kitty|g' \
	%{nil}

# non-executable-script
sed -e "s/f.endswith('\.so')/f.endswith('\.so') or f.endswith('\.py')/g" -i setup.py

# script-without-shebang '__init__.py'
find -type f -name "*.py*" | xargs chmod a-x

%install
rm -rf $RPM_BUILD_ROOT
%set_build_flags
export CC="%{__cc}"
export CXX="%{__cxx}"
export NUM_WORKERS=1
%{__python3} setup.py linux-package \
    %{nil}

install -Dp %{SOURCE1} $RPM_BUILD_ROOT%{_metainfodir}/%{name}.appdata.xml

install -Dp %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/%{name}.sh
install -Dp %{SOURCE3} $RPM_BUILD_ROOT%{fish_compdir}/%{name}.fish

sed 's|KITTY_INSTALLATION_DIR=.*|KITTY_INSTALLATION_DIR="%{_libdir}/%{name}"|' \
 -i $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/%{name}.sh
sed 's|set -l KITTY_INSTALLATION_DIR .*|set -l KITTY_INSTALLATION_DIR "%{_libdir}/%{name}"|' \
 -i $RPM_BUILD_ROOT%{fish_compdir}/%{name}.fish

# script-without-shebang '__init__.py'
find $RPM_BUILD_ROOT -type f -name "*.py*" ! -name askpass.py | xargs chmod a-x

%if %{with doc}
# rpmlint fixes
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/html/.buildinfo \
	$RPM_BUILD_ROOT%{_docdir}/%{name}/html/.nojekyll
%endif

%if %{with tests}
# Some tests ignores PATH env...
install -d kitty/launcher
ln -s $RPM_BUILD_ROOT%{_bindir}/%{name} kitty/launcher
export PATH=$RPM_BUILD_ROOT%{_bindir}:$PATH
%{__python3} setup.py test          \
    --prefix=$RPM_BUILD_ROOT%{_prefix}
%endif

appstream-util validate-relax --nonet $RPM_BUILD_ROOT%{_metainfodir}/*.xml
desktop-file-validate $RPM_BUILD_ROOT%{_desktopdir}/*.desktop

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc LICENSE
%attr(755,root,root) %{_bindir}/kitten
%attr(755,root,root) %{_bindir}/kitty
%{_desktopdir}/kitty-open.desktop
%{_desktopdir}/kitty.desktop
%{_iconsdir}/hicolor/*/*/kitty.{png,svg}
%{_metainfodir}/kitty.appdata.xml
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/*.py
%{_libdir}/%{name}/__pycache__
%{_libdir}/%{name}/kittens
%{_libdir}/%{name}/kitty
%{_libdir}/%{name}/logo
%{_libdir}/%{name}/shell-integration
%{_libdir}/%{name}/terminfo
%if %{with doc}
%{_mandir}/man1/kitty.1*
%{_mandir}/man5/kitty.conf.5*
%endif

%files bash-integration
%defattr(644,root,root,755)
/etc/profile.d/kitty.sh

%files fish-integration
%defattr(644,root,root,755)
%{fish_compdir}/kitty.fish

%files terminfo
%defattr(644,root,root,755)
%doc LICENSE
%{_datadir}/terminfo/x/xterm-kitty

%if %{with doc}
%files doc
%defattr(644,root,root,755)
%doc LICENSE
%doc CONTRIBUTING.md CHANGELOG.rst INSTALL.md
%{_docdir}/%{name}/html
%dir %{_docdir}/%{name}
%endif
