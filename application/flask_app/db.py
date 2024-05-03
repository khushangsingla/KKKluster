import psycopg2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError 
import nacl
import datetime
from typing import List, Tuple
import psycopg2.extras
import os
import socket


users_table_name = "users"

# Assuming the db passwords etc are the same.
dbName = os.environ.get("POSTGRES_DB","userdata")
dbUser = os.environ.get("POSTGRES_USER","postgres")
dbPass = os.environ.get("POSTGRES_PASSWORD","postgres")
dbHost = os.environ.get("POSTGRES_HOST","10.130.5.209")
dbPort = os.environ.get("POSTGRES_PORT",5432)
pod_identifier = os.environ.get("FRONTEND_SERVER_ID","webapp" + 'a'*(64-6)).encode('utf-8')
service_ip = os.environ.get("JOB_HANDLER_SERVICE_HOST")
service_port = int(os.environ.get("JOB_HANDLER_SERVICE_PORT"))

def createUser(username:str, password:str)->bool:
    """Adds a user with the given username and password to the database. Assumes that the checkIfUsernameFree has already been called before. We hash the password here. Returns true if the user generation happened without any error

    :param username: username
    :type username: str
    :param password: password (hashed)
    :type password: str
    :return: Whether the user creation happened succesfully
    :rtype: bool
    """
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)

        cur = conn.cursor()
        ph = PasswordHasher()
        hashedPassword = ph.hash(password) # Salts and hashes

        cur.execute("SELECT * FROM %s WHERE name = %%s" % users_table_name , [username])
        if len(cur.fetchall()) > 0:
            conn.close()
            return {"error": "User already exists"}

        cur.execute("INSERT INTO %s (role, name, password_hash, priority) VALUES ('guest', %%s, %%s, 60)" % users_table_name, [username, hashedPassword])

        conn.commit()

        cur.execute("SELECT id FROM %s WHERE name = %%s" % users_table_name, [username])
        ret = {"_id": cur.fetchall()[0][0]}

        conn.close()
    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }

    return ret

def db_login(username: str, password: str)->bool:
    """Checks if a given username password pair is present in the db

    :param username: username
    :type username: str
    :param password: password
    :type username: str
    :return: True if the user is authenticated by this
    :rtype: bool
    """
    conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
    cur = conn.cursor()
    cur.execute(f'''
        SELECT id, password_hash FROM {users_table_name} WHERE name = %s
    ''', [username])
    names = cur.fetchall()
    conn.close()
    if len(names) == 0:
        return {"error": "Username Not Present"} #username not present
    else:
        ph = PasswordHasher()
        try:
            ret = ph.verify(names[0][1], password)
            if ret:
                return {"_id": names[0][0]}

        except VerifyMismatchError:
            return {"error": "Wrong Password"} # Password did not match
        return {"error": "Unable to verify password"}

def db_add_task_and_get_tid(image,uid):
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        cur = conn.cursor()
        cur.execute(f'''
            INSERT INTO tasks (image,id) VALUES (%s, %s) RETURNING tid
        ''', [ image,uid])
        tid = cur.fetchall()[0][0]
        conn.commit()
    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }
    conn.close()
    return {"tid": tid}

def db_add_jobs(jobs,tid):
    # Batch add jobs in threads table
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        ins_query = "INSERT INTO threads (cmd,tid) VALUES %s"
        ins_task = [(job,tid) for job in jobs]
        cur = conn.cursor()
        psycopg2.extras.execute_values(cur, ins_query, ins_task, page_size=100)
        conn.commit()
    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }
    conn.close()
    # inform intermediate service
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((service_ip, service_port))
        print("Pod Identifier: ",pod_identifier)
        print("TID: ",tid)
        s.sendall(pod_identifier + tid.to_bytes(4, byteorder='little'))
        s.close()
    except Exception as e:
        if 'error' not in db_delete_job(tid):
            return {"error": "Something went wrong: Couldn't start jobs, deleted instead. Try again later. : " +  str(e)  + "[DEBUG] " + str(pod_identifier) + "\t" + str(tid) + "\t" + str(service_ip) + "\t" + str(service_port)}
        else:
            return {"error": "Serious issues occured: Couldn't start tasks and job couldn't be deleted from db. Try deleting jobs again later. Are you sure this is not close to a downtime? : " +  str(e) }
    return {"tid": tid}

def db_get_jobs(_id):
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        cur = conn.cursor()
        cur.execute('''
            SELECT tid FROM tasks WHERE id = %s
        ''', [_id])
        ret = dict()
        tasks = cur.fetchall()
        for row in tasks:
            cur.execute('''
                SELECT cmd,retval FROM threads WHERE tid = %s
            ''', [row[0]])
            ret[str(row[0])] = cur.fetchall()
        conn.close()

    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }
    return ret

def db_delete_job(jid):
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        cur = conn.cursor()
        cur.execute('''
            DELETE FROM threads WHERE tid = %s;
        ''', [jid])
        cur.execute('''
            DELETE FROM tasks WHERE tid = %s;
        ''', [jid])
        conn.commit()
        conn.close()
    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }
    return {"message": "Job deleted successfully"}

def db_check_job_owner(uid,jid):
    try:
        conn = psycopg2.connect(database = dbName, user = dbUser, password = dbPass, host = dbHost, port = dbPort)
        cur = conn.cursor()
        cur.execute('''
            SELECT id FROM tasks WHERE tid = %s
        ''', [jid])
        ret = cur.fetchall()
        conn.close()
        if len(ret) == 0:
            return {"error": "Job not found"}
        return {"uid":ret[0][0]}
    except Exception as e:
        conn.close()
        return {"error": "Something went wrong " +  str(e) }
