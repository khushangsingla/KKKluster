start_uefi=1MiB
end_uefi=300MiB
start_root=$end_uefi
device_name=$1
bootstrap_mirror=http://deb.debian.org/debian/
swapsize=1 # in units of 512MB
# grub-install --target=i386-pc /dev/${device_name}
parted -s  `# non-interactive` \
	-a optimal `# align according to optimal performance` \
	-- /dev/$device_name `# block device to set the partitions` \
	mklabel gpt `# make a gpt partition table` \
	mkpart primary fat32 $start_uefi $end_uefi `# make a UEFI partition` \
	mkpart primary ext4 $start_root -0 `# make root partition` \
	name 1 uefi \
	name 2 root \
	set 1 esp on `# set esp flag on efi partition`
	# set 1 boot on # set boot flag on


sleep 2
# formatting the partitions

mkfs.fat -F 32 /dev/${device_name}p1
mkfs.ext4 -L root /dev/${device_name}p2

# swap_uuid="$(blkid --probe /dev/${device_name}p2 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
# root_uuid="$(blkid --probe /dev/${device_name}p3 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"
# boot_uuid="$(blkid --probe /dev/${device_name}p1 | grep -o ' UUID="[^"]\+"' | sed -e 's/^ //' )"

mount /dev/${device_name}p2 /mnt

mkdir /mnt/boot
mount /dev/${device_name}p1 /mnt/boot

echo start if
if [ -d /tmp/bootstrapping ]
then
	echo hi
else

	mkdir /tmp/bootstrapping
	debootstrap --arch=amd64 `# architecture of machine` \
		--include=systemd,dbus `# packages to install` \
		--components=main,restricted,universe `# components to use` \
		bookworm `# install stable` \
		/tmp/bootstrapping `#install target` \
		$bootstrap_mirror # mirror for bootstrapping
	arch-chroot /tmp/bootstrapping bash -c "apt update \
		&& apt install network-manager grub-efi-amd64 linux-image-amd64 sudo docker.io docker-compose neovim build-essential openssl openssh-server curl wget htop nfs-common -y \
		&& curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg \
		&& echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list \
		&& apt update \
		&& apt install -y kubelet kubeadm kubectl \
		&& apt-mark hold kubelet kubeadm kubectl \
		&& systemctl enable kubelet \
		&& curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null \
		&& apt-get install apt-transport-https --yes \
		&& echo 'deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main' | tee /etc/apt/sources.list.d/helm-stable-debian.list \
		&& apt-get update \
		&& apt-get install helm \
		&& helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/ \
		&& echo 'net.bridge.bridge-nf-call-iptables=1' | sudo tee -a /etc/sysctl.conf \
		&& wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.12/cri-dockerd_0.3.12.3-0.debian-bookworm_amd64.deb \
		&& dpkg -i cri-dockerd_0.3.12.3-0.debian-bookworm_amd64.deb \
		&& mkdir -p /opt/cni/bin \
		&& curl -O -L https://github.com/containernetworking/plugins/releases/download/v1.2.0/cni-plugins-linux-amd64-v1.2.0.tgz \
		&& tar -C /opt/cni/bin -xzf cni-plugins-linux-amd64-v1.2.0.tgz"
fi
echo end if

cp -rp /tmp/bootstrapping/* /mnt
# dd if=/dev/zero of=/mnt/swapfile bs=512M count=$swapsize
# chmod 0600 /mnt/swapfile
# mkswap /mnt/swapfile
genfstab -U /mnt > /mnt/etc/fstab
echo "127.0.0.1 $2" >> /mnt/etc/hosts
echo $2 > /mnt/etc/hostname

arch-chroot /mnt/ bash -c "apt update \
	&& apt install network-manager grub-efi-amd64 linux-image-amd64 sudo docker.io docker-compose neovim build-essential openssl openssh-server curl wget -y \
	&& grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB \
	&& update-grub \
	&& grub-mkconfig -o /boot/grub/grub.cfg \
	&& useradd --home /home/admin --shell /bin/bash -m admin \
	&& passwd admin"
echo 'admin  ALL=(ALL:ALL) ALL' >> /mnt/etc/sudoers

mkdir /mnt/home/admin/.ssh
cp /home/hrishi/.ssh/authorized_keys /mnt/home/admin/.ssh
# echo "/swapfile           	none      	swap      	defaults  	0 0" >> /mnt/etc/fstab
umount -R /mnt
