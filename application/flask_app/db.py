import psycopg2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError 
import nacl
import datetime
from typing import List, Tuple
import psycopg2.extras
dbName = "userdata"

users_table_name = "users"

# Assuming the db passwords etc are the same.
dbUser = "postgres"
dbPass = "postgres"
dbHost = "10.130.5.209"
dbPort = 5432

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
        return {"error": "Something went wrong " +  str(e) }
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
        return {"error": "Something went wrong " +  str(e) }
    return {"tid": tid}
