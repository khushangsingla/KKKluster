import db
import k8s
import os
import socket
import time
import selectors

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
lsock.bind((IP_ADDRESS, PORT))
lsock.listen()

sel = selectors.DefaultSelector()
sel.register(lsock, selectors.EVENT_READ, data=None)

WORKER_POD = 1
FRONTEND_SERVER = 2

def new_job_came_up(jid):
    """
    A new job has been registered in the db
    """
    pass

def kill_pod(identifier):
    """
    Kills the pod with the given identifier
    """
    pass

def get_next_cmd(identifier):
    """
    returns a tuple thid, cmd
    """
    pass

def update_thread_retcode(thid, exit_code, identifier):
    """
    Updates the exit code of the thread in the db
    returns false if unauthorized access
    """
    pass

def get_entity_type(identifier):
    """
    returns the entity type of the identifier - WORKER_POD or FRONTEND_SERVER
    """
    pass

def accept(sel, sock):
    conn, addr = sock.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ , data={'data': b''})

def service(sel,key, mask):
    sock = key.fileobj
    data = key.data['data']
    key_data = key.data
    sel.unregister(sock)

    if mask & selectors.EVENT_READ:
        if 'identity' not in key.data:
            if len(data) < identifier_len:
                data += sock.recv(identifier_len - len(data))
            if len(data) < identifier_len:
                sel.register(sock, selectors.EVENT_READ, data={'data': data})
                return

            identifier = data
            sel.register(sock, selectors.EVENT_READ, data={'data': b'', 'identifier': identifier, 'entity_type': get_entity_type(identifier)})
            return

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
            new_job_came_up(thid)

    elif mask & selectors.EVENT_WRITE:
            # send cmd and thid
            n = sock.send(key_data['to_send'])
            key_data['to_send'] = key_data['to_send'][n:]
            if len(key_data['to_send']) > 0:
                sel.register(sock, selectors.EVENT_WRITE, data=key_data)
                return

            sock.close()
            return



while True:
    events = sel.select(timeout=None)

    for key, mask in events:
        if key.data is None:
            accept(sel, key.fileobj)
        else:
            service(sel,key, mask)
