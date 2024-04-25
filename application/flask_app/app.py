import jwt, os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, make_response
import json
from utils import *
# from auth_middleware import token_required

load_dotenv()

app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY", 'fj29823hfji23g78eryrh2uiyUIGUIRGGT3783r7f_UTjty')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')

app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
app.config["SESSION_COOKIE_SAMESITE"] = "strict"


def authorize(req):
    try:
        token = req.cookies.get("token")
        _id = req.cookies.get("_id")
    except Exception as e:
        return None
    if not token or not _id:
        return None
    if token:
        token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        if str(token['user_id']) != str(_id):
            return None
        return _id

@app.route("/")
def hello():
    ret = authorize(request)
    if ret:
        return render_template("submit_jobs.html",userid=str(ret))
    return render_template("login.html", error=None)

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.form
        if not data:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        # validate input
        user = validate_user(**data)
        if "error" in user:
            return {
                "message": "Invalid data",
                "data": None,
                "error": user["error"]
            }, 400
        if user is None:
            return dict(message="Server Error"), 500
        if user:
            try:
                # token should expire after 24 hrs
                user["token"] = jwt.encode(
                    {"user_id": user["_id"]},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                resp = make_response(render_template("submit_jobs.html",userid=str(user["_id"])))
                resp.set_cookie("token", user["token"], max_age=86400)
                resp.set_cookie("_id", str(user["_id"]), max_age=86400)
                return resp
            except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500


@app.route("/submit_jobs", methods=["POST"])
def submit_jobs():
    ret = authorize(request)
    if not ret:
        return render_template("login.html")
    try:
        data = request.files
        task_ret = add_tasks_in_db(data['textfile'].read().decode("ascii").split("\n"),request.form["image_link"],ret)
        if "error" in task_ret:
            return render_template("submit_jobs.html",userid=str(ret), message=str(task_ret["error"]))
        return render_template("submit_jobs.html",userid=str(ret), message=f"Jobs Submitted Successfully : {task_ret['tid']}")
    except Exception as e:
        raise e
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500

if __name__ == "__main__":
    app.run(debug=True)

