# Testing - KKKluster

This folder contains files for setting up test environment. If you already have a K8s cluster ready, you can skip this step. First of all, insert
`nbd` module using the following command

```bash
sudo modprobe nbd
```

Then, run the `create_machines.sh` script as root. Make sure that you have the required tools
to run the script. Some of the tools you may need to install are mentioned in the file 
`os_setup/required_tools`.

This would create `.img` files for 1 control plane and 2 worker nodes. The script will also add
a user `admin` with password `admin` in all the machines. You can then use these images to run
the machines and start the cluster. The setup instructions and debugging of common errors is there
in `k8s_setup` folder in root of the project.

### Running the job manager application

To run the job manager application, you just need to use the `application/deploy_app.yaml` file.
You may want to do the following changes to make sure it works smoothly on your machine.

- Change the IP address on line 17 of `application/deploy_app.yaml` to the IP address of the control plane of your cluster
- Change the `nfs` field everywhere to your own NFS directory and IP address of the NFS server
- For `cluster-controller` service, either copy your /root/.kube/config file to the pod or create your own image with the config file in it
