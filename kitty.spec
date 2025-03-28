#
# Conditional build:
%bcond_with	tests		# build without tests
%bcond_with	build_docs	# build docs instead of pre-packaged files
%bcond_with	vendor		# create vendor tarba

# NOTE:
# - docs build requires git checkout and (yet) missing sphinxext-opengraph package

Summary:	Cross-platform, fast, feature full, GPU based terminal emulator
Name:		kitty
Version:	0.28.0
Release:	3
# BSD:          docs/_templates/searchbox.html
# zlib:         glfw/
License:	GPLv3 and zlib and BSD
Source0:	https://github.com/kovidgoyal/kitty/releases/download/v%{version}/%{name}-%{version}.tar.xz
# Source0-md5:	5b458f1e594f7b5668b0e728957c221d
# Add AppData manifest file
# * https://github.com/kovidgoyal/kitty/pull/2088
Source1:	%{name}.metainfo.xml
Source2:	%{name}.sh
Source3:	%{name}.fish
%if %{without vendor}
Source4:	%{name}-%{version}-vendor.tar.xz
# Source4-md5:	c509736ee0f2073aa504124e6efa1be0
%endif
Patch0:		num-workers.patch
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
%if %{with build_docs}
BuildRequires:	python3dist(sphinx)
BuildRequires:	python3dist(sphinx-copybutton)
BuildRequires:	python3dist(sphinx-inline-tabs)
#BuildRequires:	python3dist(sphinxext-opengraph)
BuildRequires:	sphinx-pdg
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
%autosetup -p1 %{?without_vendor:-a4}

%if %{with vendor}
go mod vendor
tar -caf %{_sourcedir}/%{name}-%{version}-vendor.tar.xz vendor
exit 1
%endif

# Changing sphinx theme to classic
sed "s/html_theme = 'furo'/html_theme = 'classic'/" -i docs/conf.py

# Missing in pld
%{__sed} -i -e '/sphinxext.opengraph/d' docs/conf.py

find -type f -name "*.py" | xargs sed -i \
	-e 's|%{_bindir}/env python3|%{__python3}|g' \
	-e 's|%{_bindir}/env python|%{__python3}|g' \
	-e 's|%{_bindir}/env -S kitty|%{_bindir}/kitty|g' \
	%{nil}

# non-executable-script
sed -e "s/f.endswith('\.so')/f.endswith('\.so') or f.endswith('\.py')/g" -i setup.py

# script-without-shebang '__init__.py'
find -type f -name "*.py*" | xargs chmod a-x

%build
%if %{with build_docs}
%{__python3} setup.py build
%{__make} -C docs man html
%endif

%install
rm -rf $RPM_BUILD_ROOT
%set_build_flags
export CC="%{__cc}"
export CXX="%{__cxx}"
export GOCACHE=%go_cachedir
export NUM_WORKERS=1
# unset PWD for https://github.com/kovidgoyal/kitty/issues/6051
unset PWD
# NOTE: setup.py is not regular setuptools setup.py
%{__python3} setup.py linux-package \
    --libdir-name=%{_lib} \
    --prefix=$RPM_BUILD_ROOT%{_prefix} \
    --update-check-interval=0 \
    --verbose \
    --debug \
    --shell-integration "disabled" \
    %{nil}

install -Dp %{SOURCE1} $RPM_BUILD_ROOT%{_metainfodir}/%{name}.metainfo.xml
install -Dp %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/%{name}.sh
install -Dp %{SOURCE3} $RPM_BUILD_ROOT%{fish_compdir}/%{name}.fish

sed 's|KITTY_INSTALLATION_DIR=.*|KITTY_INSTALLATION_DIR="%{_libdir}/%{name}"|' \
 -i $RPM_BUILD_ROOT%{_sysconfdir}/profile.d/%{name}.sh
sed 's|set -l KITTY_INSTALLATION_DIR .*|set -l KITTY_INSTALLATION_DIR "%{_libdir}/%{name}"|' \
 -i $RPM_BUILD_ROOT%{fish_compdir}/%{name}.fish

# script-without-shebang '__init__.py'
find $RPM_BUILD_ROOT -type f -name "*.py*" ! -name askpass.py | xargs chmod a-x

# rpmlint fixes
rm $RPM_BUILD_ROOT%{_docdir}/%{name}/html/.buildinfo \
	$RPM_BUILD_ROOT%{_docdir}/%{name}/html/.nojekyll

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
%{_metainfodir}/kitty.metainfo.xml
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/logo
%{_libdir}/%{name}/shell-integration
%{_libdir}/%{name}/terminfo
%{_mandir}/man1/kitty.1*
%{_mandir}/man5/kitty.conf.5*

# verbose files to specify attr for shared libs
%{_libdir}/%{name}/*.py
%{_libdir}/%{name}/__pycache__
%dir %{_libdir}/%{name}/kittens
%{_libdir}/%{name}/kittens/*.py
%{_libdir}/%{name}/kittens/__pycache__
%dir %{_libdir}/%{name}/kittens/choose
%{_libdir}/%{name}/kittens/choose/*.py
%{_libdir}/%{name}/kittens/choose/__pycache__
%dir %{_libdir}/%{name}/kittens/diff
%{_libdir}/%{name}/kittens/diff/*.py
%{_libdir}/%{name}/kittens/diff/__pycache__
%{_libdir}/%{name}/kittens/diff/options
%dir %{_libdir}/%{name}/kittens/transfer
%{_libdir}/%{name}/kittens/transfer/*.py
%{_libdir}/%{name}/kittens/transfer/__pycache__
%dir %{_libdir}/%{name}/kittens/unicode_input
%{_libdir}/%{name}/kittens/unicode_input/*.py
%{_libdir}/%{name}/kittens/unicode_input/__pycache__
%attr(755,root,root) %{_libdir}/%{name}/kittens/*/*.so
%{_libdir}/%{name}/kittens/ask
%{_libdir}/%{name}/kittens/broadcast
%{_libdir}/%{name}/kittens/clipboard
%{_libdir}/%{name}/kittens/hints
%{_libdir}/%{name}/kittens/hyperlinked_grep
%{_libdir}/%{name}/kittens/icat
%{_libdir}/%{name}/kittens/mouse_demo
%{_libdir}/%{name}/kittens/panel
%{_libdir}/%{name}/kittens/query_terminal
%{_libdir}/%{name}/kittens/remote_file
%{_libdir}/%{name}/kittens/resize_window
%{_libdir}/%{name}/kittens/show_error
%{_libdir}/%{name}/kittens/show_key
%{_libdir}/%{name}/kittens/ssh
%{_libdir}/%{name}/kittens/themes
%{_libdir}/%{name}/kittens/tui

%dir %{_libdir}/%{name}/kitty
%{_libdir}/%{name}/kitty/__pycache__
%{_libdir}/%{name}/kitty/*.py
%{_libdir}/%{name}/kitty/*.glsl
%{_libdir}/%{name}/kitty/conf
%{_libdir}/%{name}/kitty/fonts
%{_libdir}/%{name}/kitty/launcher
%{_libdir}/%{name}/kitty/layout
%{_libdir}/%{name}/kitty/options
%{_libdir}/%{name}/kitty/rc
%attr(755,root,root) %{_libdir}/%{name}/kitty/*.so

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

%files doc
%defattr(644,root,root,755)
%doc CONTRIBUTING.md CHANGELOG.rst INSTALL.md LICENSE
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/html
