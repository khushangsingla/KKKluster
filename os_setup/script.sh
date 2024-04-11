start_uefi=1MiB
end_uefi=300MiB
start_swap=$end_uefi
end_swap=1GiB
start_root=$end_swap
device_name=nbd5
bootstrap_mirror=http://deb.debian.org/debian/
# grub-install --target=i386-pc /dev/${device_name}
parted -s  `# non-interactive` \
	-a optimal `# align according to optimal performance` \
	-- /dev/$device_name `# block device to set the partitions` \
	mklabel gpt `# make a gpt partition table` \
	mkpart primary fat32 $start_uefi $end_uefi `# make a UEFI partition` \
	mkpart primary linux-swap $start_swap $end_swap `# make a swap partition` \
	mkpart primary ext4 $start_root -0 `# make root partition` \
	name 1 uefi \
	name 2 swap \
	name 3 root \
	set 1 esp on `# set esp flag on efi partition` \
	set 2 swap on `# set swap flag on`
	# set 1 boot on # set boot flag on


# formatting the partitions

mkfs.fat -F 32 /dev/${device_name}p1
mkswap -L swap /dev/${device_name}p2
mkfs.ext4 -L root /dev/${device_name}p3

# swap_uuid="$(blkid --probe /dev/${device_name}p2 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
# root_uuid="$(blkid --probe /dev/${device_name}p3 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
# boot_uuid="$(blkid --probe /dev/${device_name}p1 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"

mount /dev/${device_name}p3 /mnt

mkdir /mnt/boot
mount /dev/${device_name}p1 /mnt/boot

swapon /dev/${device_name}p2

debootstrap --arch=amd64 `# architecture of machine` \
	--include=docker.io,docker-compose,openssh-server,grub-efi-amd64,linux-image-amd64,network-manager,dbus,dbus-bin,dbus-daemon,dbus-session-bus-common,dbus-system-bus-common,dbus-user-session,libpam-systemd,systemd `# packages to install` \
	--components=main,restricted,universe `# components to use` \
	bookworm `# install stable` \
	/mnt `#install target` \
	$bootstrap_mirror # mirror for bootstrapping

genfstab -U /mnt >> /mnt/etc/fstab
# mount --bind /dev /mnt/dev
# mount --bind /proc /mnt/proc
# mount --bind /sys /mnt/sys

arch-chroot /mnt/ bash -c "apt update && apt upgrade -y && apt install grub-efi-amd64 linux-image-amd64 sudo && grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB && update-grub && grub-mkconfig -o /boot/grub/grub.cfg && useradd --home /home/admin --shell /bin/bash -m admin && echo the_password | passwd admin --stdin && echo 'admin  ALL=(ALL:ALL) ALL' >> /etc/sudoers"
umount -R /mnt
