from flask import Flask, render_template , request
import sqlite3
app = Flask(__name__)

def execute_sql(cmd , vals=None):
    conn = sqlite3.connect("main.db")
    cursor = conn.cursor()

    if vals:
        cursor.execute(cmd , vals)
    else:
        cursor.execute(cmd)

    res = cursor.fetchall()

    conn.commit()
    conn.close()
    return res
    

@app.route("/")
def welcome():
    execute_sql("CREATE TABLE IF NOT EXISTS User(\
                user_id INTEGER PRIMARY KEY,\
                email TEXT NOT NULL UNIQUE,\
                password TEXT NOT NULL)")
    
    return render_template("welcome.html")




@app.route("/login")
def login ():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/sumbit" , methods = ["POST" , "GET"])

def submit ():
    
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        email = email.strip()
        password = password.strip()

        if email =="" or password =="":
            return render_template ("error.html", message="Email/Password cannot be empty ")

    execute_sql("INSERT INTO User (email , password) VALUES (?,?) ",  (email , password))

    return render_template("login.html")





@app.route("/submitlog" , methods = ["POST" ])


def submitlog ():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        


        check = execute_sql("SELECT EXISTS (SELECT 1 FROM User WHERE email = ?  AND password = ?)" , (  email ,password   )   )
        
        
        if str(check) == "[(1,)]":
            return render_template("welcome.html")
        else:
            return render_template("signup.html")














if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080 ,debug=True )