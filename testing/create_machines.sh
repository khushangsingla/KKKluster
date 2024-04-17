qemu-img create -f qcow2 control_plane.img 40G
qemu-img create -f qcow2 worker0.img 40G
qemu-img create -f qcow2 worker1.img 40G

qemu-nbd --connect=/dev/nbd0 control_plane.img
qemu-nbd --connect=/dev/nbd1 worker0.img
qemu-nbd --connect=/dev/nbd2 worker1.img

../os_setup/script.sh nbd0
../os_setup/script.sh nbd1
../os_setup/script.sh nbd2

qemu-nbd -d /dev/nbd0
qemu-nbd -d /dev/nbd1
qemu-nbd -d /dev/nbd2
