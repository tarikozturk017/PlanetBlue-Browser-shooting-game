import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


db = SQL("sqlite:///game.db")

@app.route("/")
@login_required
def index():

    # it is gonna be the homepage in which the user's top scores will be displayed
    # store top 5 scores of the user
    scores = db.execute("SELECT score FROM scores WHERE user_id = :user_id ORDER BY score DESC LIMIT 5", user_id = session["user_id"])
    return render_template("index.html", scores = scores)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    # if if form submitted via POST, insert the new user into users table.
    if request.method == "POST":
        # do the error checking and return apology for each error.
        # check if the user provide any username
        if not request.form.get("username"):
            return apology("must provide username")
        # check if provide a password
        elif not request.form.get("password"):
            return apology("must provide a password")
        # check if provide confirmation password
        elif not request.form.get("confirmation"):
            return apology("must provide a confirmation password")
        # check if password and confirmation password matches
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("your password and confirmation password do not match")

        # check the username if it's already taken
        username_check = db.execute("SELECT username FROM users WHERE username = :username", username = request.form.get("username"))
        if len(username_check) == 1:
            return apology("This username is already taken")

        # hash the user's password
        hash = generate_password_hash(request.form.get("password"))

        # insert the new user to the users table
        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
        username=request.form.get("username"), hash=hash)

        # remember which user has logged in
        session["user_id"] = new_user_id

        # Display a flash message
        flash("Registered!")

        # return to homepage
        return redirect("/")

    # if request method is GET, return registeration form
    else:
        return render_template("/register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":
        # apology if the current password is blank
        if not request.form.get("current_password"):
            return apology("Must provide current password")
        # store password data to password_data
        password_data = db.execute("SELECT hash FROM users WHERE id = :id", id=session["user_id"])

        # check if the current_password is correct
        if len(password_data) != 1 or not check_password_hash(password_data[0]["hash"], request.form.get("current_password")):
            return apology("Invalid password")

        # apology if the new password is blank
        if not request.form.get("new_password"):
            return apology("Must provide new password")

        # apology if the new password confirmation is blank
        if not request.form.get("new_password_confirmation"):
            return apology("Must provide new password confirmation")

        # check if the new password and new password confirmation match
        elif request.form.get("new_password") != request.form.get("new_password_confirmation"):
            return apology("New password and confirmation must match")

        # Update the database
        new_hash = generate_password_hash(request.form.get("new_password"))
        password_data = db.execute("UPDATE users SET hash = :new_hash WHERE id = :id", id=session["user_id"], new_hash=new_hash)

        flash("Your password has been successfully changed!")

        # forget any user_id
        session.clear()

        # return to homepage
        return redirect("/")

    return render_template("/change_password.html")

@app.route("/instructions")
@login_required
def instructions():

    return render_template("/instructions.html")


@app.route("/top_scores")
@login_required
def top_scores():

    # Top 1 player in the their scores will be displayed
    # join users and scores tables get the data
    top_scores = db.execute("SELECT scores.score, users.username FROM scores INNER JOIN users ON scores.user_id=users.id ORDER BY score DESC LIMIT 10");

    return render_template("/top_scores.html", top_scores=top_scores)


@app.route("/play", methods=["GET", "POST"])
@login_required
def game():

    if request.method == "POST":
        # request "mvar" from browser with the json format
        score = request.get_json().get('mvar')
        # store the score data
        # insert score to the scores table where the user id is session user id
        db.execute("INSERT INTO scores (user_id, score) VALUES (:id, :score)", id=session["user_id"], score=score)

        return render_template("shooting.html")

    else:
        return render_template("shooting.html")