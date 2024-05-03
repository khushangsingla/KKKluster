import db
import k8s
import os
import socket
import time
import selectors
import string
import random

# Listening socket on port <ENV : JOB_HANDLER_SERVICE_PORT>
"""
Message format: <64 bytes identifier><1 byte request><other info>

Request:
    0: Get job - get cmd and thread id
    1: Job done - other info - <4 bytes thid><4 bytes exit code>
"""

IP_ADDRESS = os.getenv('JOB_HANDLER_SERVICE_HOST')
PORT = int(os.getenv('JOB_HANDLER_SERVICE_PORT'))
identifier_len = 64


# setup a listening socket
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind(("0.0.0.0", PORT))
lsock.listen()

sel = selectors.DefaultSelector()
sel.register(lsock, selectors.EVENT_READ, data=None)

SEND_THREAD_CMD = 0
WORKER_POD = 1
FRONTEND_SERVER = 2
MALICIOUS = 3

frontend_server_id = os.getenv('FRONTEND_SERVER_ID')

id_to_job = {}

def new_job_came_up(jid):
    """
    A new job has been registered in the db
    """
    print("[DEBUG] New job came up: ", jid)
    num_pods = db.db_get_num_pods(jid)
    image = db.db_get_image(jid)
    hashval = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(64))
    k8s.create_pods(num_pods, image, hashval)
    id_to_job[hashval] = [jid, []]

    cmds = db.db_get_commands_of_job(jid)
    id_to_job[hashval][1] = cmds
    

def kill_pod(identifier):
    """
    Kills the pod with the given identifier
    """
    pass

def get_next_cmd(identifier):
    """
    returns a tuple thid, cmd
    """
    cmd = id_to_job[identifier][1].pop(0)
    return cmd

def update_thread_retcode(thid, exit_code, identifier):
    """
    Updates the exit code of the thread in the db
    returns false if unauthorized access
    """
    jobid = id_to_job[identifier][0]
    db.db_update_thread_retcode(thid, exit_code, jobid)
    return

def get_entity_type(identifier):
    """
    returns the entity type of the identifier - WORKER_POD or FRONTEND_SERVER
    """
    try:
        print("[DEBUG] Identifier: ", identifier)
        print("[DEBUG] Frontend server id: ", frontend_server_id, type(frontend_server_id))
        if type(identifier) == bytes:
            identifier = identifier.decode('utf-8')
        if identifier == frontend_server_id:
            return FRONTEND_SERVER
        return WORKER_POD
    except:
        return MALICIOUS

def accept(sel, sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ , data={'data': b''})
    print("[DEBUG] Accepted connection from: ", addr)

def service(sel,key, mask):
    sock = key.fileobj
    data = key.data['data']
    key_data = key.data
    sel.unregister(sock)
    print("[DEBUG] Service: ", key.data)

    if mask & selectors.EVENT_READ:
        print("[DEBUG] Reading data")
        if 'entity_type' not in key.data:
            print("[DEBUG] Reading identity")
            if len(data) < identifier_len:
                data += sock.recv(identifier_len - len(data))
            if len(data) < identifier_len:
                sel.register(sock, selectors.EVENT_READ, data={'data': data})
                return

            identifier = data
            sel.register(sock, selectors.EVENT_READ, data={'data': b'', 'identifier': identifier, 'entity_type': get_entity_type(identifier)})
            return

        print("[DEBUG] Entity type: ", key.data['entity_type'])

        if key.data['entity_type'] == WORKER_POD:
            if 'task' not in key.data:
                if len(data) < 1:
                    data += sock.recv(1)
                if len(data) < 1:
                    key_data['data'] = data
                    sel.register(sock, selectors.EVENT_READ, data=key_data)
                    return
                if data == b'\x00':
                    # send cmd and thid
                    key_data['task'] = SEND_THREAD_CMD
                    sel.register(sock, selectors.EVENT_WRITE, data=key_data)
                elif data == b'\x01':
                    # thread is completed
                    key_data['task'] = GET_THREAD_RETCODE
                    sel.register(sock, selectors.EVENT_READ , data=key_data)
                return
            if key_data['task'] == SEND_THREAD_CMD:
                # send cmd and thid
                thid, cmd = get_next_cmd(key_data['identifier'])
                to_send = thid.to_bytes(4, 'little') + len(cmd).to_bytes(4,'little') + cmd
                sel.register(sock, selectors.EVENT_WRITE, data={'data' : b"", 'to_send': to_send, 'task': SEND_THREAD_CMD, 'identifier': key_data['identifier']})
                pass
            elif key_data['task'] == GET_THREAD_RETCODE:
                # get thread id and exit code
                if len(data) < 8:
                    data += sock.recv(8 - len(data))
                if len(data) < 8:
                    key_data['data'] = data
                    sel.register(sock, selectors.EVENT_READ, data=key_data)
                    return
                thid = int.from_bytes(data[:4], 'little')
                exit_code = int.from_bytes(data[4:], 'little')
                sock.close()
                # update db
                if not update_thread_retcode(thid, exit_code, key_data['identifier']):
                    # unauthorized access
                    kill_pod(key_data['identifier'])
                    return
                return


        elif key.data['entity_type'] == FRONTEND_SERVER:
            data += sock.recv(4)
            if len(data) < 4:
                key_data['data'] = data
                sel.register(sock, selectors.EVENT_READ, data=key_data)
                return
            thid = int.from_bytes(data, 'little')
            sock.close()
            print("[DEBUG] New job came up: ", thid)
            new_job_came_up(thid)
            return

    elif mask & selectors.EVENT_WRITE:
        print("[DEBUG] Writing data")
        # send cmd and thid
        n = sock.send(key_data['to_send'])
        key_data['to_send'] = key_data['to_send'][n:]
        if len(key_data['to_send']) > 0:
            sel.register(sock, selectors.EVENT_WRITE, data=key_data)
            return

        sock.close()
        return



print("I JUST STARTED!!")
while True:
    events = sel.select(timeout=None)

    print("[DEBUG] Events: ", events)
    for key, mask in events:
        if key.data is None:
            accept(sel, key.fileobj)
        else:
            service(sel,key, mask)
