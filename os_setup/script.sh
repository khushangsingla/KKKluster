start_uefi=1MiB
end_uefi=300MiB
start_swap=$end_uefi
end_swap=1GiB
start_root=$end_swap
device_name=sda
bootstrap_mirror=http://deb.debian.org/debian/
parted -s \ # non-interactive
	-a optimal \ # align according to optimal performance
	-- /dev/$device_name \ # block device to set the partitions
	mklabel gpt \ # make a gpt partition table
	mkpart primary uefi fat32 $start_uefi $end_uefi \ # make a UEFI partition
	mkpart primary swap linux-swap $start_swap $end_swap \ # make a swap partition
	mkpart primary root ext4 $start_root -0 \ # make root partition
	set 1 esp on \ # set esp flag on efi partition
	set 2 swap on \ # set swap flag on
	set 3 root on \ # set root flag on
	set 1 boot on # set boot flag on


# formatting the partitions

mkfs -t fat -F 32 -n EFI /dev/${device_name}p1
mkswap -L swap /dev/${device_name}p2
mkfs -t ext4 -L root /dev/${device_name}p3

swap_uuid="$(blkid | grep '^/dev/${device_name}p2' | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
root_uuid="$(blkid | grep '^/dev/${device_name}p3' | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
boot_uuid="$(blkid | grep '^/dev/${device_name}p1' | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"

mount /dev/${device_name}p3 /mnt
mount /dev/${device_name}p1 /mnt/boot

debootstrap --arch=amd64 \ # architecture of machine
	--include=docker.io,docker-compose,openssh-server,network-manager \ # packages to install
	--components= \ # components to use
	bookworm \ # install stable
	/mnt \ #install target
	$bootstrap_mirror # mirror for bootstrapping
