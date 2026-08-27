from flask import Blueprint, render_template, request, session


main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        username = request.form["username"]
        session["username"] = username

    username = session.get("username")
    message = request.args.get("message")

    return render_template(
        "home.html",
        username=username,
        message=message
    )