qemu-img create -f qcow2 control_plane.img 40G
qemu-img create -f qcow2 worker0.img 40G
qemu-img create -f qcow2 worker1.img 40G

qemu-nbd --connect=/dev/nbd0 control_plane.img
qemu-nbd --connect=/dev/nbd1 worker0.img
qemu-nbd --connect=/dev/nbd2 worker1.img

../os_setup/script.sh nbd0 controlplane
../os_setup/script.sh nbd1 worker0
../os_setup/script.sh nbd2 worker1

sudo VBoxManage internalcommands createrawvmdk -filename control_plane.vmdk -rawdisk /dev/nbd0
sudo VBoxManage internalcommands createrawvmdk -filename worker0.vmdk -rawdisk /dev/nbd1
sudo VBoxManage internalcommands createrawvmdk -filename worker1.vmdk -rawdisk /dev/nbd2

# Use the following in EFI shell
# FS0:
# bcfg boot add 0 fs0:\EFI\GRUB\grubx64.efi "UEFI OS"
