# build ids are not currently generated:
# https://code.google.com/p/go/issues/detail?id=5238
#
# also, debuginfo extraction currently fails with
# "Failed to write file: invalid section alignment"
%global debug_package %{nil}

# we are shipping the full contents of src in the data subpackage, which
# contains binary-like things (ELF data for tests, etc)
%global _binaries_in_noarch_packages_terminate_build 0

# Do not check any files in doc or src for requires
%global __requires_exclude_from ^(%{_datadir}|/usr/lib)/%{name}/(doc|src)/.*$

# Don't alter timestamps of especially the .a files (or else go will rebuild later)
# Actually, don't strip at all since we are not even building debug packages and this corrupts the dwarf testdata
%global __strip /bin/true

# rpmbuild magic to keep from having meta dependency on libc.so.6
%define _use_internal_dependency_generator 0
%define __find_requires %{nil}
%global __spec_install_post /usr/lib/rpm/check-rpaths   /usr/lib/rpm/check-buildroot  \
  /usr/lib/rpm/brp-compress

# let this match the macros in macros.golang
%global goroot          /usr/lib/%{name}
%global gopath          %{_datadir}/gocode
%global goarch 		%{_arch}
%global go_arches       %{ix86} x86_64 %{arm}
%ifarch x86_64
%global gohostarch  amd64
%endif
%ifarch %{ix86}
%global gohostarch  386
%endif
%ifarch %{arm}
%global gohostarch  arm
%endif

%global go_api 1.4

Name:           golang
Version:        1.4.2
Release:        1%{?dist}
Summary:        The Go Programming Language

License:        BSD
URL:            http://golang.org/
Source:         %{name}-%{version}.tar.gz
BuildRequires:  hostname

Provides:       go = %{version}-%{release}
Requires:       golang-bin
Requires:       golang-src = %{version}-%{release}

# Having documentation separate was broken
Obsoletes:      %{name}-docs < 1.1-4

# RPM can't handle symlink -> dir with subpackages, so merge back
Obsoletes:      %{name}-data < 1.1.1-4

# These are the only RHEL/Fedora architectures that we compile this package for
ExclusiveArch:  %{go_arches}

Source100:      golang-gdbinit
Source101:      golang-prelink.conf
Source102:      macros.golang
Patch001:         os_linux_h.patch

%description
%{summary}.


# Restore this package if RPM gets fixed (bug #975909)
%package       data
Summary:       Required architecture-independent files for Go
Requires:      %{name} = %{version}-%{release}
BuildArch:     noarch
Obsoletes:     %{name}-docs < 1.1-4

%description   data
%{summary}.


##
# the source tree
%package        src
Summary:        Golang compiler source tree
BuildArch:      noarch
%description    src
%{summary}

##
# This is the only architecture specific binary
%ifarch %{ix86}
%package        pkg-bin-linux-386
Summary:        Golang compiler tool for linux 386
Requires:       go = %{version}-%{release}
Requires:       golang-pkg-linux-386 = %{version}-%{release}
Requires(post): golang-pkg-linux-386 = %{version}-%{release}
Provides:       golang-bin = 386
Provides:       go(API)(go) = %{go_api}
# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       gcc
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
%description    pkg-bin-linux-386
%{summary}
%endif

%ifarch x86_64
%package        pkg-bin-linux-amd64
Summary:        Golang compiler tool for linux amd64
Requires:       go = %{version}-%{release}
Requires:       golang-pkg-linux-amd64 = %{version}-%{release}
Requires(post): golang-pkg-linux-amd64 = %{version}-%{release}
Provides:       golang-bin = amd64
Provides:       go(API)(go) = %{go_api}
# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       gcc
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
%description    pkg-bin-linux-amd64
%{summary}
%endif

%ifarch %{arm}
%package        pkg-bin-linux-arm
Summary:        Golang compiler tool for linux arm
Requires:       go = %{version}-%{release}
Requires:       golang-pkg-linux-arm = %{version}-%{release}
Requires(post): golang-pkg-linux-arm = %{version}-%{release}
Provides:       golang-bin = arm
Provides:       go(API)(go) = %{go_api}
# We strip the meta dependency, but go does require glibc.
# This is an odd issue, still looking for a better fix.
Requires:       glibc
Requires:       gcc
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
%description    pkg-bin-linux-arm
%{summary}
%endif

##
# architecture independent go tooling, that allows for cross
# compiling on golang supported architectures
# http://golang.org/doc/install/source#environment
%package        pkg-linux-386
Summary:        Golang compiler toolchain to compile for linux 386
Requires:       go = %{version}-%{release}
Provides:       go(API)(cgo) = %{go_api}
BuildArch:      noarch
%description    pkg-linux-386
%{summary}

%package        pkg-linux-amd64
Summary:        Golang compiler toolchain to compile for linux amd64
Requires:       go = %{version}-%{release}
Provides:       go(API)(cgo) = %{go_api}
BuildArch:      noarch
%description    pkg-linux-amd64
%{summary}

%package        pkg-linux-arm
Summary:        Golang compiler toolchain to compile for linux arm
Requires:       go = %{version}-%{release}
Provides:       go(API)(cgo) = %{go_api}
BuildArch:      noarch
%description    pkg-linux-arm
%{summary}

## missing ./go/src/runtime/defs_openbsd_arm.h
## we'll skip this bundle for now
#%package        pkg-openbsd-arm
#Summary:        Golang compiler toolchain to compile for openbsd arm
#Requires:       go = %{version}-%{release}
#BuildArch:      noarch
#%description    pkg-openbsd-arm
#%{summary}

# Workaround old RPM bug of symlink-replaced-with-dir failure
%pretrans -p <lua>
for _,d in pairs({"api", "doc", "include", "lib", "src"}) do
  path = "%{goroot}/" .. d
  if posix.stat(path, "type") == "link" then
    os.remove(path)
    posix.mkdir(path)
  end
end


%prep
%setup -q
%ifarch %{arm}
patch -p0 < os_linux_h.patch
%endif

%build
# set up final install location
export GOROOT_FINAL=%{goroot}

# TODO use the system linker to get the system link flags and build-id
# when https://code.google.com/p/go/issues/detail?id=5221 is solved
#export GO_LDFLAGS="-linkmode external -extldflags $RPM_LD_FLAGS"

export GOHOSTOS=linux
export GOHOSTARCH=%{gohostarch}
export GOOS=linux
export GOARCH=%{goarch}

# build for all (see http://golang.org/doc/install/source#environment)
pushd src
	# use our gcc options for this build, but store gcc as default for compiler
	CC="gcc $RPM_OPT_FLAGS $RPM_LD_FLAGS" 
	CC_FOR_TARGET="gcc"
	./make.bash --no-clean
popd

%install
rm -rf $RPM_BUILD_ROOT

# create the top level directories
mkdir -p $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{goroot}

# install everything into libdir (until symlink problems are fixed)
# https://code.google.com/p/go/issues/detail?id=5830
cp -apv api bin doc favicon.ico include lib pkg robots.txt src misc VERSION \
   $RPM_BUILD_ROOT%{goroot}

# bz1099206
find $RPM_BUILD_ROOT%{goroot}/src -exec touch -r $RPM_BUILD_ROOT%{goroot}/VERSION "{}" \;
# and level out all the built archives
touch $RPM_BUILD_ROOT%{goroot}/pkg
find $RPM_BUILD_ROOT%{goroot}/pkg -exec touch -r $RPM_BUILD_ROOT%{goroot}/pkg "{}" \;
# generate the spec file ownership of this source tree and packages
cwd=$(pwd)
src_list=$cwd/go-src.list
rm -f $src_list
touch $src_list

pushd $RPM_BUILD_ROOT%{goroot}
	find src/ -type d -printf '%%%dir %{goroot}/%p\n' >> $src_list
	find src/ ! -type d -printf '%{goroot}/%p\n' >> $src_list
	file_list=${cwd}/pkg-linux-%{goarch}.list
	rm -f $file_list
	touch $file_list
	find pkg/linux_%{goarch}/ -type d -printf '%%%dir %{goroot}/%p\n' >> $file_list
	find pkg/linux_%{goarch}/ ! -type d -printf '%{goroot}/%p\n' >> $file_list
popd

# remove the unnecessary zoneinfo file (Go will always use the system one first)
rm -rfv $RPM_BUILD_ROOT%{goroot}/lib/time

# remove the doc Makefile
rm -rfv $RPM_BUILD_ROOT%{goroot}/doc/Makefile

# put binaries to bindir, linked to the arch we're building,
# leave the arch independent pieces in %{goroot}
mkdir -p $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}
mv $RPM_BUILD_ROOT%{goroot}/bin/go $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/go
mv $RPM_BUILD_ROOT%{goroot}/bin/gofmt $RPM_BUILD_ROOT%{goroot}/bin/linux_%{gohostarch}/gofmt

# ensure these exist and are owned
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/github.com/
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/bitbucket.org/
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/code.google.com/
mkdir -p $RPM_BUILD_ROOT%{gopath}/src/code.google.com/p/

# remove the go and gofmt for other platforms (not used in the compile)
pushd $RPM_BUILD_ROOT%{goroot}/bin/
	rm -rf darwin_* windows_* freebsd_* netbsd_* openbsd_* plan9_*
	case "%{gohostarch}" in
		amd64)
			rm -rf linux_386 linux_arm ;;
		386)
			rm -rf linux_arm linux_amd64 ;;
		arm)
			rm -rf linux_386 linux_amd64 ;;
	esac
popd

# make sure these files exist and point to alternatives
rm -f $RPM_BUILD_ROOT%{_bindir}/go
ln -sf /etc/alternatives/go $RPM_BUILD_ROOT%{_bindir}/go
rm -f $RPM_BUILD_ROOT%{_bindir}/gofmt
ln -sf /etc/alternatives/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

# gdbinit
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d
cp -av %{SOURCE100} $RPM_BUILD_ROOT%{_sysconfdir}/gdbinit.d/golang.gdb

# prelink blacklist
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d
cp -av %{SOURCE101} $RPM_BUILD_ROOT%{_sysconfdir}/prelink.conf.d/golang.conf

# rpm macros
mkdir -p %{buildroot}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/rpm
cp -av %{SOURCE102} $RPM_BUILD_ROOT%{_sysconfdir}/rpm/macros.golang


%ifarch %{ix86}
%post pkg-bin-linux-386
# since the cgo.a packaged in this rpm will be older than the other archives likely built on the ARM builder,
touch -r %{goroot}/pkg/linux_386/runtime.a %{goroot}/pkg/linux_386/runtime/cgo.a

%{_sbindir}/update-alternatives --install %{_bindir}/go \
	go %{goroot}/bin/linux_386/go 90 \
	--slave %{_bindir}/gofmt gofmt %{goroot}/bin/linux_386/gofmt

%preun pkg-bin-linux-386
if [ $1 = 0 ]; then
	%{_sbindir}/update-alternatives --remove go %{goroot}/bin/linux_386/go
fi
%endif

%ifarch x86_64
%post pkg-bin-linux-amd64
# since the cgo.a packaged in this rpm will be older than the other archives likely built on the ARM builder,
touch -r %{goroot}/pkg/linux_amd64/runtime.a %{goroot}/pkg/linux_amd64/runtime/cgo.a

%{_sbindir}/update-alternatives --install %{_bindir}/go \
	go %{goroot}/bin/linux_amd64/go 90 \
	--slave %{_bindir}/gofmt gofmt %{goroot}/bin/linux_amd64/gofmt

%preun pkg-bin-linux-amd64
if [ $1 = 0 ]; then
	%{_sbindir}/update-alternatives --remove go %{goroot}/bin/linux_amd64/go
fi
%endif

%ifarch %{arm}
%post pkg-bin-linux-arm
# since the cgo.a packaged in this rpm will be older than the other archives likely built on the ARM builder,
touch -r %{goroot}/pkg/linux_arm/runtime.a %{goroot}/pkg/linux_arm/runtime/cgo.a

%{_sbindir}/update-alternatives --install %{_bindir}/go \
	go %{goroot}/bin/linux_arm/go 90 \
	--slave %{_bindir}/gofmt gofmt %{goroot}/bin/linux_arm/gofmt

%preun pkg-bin-linux-arm
if [ $1 = 0 ]; then
	%{_sbindir}/update-alternatives --remove go %{goroot}/bin/linux_arm/go
fi
%endif


%files
%doc AUTHORS CONTRIBUTORS LICENSE PATENTS
# VERSION has to be present in the GOROOT, for `go install std` to work
%doc %{goroot}/VERSION
%doc %{goroot}/doc/*

# go files
%dir %{goroot}
%{goroot}/*
%exclude %{goroot}/VERSION
%exclude %{goroot}/bin/
%exclude %{goroot}/pkg/
%exclude %{goroot}/src/

# ensure directory ownership, so they are cleaned up if empty
%dir %{gopath}
%dir %{gopath}/src
%dir %{gopath}/src/github.com/
%dir %{gopath}/src/bitbucket.org/
%dir %{gopath}/src/code.google.com/
%dir %{gopath}/src/code.google.com/p/


# gdbinit (for gdb debugging)
%{_sysconfdir}/gdbinit.d

# prelink blacklist
%{_sysconfdir}/prelink.conf.d
%{_sysconfdir}/rpm/macros.golang


%files -f go-src.list src

%ifarch %{ix86}
%files pkg-bin-linux-386
%{goroot}/bin/linux_386/
# binary executables
%{_bindir}/go
%{_bindir}/gofmt
%dir %{goroot}/pkg/obj/linux_386
%{goroot}/pkg/obj/linux_386/*
%{goroot}/pkg/linux_386/runtime/cgo.a
%dir %{goroot}/pkg/tool/linux_386
%{goroot}/pkg/tool/linux_386/5a
%{goroot}/pkg/tool/linux_386/5c
%{goroot}/pkg/tool/linux_386/5g
%{goroot}/pkg/tool/linux_386/5l
%{goroot}/pkg/tool/linux_386/6a
%{goroot}/pkg/tool/linux_386/6c
%{goroot}/pkg/tool/linux_386/6g
%{goroot}/pkg/tool/linux_386/6l
%{goroot}/pkg/tool/linux_386/8a
%{goroot}/pkg/tool/linux_386/8c
%{goroot}/pkg/tool/linux_386/8g
%{goroot}/pkg/tool/linux_386/8l
%{goroot}/pkg/tool/linux_386/addr2line
%{goroot}/pkg/tool/linux_386/dist
%{goroot}/pkg/tool/linux_386/nm
%{goroot}/pkg/tool/linux_386/objdump
%{goroot}/pkg/tool/linux_386/pack
%{goroot}/pkg/tool/linux_386/pprof
%endif

%ifarch x86_64
%files pkg-bin-linux-amd64
%{goroot}/bin/linux_amd64/
# binary executables
%{_bindir}/go
%{_bindir}/gofmt
%dir %{goroot}/pkg/obj/linux_amd64
%{goroot}/pkg/obj/linux_amd64/*
%{goroot}/pkg/linux_amd64/runtime/cgo.a
%dir %{goroot}/pkg/tool/linux_amd64
%{goroot}/pkg/tool/linux_amd64/5a
%{goroot}/pkg/tool/linux_amd64/5c
%{goroot}/pkg/tool/linux_amd64/5g
%{goroot}/pkg/tool/linux_amd64/5l
%{goroot}/pkg/tool/linux_amd64/6a
%{goroot}/pkg/tool/linux_amd64/6c
%{goroot}/pkg/tool/linux_amd64/6g
%{goroot}/pkg/tool/linux_amd64/6l
%{goroot}/pkg/tool/linux_amd64/8a
%{goroot}/pkg/tool/linux_amd64/8c
%{goroot}/pkg/tool/linux_amd64/8g
%{goroot}/pkg/tool/linux_amd64/8l
%{goroot}/pkg/tool/linux_amd64/addr2line
%{goroot}/pkg/tool/linux_amd64/dist
%{goroot}/pkg/tool/linux_amd64/nm
%{goroot}/pkg/tool/linux_amd64/objdump
%{goroot}/pkg/tool/linux_amd64/pack
%{goroot}/pkg/tool/linux_amd64/pprof
%endif

%ifarch %{arm}
%files pkg-bin-linux-arm
%{goroot}/bin/linux_arm/
# binary executables
%{_bindir}/go
%{_bindir}/gofmt
%dir %{goroot}/pkg/obj/linux_arm
%{goroot}/pkg/obj/linux_arm/*
%{goroot}/pkg/linux_arm/runtime/cgo.a
%dir %{goroot}/pkg/tool/linux_arm
%{goroot}/pkg/tool/linux_arm/5a
%{goroot}/pkg/tool/linux_arm/5c
%{goroot}/pkg/tool/linux_arm/5g
%{goroot}/pkg/tool/linux_arm/5l
#%{goroot}/pkg/tool/linux_arm/6a
#%{goroot}/pkg/tool/linux_arm/6c
#%{goroot}/pkg/tool/linux_arm/6g
#%{goroot}/pkg/tool/linux_arm/6l
#%{goroot}/pkg/tool/linux_arm/8a
#%{goroot}/pkg/tool/linux_arm/8c
#%{goroot}/pkg/tool/linux_arm/8g
#%{goroot}/pkg/tool/linux_arm/8l
%{goroot}/pkg/tool/linux_arm/addr2line
%{goroot}/pkg/tool/linux_arm/dist
%{goroot}/pkg/tool/linux_arm/nm
%{goroot}/pkg/tool/linux_arm/objdump
%{goroot}/pkg/tool/linux_arm/pack
%{goroot}/pkg/tool/linux_arm/pprof
%endif

%ifarch %{ix86}
%files pkg-linux-386 -f pkg-linux-386.list
%{goroot}/pkg/linux_386/
%exclude %{goroot}/pkg/linux_386/runtime/cgo.a
%{goroot}/pkg/tool/linux_386/cgo
%{goroot}/pkg/tool/linux_386/fix
%{goroot}/pkg/tool/linux_386/yacc
%endif

%ifarch x86_64
%files pkg-linux-amd64 -f pkg-linux-amd64.list
%{goroot}/pkg/linux_amd64/
%exclude %{goroot}/pkg/linux_amd64/runtime/cgo.a
%{goroot}/pkg/tool/linux_amd64/cgo
%{goroot}/pkg/tool/linux_amd64/fix
%{goroot}/pkg/tool/linux_amd64/yacc
%endif

%ifarch %{arm}
%files pkg-linux-arm -f pkg-linux-arm.list
%{goroot}/pkg/linux_arm/
%exclude %{goroot}/pkg/linux_arm/runtime/cgo.a
%{goroot}/pkg/tool/linux_arm/cgo
%{goroot}/pkg/tool/linux_arm/fix
%{goroot}/pkg/tool/linux_arm/yacc
%endif


