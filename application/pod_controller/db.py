import psycopg2
import random
import time
import os

dbName = os.environ.get("POSTGRES_DB","userdata")
dbUser = os.environ.get("POSTGRES_USER","postgres")
dbPass = os.environ.get("POSTGRES_PASSWORD","postgres")
dbHost = os.environ.get("POSTGRES_HOST","10.130.5.209")
dbPort = os.environ.get("POSTGRES_PORT",5432)


def db_get_thid_to_do(jobid, n = 10):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    except Exception as e:
        print(f"Error1: {e}")
        return []
    while True:
        try:
            cur = conn.cursor()
            print(f"Running cmd: SELECT thid,cmd FROM threads WHERE tid = {jobid} AND status = 'waiting' LIMIT {n}")
            cur.execute(f"SELECT thid,cmd FROM threads WHERE tid = {jobid} AND status = 'waiting' LIMIT {n}")
            rows = cur.fetchall()
            if(len(rows) == 0):
                conn.close()
                break
            print(f"Running cmd: UPDATE threads SET status = 'running' WHERE thid in ({','.join([str(r[0]) for r in rows])})")
            cur.execute(f"UPDATE threads SET status = 'running' WHERE thid in ({','.join([str(r[0]) for r in rows])})")
            conn.commit()
        except Exception as e:
            print(f"Error2: {e}")
            time.sleep(random.randint(1,5))
            continue
        break
    print("Got from db: ",rows[0][0],rows[0][1])
    conn.close()
    if len(rows) == 0:
        return None
    return rows

def db_assign_thid_to_pod(thids,pod):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    except Exception as e:
        print(f"3Error: {e}")
        return False
    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE threads SET pod_name = %s WHERE thids in ({','.join([str(r[0]) for r in thids])})", (pod))
        conn.commit()
    except Exception as e:
        print(f"4Error: {e}")
        return False
    conn.close()
    return True

def db_has_job_finished(jobid):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    except Exception as e:
        print(f"5Error: {e}")
        return False
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT count(*) FROM threads WHERE tid = %s AND (status = 'running' or status = 'waiting')", (jobid))
        rows = cur.fetchall()
    except Exception as e:
        print(f"6Error: {e}")
        return False
    conn.close()
    return rows[0][0] == 0

def db_get_commands_of_job(jobid):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    except Exception as e:
        print(f"7Error: {e}")
        return []
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT cmd FROM threads WHERE tid = {jobid}")
        rows = cur.fetchall()
    except Exception as e:
        print(f"8Error: {e}")
        return []
    conn.close()
    return [r[0] for r in rows]

def db_get_num_pods(jobid):
    return 2

def db_update_thread_retcode(thid, ret_code, jobid):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
    except Exception as e:
        print(f"9Error: {e}")
        return False

    try:
        cur = conn.cursor()
        cur.execute(f"UPDATE threads SET retval = {ret_code} WHERE thid = {thid} AND tid = {jobid}")
        conn.commit()
    except Exception as e:
        print(f"10Error: {e}")
        return False
    conn.close()
    return

def db_get_image(jobid):
    try:
        conn = psycopg2.connect(dbname=dbName, user=dbUser, password=dbPass, host=dbHost, port=dbPort)
    except Exception as e:
        print(f"11Error: {e}")
        return ""
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT image FROM tasks WHERE tid = {jobid}")
        rows = cur.fetchall()
    except Exception as e:
        print(f"12Error: {e}")
        return ""
    conn.close()
    return rows[0][0]
