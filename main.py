from flask import Flask, render_template , request , session
import sqlite3
import os
import calendar

app = Flask(__name__)
app.secret_key = os.urandom(24)

# SQL funkcija
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
   
    
    
    return render_template("welcome.html")



# Vairāku skatu izveidošana un maršutēšana
@app.route("/login")
def login ():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/home")
def home():
    return render_template ("home.html")


# Izveidoju tabulu ,kur tiks saglabāti ieraksti par akcijas, kripto utt tirgu pirkumiem
@app.route("/journal")
def journal():
    execute_sql("CREATE TABLE IF NOT EXISTS Trades(\
                date DATE ,\
                symbol TEXT,\
                buy_sell TEXT,\
                win_loss TEXT,\
                pnl INTEGER,\
                risk INTEGER,\
                confidence TEXT,\
                description TEXT,\
                trade_id INTEGER PRIMARY KEY,\
                user_id INTEGER )")

    user_id = session["user_id"]
    mytrades =  execute_sql("SELECT date , symbol , buy_sell , win_loss, pnl , risk , confidence , description FROM Trades  WHERE user_id  = ? ", (user_id,))

    year = 2025  # The year to display
    full_calendar = ""

    
    for month in range(3, 4):
        cal = calendar.HTMLCalendar().formatmonth(year, month)

        
        for day in range(1, 32):
            day_str = f'>{day}<'
            if day_str in cal:
                cal = cal.replace(day_str, f'><a href="/new_trade-{year}-{month}-{day}"><button type="button">{day}</button></a><')

        full_calendar += f"<h3>{calendar.month_name[month]} {year}</h3>{cal}"

    return render_template ("journal.html", mytrades =mytrades , full_calendar =full_calendar ) 


@app.route("/new_trade-<int:year>-<int:month>-<int:day>")
def new_trade(year, month, day):
    return render_template("newtrade.html", year=year, month=month, day=day)



@app.route("/sumbit" , methods = ["POST" , "GET"])

def submit ():
    
    if request.method == "POST" :
        email = request.form["email"]
        password = request.form["password"]
        
        # Noņem liekas atstarpes
        email = email.strip()
        password = password.strip()

        

        # Pārbauda vai ievadītais emails vai parole nav tuksš pēc atstarpju noņemšanas
        if email =="" or password =="":
            return render_template ("error.html", message="Email/Password cannot be empty ")
        
        # Pārbauda vai ievadītais epasts jau netiek lietots 
        check = execute_sql("SELECT EXISTS (SELECT 1 FROM User WHERE email = ?  )" , (  email ,    )   )

        if check[0][0] == 0:
            # Pievieno no datubāzei
            execute_sql("INSERT INTO User (email , password) VALUES (?,?) ",  (email , password))
            return render_template("login.html")
        else :
            return render_template ( "signup.html", message ="An account with this email already exists")
             
    






@app.route("/submitlog" , methods = ["POST" ])


def submitlog ():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        

        # Pārbauda vai profils ar ievietotajiem datiem eksistē
        check = execute_sql("SELECT EXISTS (SELECT 1 FROM User WHERE email = ?  AND password = ?)" , (  email ,password   )   )
        
        
        
        if check[0][0] == 1:
            # Saglabā sessijas lietotāja id turpmāko datu lietošanai
            user_id = execute_sql("SELECT user_id FROM User WHERE email = ? " , (email,))
            session["user_id"] = user_id[0][0]
            
            # Ielaiž profilā
            return render_template("home.html")
        else:
            return render_template("login.html" , message = "Incorrect email or password")



@app.route("/submit_trade" , methods = ["POST"])
# funkcija kas apstrādā ievadītos datus par akciju tirgu tirgojumiem un ievieto tos datubāze
def submit_trade():
    if request.method == "POST":
        date = request.form["date"]
        symbol = request.form["symbol"]
        buy_sell = request.form["buy_sell"]
        win_loss = request.form["win_loss"]
        risk = request.form["risk"]
        confidence =request.form["confidence"]
        description = request.form["description"]
        # saglabāto sessijas lietotāja ID ievieto kopā ar tirgojumu ,lai varētu kategorizēt datus priekš katra lietotāja
        user_id = session["user_id"]
        if win_loss == "loss":
            pnl = request.form["deficit"]
        else:
            pnl = request.form["profit"]

        print(win_loss)
        execute_sql("INSERT INTO Trades (date , symbol , buy_sell , win_loss, pnl , risk , confidence , description , user_id) VALUES(?,?,?,?,?,?,?,?,?) " , (date , symbol , buy_sell , win_loss , pnl , risk , confidence , description , user_id))
        
        
    return execute_sql("SELECT  * FROM Trades ORDER BY date ASC")









if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080 ,debug=True )