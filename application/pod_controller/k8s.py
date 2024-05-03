import time
import os

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

IP_ADDRESS = os.getenv('JOB_HANDLER_SERVICE_HOST',"0.0.0.0")
PORT = int(os.getenv('JOB_HANDLER_SERVICE_PORT',9876))
print(f"IP_ADDRESS: {IP_ADDRESS}")
print(f"PORT: {PORT}")

def create_pods(num_pods, image, hashval):
    config.load_kube_config()
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    api_instance = core_v1_api.CoreV1Api()

    for i in range(num_pods):
        name = f"{hashval[:10]}-{i}" 
        resp = None

        try:
            resp = api_instance.read_namespaced_pod(name=name,
                                                    namespace='kkkluster')
        except ApiException as e:
            if e.status != 404:
                print(f"Unknown error: {e}")
                exit(1)

        if not resp:
            print(f"Pod {name} does not exist. Creating it...")
            pod_manifest = {
                    'apiVersion': 'v1',
                    'kind': 'Pod',
                    'metadata': {
                        'name': name
                        },
                    'spec': {
                        'containers': [{
                            'image': image,
                            'imagePullPolicy': 'Always',
                            'name': f"{hashval[:10]}-{i}-container",
                            'env': [{'name':'POD_IDENTIFIER', 'value': str(hashval)},
                                    {'name':'JOB_HANDLER_SERVICE_IP', 'value': IP_ADDRESS},
                                    {'name':'JOB_HANDLER_SERVICE_PORT', 'value': str(PORT)},
                                    {'name':'NUM_THREADS', 'value': "2"}],
                            "args": [ "python3", "/common_mount/interact.py" ],
                            "volumeMounts": [
                                {
                                    "mountPath": "/common_mount",
                                    "name": "common-mount"
                                    },
                                {
                                    "mountPath": "/nfs_mount",
                                    "name": "nfs-mount"
                                    }]
                                }],
                        'volumes': [
                            {
                                "name": "common-mount",
                                "nfs": {
                                    "server": "10.130.5.151",
                                    "path": "/k8s_test/common"
                                    }
                                },
                            {
                                "name": "nfs-mount",
                                "nfs": {
                                    "server": "10.130.5.151",
                                    "path": "/k8s_test/nfs"
                                    }
                                }]
                            }
                    }
            print(pod_manifest)
            resp = api_instance.create_namespaced_pod(body=pod_manifest,
                                                      namespace='kkkluster')
            print("Pod created. status='%s'" % str(resp.status))
            # while True:
            #     resp = api_instance.read_namespaced_pod(name=name,
            #                                             namespace='default')
            #     if resp.status.phase != 'Pending':
            #         break
            #     time.sleep(1)
            # print("Done.")

def kill_pod_with_name(name):
    config.load_kube_config()
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    api_instance = core_v1_api.CoreV1Api()
    try:
        resp = api_instance.delete_namespaced_pod(name=name,
                                                  namespace='kkkluster',
                                                  body={})
        print("Pod deleted. status='%s'" % str(resp.status))
    except ApiException as e:
        print(f"Error: {e}")

# def main():
#     config.load_kube_config()
#     try:
#         c = Configuration().get_default_copy()
#     except AttributeError:
#         c = Configuration()
#         c.assert_hostname = False
#     Configuration.set_default(c)
#     core_v1 = core_v1_api.CoreV1Api()
# 
#     exec_commands(core_v1)
# 
# 
# if __name__ == '__main__':
#     main()

