# K8S setup

## Control Plane

- Run `kubeadm init` to initialize the control plane

#### Common Issues

- crictl can be used to debug any problems with the container runtime
- Use cgroup\_v2\_selection to use cgroupv2 with containerd
- Use `--pod-network-cidr="10.244.0.0./16"` to set the pod network CIDR to work with flannel
- Use following command to set flannel:

```
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```
- `mkdir /run/flannel` on boot time
