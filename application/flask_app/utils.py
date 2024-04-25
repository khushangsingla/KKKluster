from db import *
from datetime import datetime

def validate_user(username, password, submit=None, create=None):
    if create is not None and submit is not None:
        return {"error": "Bad request"}

    if create is not None:
        ret = createUser(username, password)
        return ret
    else:
        ret = db_login(username, password)
        return ret

     
def add_tasks_in_db(jobs,image,uid):
    ret = db_add_task_and_get_tid(image,uid)
    if "error" in ret:
        return ret
    ret = db_add_jobs(jobs,ret["tid"])
    return ret
