import psycopg2
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
            cur.execute(f"SELECT thid FROM threads WHERE jobid = %s AND status = 'waiting' LIMIT {n}", (jobid))
            rows = cur.fetchall()
            cur.execute(f"UPDATE threads SET status = 'running' WHERE thid in ({','.join([str(r[0]) for r in rows])})")
            cur.commit()
        except Exception as e:
            print(f"Error2: {e}")
            continue
        break
    conn.close()
    return [r[0] for r in rows]

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
        cur.commit()
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
        cur.execute(f"SELECT count(*) FROM threads WHERE jobid = %s AND (status = 'running' or status = 'waiting')", (jobid))
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
        cur.execute(f"SELECT cmd FROM threads WHERE jobid = %s", (jobid))
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
        cur.execute(f"UPDATE threads SET ret_code = %s WHERE thid = %s AND jobid = %s", (ret_code, thid, jobid))
        cur.commit()
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
