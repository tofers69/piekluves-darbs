from flask import Flask, render_template
import sqlite3
app = Flask(__name__)


app.route("/")
def welcome():
    return render_template("welcome.html")




app.route("/Log in")
def log_in ():
    return render_template("log_in.html")




















if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080 ,debug=True )