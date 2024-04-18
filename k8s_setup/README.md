# K8S setup

## Control Plane

- Run `kubeadm init` to initialize the control plane

#### Common Issues

- crictl can be used to debug any problems with the container runtime
- Use cgroup\_v2\_selection to use cgroupv2 with containerd
