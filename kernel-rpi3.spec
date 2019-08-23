%define config_name bcmrpi3_defconfig
%define buildarch arm64
%define target_board rpi3

Name: kernel-rpi3
Summary: The Linux Kernel for Raspberry Pi3
Version: 4.19.66
Release: 1
License: GPL-2.0
Vendor: The Linux Community
URL: https://www.kernel.org
ExclusiveArch: aarch64
Source0: conform_config-rpi-4.19.y.sh

BuildRequires: bc
BuildRequires: git
BuildRequires: curl
BuildRequires: u-boot-tools >= 2016.03
BuildRequires: bison
BuildRequires: flex
BuildRequires: openssl-devel

%description
The Linux Kernel, the operating system core itself

%package modules
Summary: Kernel modules for %{target_board}
Group: System/Kernel
Provides: %{name}-modules = %{EVRD}

%description modules
Kernel-modules includes the loadable kernel modules(.ko files) for %{target_board}

%package devel
License: GPL-2.0
Summary: Linux support kernel map and etc for other packages
Group: System/Kernel

%description devel
This package provides kernel map and etc information.

%prep
git clone --depth 1 https://github.com/raspberrypi/linux.git

%build
pushd linux
# 1-1. Set config file
%make_build bcmrpi3_defconfig
#sh %{SOURCE0} .config
sed -i 's!-v8!!g' .config
# 1-2. Build Image/Image.gz
%make_build CC=gcc CXX=g++ CFLAGS="%{optflags}"
# 1-3. Build dtbs & modules
%make_build dtbs modules CC=gcc CXX=g++ CFLAGS="%{optflags}"
popd

%install
# 2-1. Destination directories
mkdir -p %{buildroot}/boot/broadcom
mkdir -p %{buildroot}/boot/overlays
mkdir -p %{buildroot}/lib/modules

pushd linux
# 2-2. Install kernel binary and DTB
install -m 644 arch/%{buildarch}/boot/Image %{buildroot}/boot/%{name}-%{version}-%{release}.img
install -m 644 arch/%{buildarch}/boot/dts/broadcom/bcm*.dtb %{buildroot}/boot/
install -m644  arch/arm/boot/dts/overlays/*.dtb* %{buildroot}/boot/overlays

# 2-3. Install modules
make INSTALL_MOD_STRIP=1 INSTALL_MOD_PATH=%{buildroot} modules_install
# 4. Move files for each package
%{make_build} INSTALL_HDR_PATH=%{buildroot}%{_prefix} KERNELRELEASE=%{version} headers_install 

make mrproper
popd

cat <<EOF > %{buildroot}/boot/cmdline.txt
dwc_otg.lpm_enable=0 console=ttyS0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait
EOF

cat <<EOF > %{buildroot}/boot/config.txt
# See
# https://www.raspberrypi.org/documentation/configuration/config-txt
arm_64bit=1
kernel=%{name}-%{version}-%{release}.img
dtoverlay=vc4-kms-v3d-overlay
# enable serial
enable_uart=1
# Force the monitor to HDMI mode so that sound will be sent over HDMI cable
hdmi_drive=2
# Set monitor mode to DMT
hdmi_group=2
# Set monitor resolution to 1024x768 XGA 60Hz (HDMI_DMT_XGA_60)
hdmi_mode=16
# Make display smaller to stop text spilling off the screen
overscan_left=20
overscan_right=12
overscan_top=10
overscan_bottom=10
# For i2c & spi
dtparam=i2c_arm=on
dtparam=spi=on
# Enable audio (loads snd_bcm2835)
dtparam=audio=on
EOF

curl -L https://github.com/raspberrypi/firmware/raw/master/boot/bootcode.bin --output %{buildroot}/boot/bootcode.bin
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/fixup.dat --output %{buildroot}/boot/fixup.dat 
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/fixup_cd.dat --output %{buildroot}/boot/fixup_cd.dat
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/fixup_db.dat --output %{buildroot}/boot/fixup_db.dat
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/fixup_x.dat --output %{buildroot}/boot/fixup_x.dat
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/start.elf --output %{buildroot}/boot/start.elf
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/start_cd.elf --output %{buildroot}/boot/start_cd.elf
curl -L https://github.com/raspberrypi/firmware/raw/master/boot/start_db.elf --output %{buildroot}/boot/start_db.elf

%post
/sbin/dracut --gzip -o ifcfg -o lvm -o mdraid i\
	-o aufs-mount -o network -o dm -o crypt \
	-o dmraid -o multipath -o multipath-hostonly \
	--fstab --add-fstab /etc/fstab -f /boot/initrd-%{version}-%{release}.img %{version}-%{release}

chmod 0644 %{buildroot}/boot/initrd-%{version}-%{release}.img

/sbin/depmod -a

%postun
rm -fv /boot/initrd-%{version}-%{release}.img

%files
/boot/%{name}-%{version}-%{release}.img
/boot/bcm*.dtb
/boot/config.txt
/boot/cmdline.txt
/boot/bootcode.bin
/boot/start*.elf
/boot/fixup*.dat
/boot/overlays/*.dtb*

%files modules
/lib/modules/*

%files devel
%{_includedir}
