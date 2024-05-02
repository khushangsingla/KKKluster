import os
import socket
import multiprocessing.pool as Pool
# jobid = sys.argv[1]

identifier = os.environ.get("POD_IDENTIFIER")
service_ip = os.environ.get("JOB_HANDLER_SERVICE_IP")
service_port = int(os.environ.get("JOB_HANDLER_SERVICE_PORT"))
num_threads = int(os.environ.get("NUM_THREADS", 10))

commands = None

def getNewCmd():
    # get cmd from service
    try:
        msg = identifier.encode("utf-8") + b"\x00"

        # send msg to service
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((service_ip, service_port))
        s.sendall(msg)

        resp = b""
        while True:
            data = s.recv(8 - len(resp))
            resp += data
            if len(resp) == 8:
                break

        # get response from service in resp
        thid = int.from_bytes(resp[:4], "little")
        cmdlen = int.from_bytes(resp[4:], "little")
        cmd = b""

        while len(cmd) < cmdlen:
            data = s.recv(cmdlen - len(cmd))
            cmd += data

        s.close()

        if len(cmd) == 0:
           return None 
        else:
            return thid, cmd.decode("utf-8")

    except Exception as e:
        print("Error: ", e)
        return getNewCmd()


def informService(thid, retcode):
    try:
        msg = identifier.encode("utf-8") + b"\x01"
        msg += thid.to_bytes(4, "little") + retcode.to_bytes(4, "little")

        # send msg to service
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((service_ip, service_port))
        s.sendall(msg)
        s.close()

    except Exception as e:
        print("Error: ", e)
        informService(thid, retcode)

def runCmd():
    thid, cmd = getNewCmd()

    if cmd is None:
        return

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    retcode = result.returncode

    # inform service about thread completion
    informService(thid, retcode)
    runCmd()
    

if __name__ == "__main__":
    # put in MP pool
    pool = Pool.Pool(num_threads)
    pool.map(runCmd, range(num_threads))
    pool.close()
