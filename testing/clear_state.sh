qemu-nbd -d /dev/nbd0
qemu-nbd -d /dev/nbd1
qemu-nbd -d /dev/nbd2

rm -r /tmp/bootstrapping
umount -R /mnt
umount -R /mnt
umount -R /mnt

rm -r /mnt/*

rm *.img
rm *.vmdk
