from flask import Flask, render_template , request , redirect
import sqlite3

def execute_sql(cmd , vals=None):
    conn = sqlite3.connect("flask.db")
    cursor = conn.cursor()

    if vals:
        cursor.execute(cmd , vals)
    else:
        cursor.execute(cmd)

    res = cursor.fetchall()

    conn.commit()
    conn.close()
    return res
    

app = Flask(__name__)

@app.route("/")
def sakums():
    
    
    execute_sql("CREATE TABLE IF NOT EXISTS Lietotajs(\
                lietotaja_ID INTEGER PRIMARY KEY AUTOINCREMENT,\
                vards TEXT NOT NULL,\
                uzvards TEXT NOT NULL,\
                trenins_ID INTEGER,\
                FOREIGN KEY (trenins_ID) REFERENCES Trenins(ID))")
    return render_template("sakums.html")

@app.route("/jauns_lietotājs")
def pievienot_lietotaju():

    return render_template("jaunsLietotajs.html")



@app.route("/jauns_sports")
def pievienot_sportu():
    execute_sql("CREATE TABLE IF NOT EXISTS Sportaveidi(\
                ID INTEGER PRIMARY KEY AUTOINCREMENT,\
                nosaukums TEXT NOT NULL UNIQUE)")
    return render_template ("jaunsSports.html")

@app.route("/jauns_treninš")
def pievienot_treninu():
    visi_lietotaji = execute_sql("SELECT vards , uzvards FROM Lietotajs ")
    visi_sportaveidi = execute_sql("SELECT nosaukums FROM Sportaveidi")
    
    


    execute_sql( "CREATE TABLE IF NOT EXISTS Trenins(\
                ID INTEGER PRIMARY KEY AUTOINCREMENT,\
                trenina_laiks TEXT NOT NULL,\
                trenina_intensitate INTEGER NOT NULL,\
                lietotajs TEXT,\
                sportaveids TEXT)")
    return render_template ("jaunsTrenins.html" , visi_lietotaji = visi_lietotaji , visi_sportaveidi = visi_sportaveidi)

@app.route("/sportaveidu_saraksts")
def sporta_saraksts():
    visi_sportaveidi = execute_sql("SELECT nosaukums FROM Sportaveidi  ORDER BY nosaukums ASC")
    return render_template ("sportaveiduSaraksts.html" , visi_sportaveidi = visi_sportaveidi)

@app.route("/treninu_saraksts")
def treninu_saraksts():
    trenini = execute_sql ("SELECT ID ,lietotajs , sportaveids , trenina_intensitate , trenina_laiks FROM Trenins")
    
   
    return render_template ("treninuSaraksts.html", trenini = trenini)

@app.route("/lietotaju_saraksts")
def lietotaju_saraksts():
    lietotaja_sports = execute_sql("SELECT lietotajs, sportaveids  , COUNT(*) AS skaits FROM Trenins GROUP BY lietotajs, sportaveids ORDER BY lietotajs ,skaits DESC    ")
    dic = {}
    for row in lietotaja_sports:
        lietotajs = row[0]  
        sportaveids = row[1]  
        skaits = row[2]  

    
        if lietotajs not in dic:
            dic[lietotajs] = []
            dic[lietotajs].append((sportaveids, skaits))
   
        
        else:
            if dic[lietotajs][0][1] < skaits :
                     dic[lietotajs].pop(0)
                     dic[lietotajs].append((sportaveids, skaits))
            elif dic[lietotajs][0][1] == skaits:
                dic[lietotajs].append((sportaveids, skaits))
                
            else:
                pass
    
    dic_str = str(dic)
    saraksts = dic_str.split()



    lietotaju_intensitate = execute_sql("SELECT lietotajs ,  AVG(trenina_intensitate)  FROM Trenins GROUP BY lietotajs   ")


    lietotaju_laiks = execute_sql("SELECT  lietotajs , trenina_laiks , COUNT(trenina_laiks) AS reizes FROM Trenins GROUP BY trenina_laiks ,lietotajs ORDER BY lietotajs ,reizes DESC")
    sorted_lietotaju_laiks = []
    seen_users = []

    for user in lietotaju_laiks:
        user_name = user[0]
        if user_name in seen_users:
            pass
        else:
            sorted_lietotaju_laiks.append(user)
            seen_users.append(user_name)





        
    return render_template ("lietotajuSaraksts.html" , saraksts = saraksts , lietotaju_intensitate = lietotaju_intensitate , sorted_lietotaju_laiks = sorted_lietotaju_laiks)



@app.route("/nolasīšana" , methods = ["GET" , "POST"])
def jauns_lietotajs():
    jauns_lietotajs = {}
    if request.method =="POST":
        jauns_lietotajs["Vārds"] = request.form["Vārds"]
        jauns_lietotajs["Uzvārds"] = request.form["Uzvārds"]
    execute_sql("INSERT INTO Lietotajs(vards , uzvards) VALUES (?,?)", (
        jauns_lietotajs["Vārds"],
        jauns_lietotajs["Uzvārds"]
    ))
    return render_template("submit.html")

@app.route("/nolasīšana2" , methods = ["POST" , "GET"])
def jauns_trenins():
    jauns_trenins = {}
    if request.method == "POST" :
        jauns_trenins["laiks"] = request.form["laiks"] 
        jauns_trenins["intensitāte"] = request.form ["intensitāte"] 
        jauns_trenins["lietotāji"] = request.form["lietotāji"]
        jauns_trenins["sportaveidi"] = request.form["sportaveidi"]
    execute_sql("INSERT INTO Trenins (trenina_laiks , trenina_intensitate , lietotajs , sportaveids) VALUES (?,?,?,?)",(
        jauns_trenins["laiks"],
        jauns_trenins["intensitāte"],
        jauns_trenins["lietotāji"],
        jauns_trenins["sportaveidi"]

    )) 
    return render_template("submit.html")


@app.route("/nolasīšana3" , methods = ["POST" , "GET"] )
def jauns_sportaveids () :
    jauns_sportaveids = {}
    if request.method ==  "POST" :
        jauns_sportaveids["nosaukums"] = request.form["nosaukums"]
    execute_sql ("INSERT INTO Sportaveidi (nosaukums) VALUES (?)", (
        jauns_sportaveids["nosaukums"],
    ))

    return render_template("submit.html")

@app.route("/izdzest" , methods = ["POST" , "GET"] )
def izdzest ():
    
    ID = request.form["ID"]

    execute_sql("DELETE FROM Trenins WHERE ID = ? ", (ID,))

    return render_template("submit.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080 ,debug=True )
    


