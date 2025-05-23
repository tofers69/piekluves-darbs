from flask import Flask, render_template , request , session ,redirect , url_for
import sqlite3
import os
import calendar
import requests
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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

    return render_template ("home.html", news = session["news"])


# Izveidoju tabulu ,kur tiks saglabāti ieraksti par akcijas, kripto utt tirgu pirkumiem
@app.route("/journal" , methods=[ "POST" , "GET"])
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

    
    # Kalendāra izveide ar importētām funkcijām
    current_date = datetime.now()
    year = request.form.get("year", current_date.year, type=int)
    month = request.form.get("month", current_date.month, type=int)
    
    full_calendar=""
    cal = calendar.HTMLCalendar().formatmonth(year, month)
    
    user_id = session["user_id"]
    for day in range(1, 32):
        
        try:
            
            date = (f"{year}-{month}-{day}")
            # Katrai dienai aprēķinu kopēju peļņu/zaudi
            pnl = execute_sql("SELECT COALESCE((SELECT SUM(pnl) FROM Trades WHERE win_loss = 'win' AND date = ? AND user_id = ?), 0)-COALESCE((SELECT SUM(pnl) FROM Trades WHERE win_loss = 'loss' AND date = ? AND user_id = ?), 0) AS result ", (date, user_id , date , user_id))            # Pārbaudu katrai dienai vai ir peļņa , zaude vai pa nullēm ,lai varētu katrai but savādāks dizains
            if pnl[0][0] < 0:
                id = "-day"
            elif pnl[0][0] > 0 :
                id = "+day"
            else:
                id = "day"
          
            day_str = f'>{day}<'
            if day_str in cal:
                # Kalendāram katrai dienai izveidoju pogu ,kuru uzspiežot var pievienot "trade" priekš tās dienas ,neievadot datumu
                cal = cal.replace(day_str, f'><a href="/new_trade-{year}-{month:02d}-{day:02d}" id="{id}"><button type="button">{day} <br> {pnl[0][0]} € </button></a><')
        except ValueError:
            continue
    full_calendar += f"{cal}"

    return render_template("journal.html", full_calendar=cal, year=year, month=month)

@app.route("/new_trade-<int:year>-<int:month>-<int:day>")
# funkcija ,kas tiek palaista uzspiežot uz jebkuru dienu kalendārā ,ar padoto datumu linkā
def new_trade(year, month, day):
    user_id = session["user_id"]
    date = f"{year}-{month}-{day}"
    # tiek saglabāti "tradi" no konkrēta datumu ,lai tos varētu parādīt ,kā vēsturi
    trades = execute_sql("SELECT  date , symbol , buy_sell , win_loss, pnl , risk , confidence , description ,trade_id FROM Trades WHERE date  = ? AND user_id = ?" , (date , user_id) )
    
    return render_template("newtrade.html", year=year, month=month, day=day , trades = trades )

# Skats kur varēs apskatīt analītikas un statistikas par veiktajiem "tradiem".
@app.route("/analytics")
def stats ():
    user_id = session["user_id"]
    wins = execute_sql("SELECT COUNT(*) FROM Trades Where user_id = ? AND win_loss = 'win' " , (user_id,))
    losses = execute_sql("SELECT COUNT(*) FROM Trades Where user_id = ? AND win_loss = 'loss' " , (user_id,))
    if wins[0][0] > 0 and losses[0][0] > 0:
        
        trade_amount = execute_sql("SELECT COUNT(*) FROM Trades Where user_id = ?  " , (user_id,))
        win_rate = round(wins[0][0]/trade_amount[0][0] * 100)
        
        highest_win = execute_sql("SELECT pnl , date FROM Trades WHERE win_loss = 'win' AND user_id = ? ORDER BY pnl DESC LIMIT 1  " , (user_id,)) 
        highest_loss = execute_sql("SELECT pnl , date FROM Trades WHERE win_loss = 'loss' AND user_id = ? ORDER BY pnl DESC LIMIT 1  " , (user_id,)) 

        total_pnl = execute_sql("SELECT COALESCE((SELECT SUM(pnl) FROM Trades WHERE win_loss = 'win' AND user_id = ?), 0) - ""COALESCE((SELECT SUM(pnl) FROM Trades WHERE win_loss = 'loss' AND user_id = ?), 0)",(user_id, user_id))
        
        average_win = execute_sql("SELECT AVG(pnl) FROM Trades WHERE win_loss = 'win' AND user_id = ? " , (user_id,)) 
        average_loss = execute_sql("SELECT AVG(pnl) FROM Trades WHERE win_loss = 'loss' AND user_id = ? " , (user_id,))
        win_loss_ratio = round( average_win[0][0] / average_loss[0][0] ,1)

        most_traded = execute_sql("SELECT symbol, COUNT(symbol) AS  symbol_count FROM Trades WHERE user_id = ? GROUP BY symbol ORDER BY symbol_count DESC LIMIT 1" , (user_id,))
        
        return render_template("analytics.html" ,win_rate = win_rate ,trade_amount = trade_amount[0][0] , highest_win = highest_win[0][0] , highest_win_date = highest_win[0][1] , highest_loss = highest_loss[0][0] ,highest_loss_date = highest_loss[0][1] , total_pnl = total_pnl[0][0] , average_win = round(average_win[0][0],2), average_loss =round( average_loss[0][0],2) ,win_loss_ratio = win_loss_ratio ,most_traded = most_traded[0][0])
    else:
        # Lai analītikas par "traidiem" varētu but aprēķinātas ir vajadzīga vismaz viena uzvara un viena zaude
        return render_template("error.html", message = "Not Enough Trades For Analytics .Minimum : 1 Win & 1 Loss .")
        
@app.route("/submit" , methods = ["POST" , "GET"])

def submit ():
    
    if request.method == "POST" :
        email = request.form["email"]
        password = request.form["password"]
        
        # Noņem liekas atstarpes
        email = email.strip()
        password = password.strip()
        # Paroli teik "hashota" ar kriptogrāfiju , lai lietotāja dati būtu pasargāti
        hashed_password = generate_password_hash(password)

        # Pārbauda vai ievadītais emails vai parole nav tuksš pēc atstarpju noņemšanas
        if email =="" or password =="":
            return render_template ("error.html", message="Email/Password cannot be empty ")
        
        # Pārbauda vai ievadītais epasts jau netiek lietots 
        check = execute_sql("SELECT EXISTS (SELECT 1 FROM User WHERE email = ?  )" , (  email ,    )   )

        if check[0][0] == 0:
            # Pievieno no datubāzei
            execute_sql("INSERT INTO User (email , password) VALUES (?,?) ",  (email , hashed_password))
            return render_template("login.html")
        else :
            return render_template ( "signup.html", message ="An account with this email already exists")
             

@app.route("/submitlog", methods=["POST", "GET"])
def submitlog():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = execute_sql("SELECT user_id, password FROM User WHERE email = ?", (email,))

        # Pārbauda vai ievadīta parole sakrīt ar "hashoto" paroli
        if user and check_password_hash(user[0][1], password):
            # saglabā lietotāja id , priekš sesijas ,lai vēlāk varētu to lietotot priekš datubāzes lietošanas
            session["user_id"] = user[0][0]

            # API finkcija ,kas savāc datus par pasaules ekomiskajām ziņām lietošanas bŗīža dienā ar limitu requestiem vienreiz piecās minūtēs
            url: str = "https://www.jblanked.com/news/api/forex-factory/calendar/today/"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key DYibXX4P.rn7fKN0jPM0oozVFrkWO3VA32JU1Ch5J ",
            }
            response = requests.get(url, headers=headers)
            news = []

            if response.status_code == 200:
                data = response.json()
                # Ja datu koppa nav tukša tiek atgriezti datu nosaukums , kuru valūtu ziņas ietekmē un datums
                for result in data:
                    news.append([result["Name"], result["Currency"], result["Date"]])
            else:
                print(f"Error: {response.status_code}")
                print(response.json())

            session["news"] = news
            

            return render_template("home.html", news=news)
        else:
            return render_template("login.html", message="Incorrect email or password")




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
        print(win_loss)
        if win_loss == "win":
            pnl = request.form["profit"]
        else:
            pnl = request.form["deficit"]

        
        execute_sql("INSERT INTO Trades (date , symbol , buy_sell , win_loss, pnl , risk , confidence , description , user_id) VALUES(?,?,?,?,?,?,?,?,?) " , (date , symbol , buy_sell , win_loss , pnl , risk , confidence , description , user_id))
        
        
    year, month, day = date.split("-")

    
    return redirect(url_for("new_trade", year=year, month=month, day=day))

# Opcija izdzēst kādu ievadījumu no datubāzes
@app.route ("/delete" , methods = ["POST"])
def delete():
    trade_id = request.form["trade_id"]
    date = request.form["date"]
    execute_sql("DELETE FROM Trades WHERE trade_id = ?" , (trade_id,))

    year, month, day = date.split("-")

    
    return redirect(url_for("new_trade", year=year, month=month, day=day))
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080 ,debug=True )