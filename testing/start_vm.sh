qemu-system-x86_64 -enable-kvm -m 4096 -smp cpus=4 -bios /usr/share/ovmf/OVMF.fd -device virtio-net-pci,netdev=user0,mac=52:54:00:37:84:18 -netdev bridge,id=user0,br=br0 -hda test1.img
