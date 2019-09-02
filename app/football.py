from flask import Flask, render_template, url_for, redirect, request, flash, session, g, abort, jsonify
from crudClass import Team
import sqlite3, os, smtplib, itertools, random, datetime
import pygal
from pygal import style
from passlib.hash import argon2
from flask_login import LoginManager
from functools import wraps
from twilio.rest import Client

app = Flask(__name__)

app.secret_key = "!@#$%^&*()a-=afs;'';312$%^&*k-[;.sda,./][p;/'=-0989#$%^&0976678v$%^&*(fdsd21234266OJ^&UOKN4odsbd#$%^&*(sadg7(*&^%32b342gd']"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def sqlconnection():
    conn = sqlite3.connect("football.db")
    return conn


@login_manager.user_loader
def load_user(id):
    conn = sqlconnection()
    cursor = conn.execute("SELECT ID FROM USERS WHERE ID=?", (id)).fetchone()[0]
    conn.close()
    return int(cursor)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == "POST":
        conn = sqlconnection()

        cursor = conn.execute("SELECT  PHONENUMBER FROM USERS WHERE PHONENUMBER=?",
                              (request.form.get("phone", 0),)).fetchone()
        cursor1 = conn.execute("SELECT EMAIL FROM USERS WHERE EMAIL=?", (request.form["email"],)).fetchone()

        if cursor:
            flash("Dude you need to take some different a Phone Number")
            return render_template("register.html")
        elif cursor1:
            flash("Dude you need to take some different email")
            return render_template("register.html")
        else:
            if str(request.form["cpassword"]) == str(request.form['password']):
                password = argon2.hash(str(request.form['password']))
                conn.execute(
                    "INSERT INTO USERS(FULLNAME, PASSWORD, EMAIL, REGISTEREDON  , PHONENUMBER) VALUES (?,?,?,? , ?)",
                    (request.form['username']
                     , password, request.form['email'], datetime.datetime.utcnow(), request.form.get("phone", 0)))
                conn.commit()
            else:
                flash("Dude you need to enter same password")
                return render_template("register.html")
        conn.close()
        flash('User successfully registered')
        return redirect(url_for('login'))


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session or 'admin' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been Logged out")
    return redirect(url_for("teamInfo"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not ('logged_in' in session):
        if request.method == 'GET':
            return render_template('login.html')
        else:
            phone = request.form['phone']
            password = request.form['password']
            conn = sqlconnection()
            cursor = conn.execute("SELECT PHONENUMBER ,PASSWORD FROM USERS WHERE PHONENUMBER=? ", (phone,)).fetchone()
            conn.close()
            if cursor is None:
                flash('Invalid Credentials', 'error')
                return redirect(url_for('login'))
            else:
                if argon2.verify(password, cursor[1]):
                    if phone == "8197056461":
                        session['admin'] = "admin"
                        session['phone'] = phone
                        flash('Welcome Admin')

                    else:
                        flash('Logged in successfully')
                        session['logged_in'] = True
                        session['phone'] = phone
                    return redirect(url_for('teamInfo'))
                else:
                    flash('Invalid Credentials', 'error')
                    return redirect(url_for('login'))
    else:
        return "already logged in"


def send_confirmation_code(to_number):
    verification_code = generate_code()
    send_sms(to_number, verification_code)
    session['verification_code'] = verification_code
    session['phone'] = to_number
    return verification_code


def generate_code():
    return str(random.randrange(100000, 999999))


def send_sms(to_number, body):
    account_sid = "ACfd45034bed17278218be3bea65bb3aef"
    auth_token = "237ad00d1a4e907e055b3af46f50bd44"
    twilio_number = "+1 479-777-2571"
    body = "Your one time password is " + body
    client = Client(account_sid, auth_token)
    client.api.messages.create(to_number,
                               from_=twilio_number,
                               body=body)


@app.route("/verifypassword", methods=["GET", "POST"])
def verifypassword():
    if request.method == "GET":
        return render_template("verifypassword.html", tad1=True)
    elif request.method == "POST":
        if not ("OTP" in request.form):
            phone = request.form.get("phone", 0)
            conn = sqlconnection()
            cursor = conn.execute("SELECT PHONENUMBER  FROM USERS WHERE PHONENUMBER=? ", (phone,)).fetchone()
            conn.close()
            if cursor is None:
                flash('Invalid Credentials', 'error')
                return render_template("verifypassword.html", tad1=True)
            else:
                phone = "+91" + phone
                send_confirmation_code(phone)
                return render_template("verifypassword.html", tad1=False)
        elif "OTP" in request.form:
            otp = request.form.get("OTP", 0)
            if "verification_code" in session:
                if otp == session["verification_code"]:
                    return redirect(url_for("changepassword"))
                else:
                    flash("Wrong OTP")
                    return render_template("verifypassword.html", tad1=False)


@app.route("/changedpassword", methods=["GET", "POST"])
def changepassword():
    if request.method == "GET":
        if "phone" in session:
            return render_template("passwordchange.html")
    elif request.method == "POST":
        if str(request.form["cpassword"]) == str(request.form['password']):
            if "phone" in session:
                phone = session["phone"]
                phone = phone.partition("+91")[2]
                password = argon2.hash(str(request.form['password']))

                conn = sqlconnection()
                conn.execute("UPDATE USERS SET PASSWORD = ? WHERE PHONENUMBER =?", (password, phone,))
                conn.commit()
                conn.close()
                flash("Password Updated Succesfully")
                session.pop("phone")
                session.pop("verification_code")
                return redirect(url_for("login"))
        else:
            flash("enter the same password")
            return redirect(url_for("changepassword"))


@app.route('/test')
def hello_world():
    return "working Success"


@app.route("/editTeam/<string:teamName>/", methods=["GET", "POST"])
@login_required
def editTeam(teamName):
    conn = sqlconnection()
    if request.method == "GET":
        cursor = conn.execute("SELECT  * FROM TEAM WHERE TEAM_NAME=?", (teamName,)).fetchone()
        print(os.getcwd())
        b = ["teamName",
             "teamLogo",
             "squadPic",
             "founded",
             "homeGround",
             "teamCost",
             "teamWebsite",
             "teamOwner",
             "teamCoach",
             "teamSponsor",
             "country",
             "about"]
        teamInfo = dict(zip(b, cursor))
        conn.close()
        return render_template("teamEditForm.html", teamInfo=teamInfo)

    elif request.method == "POST":
        t = Team(teamName)
        about = request.form.get("teamAbout", None)
        if about.strip() == "":
            about = "This team is prominent team in league"
        t.insert_team(teamLogo=request.form.get("teamLogo", None),
                      squadpic=request.form.get("squadPic", None),
                      founded=request.form.get("founded", None),
                      homeground=request.form.get("homeGround", None),
                      teamcost=eval(request.form.get("teamCost", 0)),
                      teamWebsite=request.form.get("teamWebsite", None),
                      teamowner=request.form.get("teamOwner", None),
                      teamcoach=request.form.get("teamCoach", None),
                      sponser=request.form.get("teamSponsor", None),
                      country=request.form.get("country", None),
                      about=about,
                      operation="update")

        flash("You Just Edited a Team  " + teamName, "message")
        executeTrigger(teamName)
        return redirect(url_for("showTeam"))


def executeTrigger(teamName):
    print(session['phone'])
    conn = sqlconnection()
    conn.execute('''CREATE TRIGGER IF NOT EXISTS LOGS AFTER UPDATE ON TEAM 
BEGIN 
INSERT INTO TEAM_LOG(TEAM_NAME, UPDATEON) VALUES (old.TEAM_NAME,datetime('now'));
END;
''')
    conn.commit()
    conn.close()


@app.route("/addTeam/", methods=["POST", "GET"])
@login_required
def addTeam():
    if request.method == 'POST':

        about = request.form.get("teamAbout", None)
        if about.strip() == "":
            about = "This team is prominent team in league"
        t = Team(request.form.get("teamName", None))
        t.insert_team(teamLogo=request.form.get("teamLogo", None),
                      squadpic=request.form.get("squadPic", None),
                      founded=request.form.get("founded", None),
                      homeground=request.form.get("homeGround", None),
                      teamcost=eval(request.form.get("teamCost", 0)),
                      teamWebsite=request.form.get("teamWebsite", None),
                      teamowner=request.form.get("teamOwner", None),
                      teamcoach=request.form.get("teamCoach", None),
                      sponser=request.form.get("teamSponsor", None),
                      country=request.form.get("country", None),
                      about=about,
                      operation="insert")
        flash("You Just Added " + request.form.get("teamName", None) + " in league")
        return redirect(url_for("showTeam"))
    else:
        return render_template("teamAddForm.html")


@app.route("/json")
@app.route("/", methods=["GET", "POST"])
def teamInfo():
    try:
        if request.method == "GET":
            conn = sqlconnection()
            cursor = conn.execute("SELECT  TEAM_NAME FROM TEAM ")
            b = ["teamName"]
            list1 = []

            cursor1 = conn.execute("SELECT PLAYER_NAME  FROM PLAYER ").fetchall()
            z = [dict(zip(["playerName"], line)) for line in cursor1]
            for line in cursor:
                list1.append(dict(zip(b, line)))
            conn.close()
            rule = request.url_rule
            if request.path == "/":
                return render_template("index.html", teamNamess=list1, player_list=z)
            else:
                return jsonify(list1)
        elif request.method == "POST":
            conn = sqlconnection()
            cursor1 = conn.execute("SELECT TEAM_NAME, PLAYER_ID FROM PLAYER WHERE PLAYER_NAME =? ",
                                   (request.form.get("searchBox", None),)).fetchone()

            conn.close()
            if not (cursor1 is None):
                return redirect(url_for("viewPlayer", teamName=cursor1[0], playerId=cursor1[1]))
            else:
                return render_template("error.html")

    except Exception as e:
        return render_template("index.html")


@app.route("/showTeam/")
def showTeam():
    try:
        conn = sqlconnection()
        cursor = conn.execute("SELECT * FROM TEAM ")
        b = ["teamName",
             "teamLogo",
             "squadPic",
             "founded",
             "homeGround",
             "teamCost",
             "teamWebsite",
             "teamOwner",
             "teamCoach",
             "teamSponsor",
             "country",
             "about"]
        list1 = []
        for line in cursor:
            list1.append(dict(zip(b, line)))
        conn.close()
        return render_template("allTeam.html", teamInformation=list1, len=len(list1))
    except Exception as e:
        return render_template("allTeam.html")


@app.route("/team_view/<string:teamName>")
def viewTeam(teamName):
    conn = sqlconnection()
    conn.execute('PRAGMA FOREIGN_KEYS = ON ')
    cursor = conn.execute("SELECT  * FROM TEAM WHERE TEAM_NAME =?", (teamName,)).fetchone()
    cursor1 = conn.execute("SELECT PLAYER_NAME , JERSEY_NUMBER FROM PLAYER WHERE PLAYER.TEAM_NAME=? ", (teamName,))
    b = ["teamName",
         "teamLogo",
         "squadPic",
         "founded",
         "homeGround",
         "teamCost",
         "teamWebsite",
         "teamOwner",
         "teamCoach",
         "teamSponsor",
         "country",
         "about"]
    teamInfo = dict(zip(b, cursor))
    z = [dict(zip(["playerName", "jerseyNum"], line)) for line in cursor1]
    conn.close()
    return render_template("teaminfo.html", teamdata=teamInfo, playerData=z)


@app.route("/team_delete/<string:teamName>", methods=["POST"])
@login_required
def deleteTeam(teamName):
    if request.method == "POST":
        conn = sqlconnection()
        conn.execute('PRAGMA FOREIGN_KEYS = ON ')
        conn.execute("DELETE FROM TEAM WHERE TEAM_NAME=?", (teamName,))
        conn.commit()
        conn.close()
        flash("You Just Deleted a Team " + teamName)
        return redirect(url_for("showTeam"))


@app.route("/teamPlayers/<string:teamName>")
def teamPlayers(teamName):
    conn = sqlconnection()
    conn.execute('PRAGMA FOREIGN_KEYS = ON ')
    cursor = conn.execute("SELECT  * FROM PLAYER WHERE TEAM_NAME =?", (teamName,))
    try:
        b = ["teamName", "playerId", "playerName", "country", "playerAge", "playerPhoto",
             "playerDate", "numberOfGoals", "playerPosition", "playerCost",
             "playerJerseyNum", "about"]
        list1 = []
        for cursor1 in cursor:
            list1.append(dict(zip(b, cursor1)))
        return render_template("teamplayers.html", teamPlayersData=list1, teamNamee=list1[0]["teamName"],
                               len=len(list1))

    except:
        return render_template("teamplayers.html", teamNamee=teamName, len=0)
    finally:
        conn.close()


@app.route("/addplayers/<string:teamName>", methods=["GET", "POST"])
@login_required
def addPlayers(teamName):
    if request.method == "POST":
        t = Team(teamName)
        about = request.form.get("about", None)
        if about == "" or about == " ":
            about = "This Player is a prominent Player in " + teamName

        t.insertPlayer(playername=request.form.get("playerName", None),
                       country=request.form.get("country", None),
                       age=request.form.get("playerAge", None),
                       dateofbirth=request.form.get("playerDateOfBirth", None),
                       numberofgoals=request.form.get("numberOfGoals", None),
                       photo=request.form.get("playerPhoto", None),
                       playerposition=request.form.get("playerPosition", None),
                       playercost=request.form.get("playerCost", None),
                       jerseynum=request.form.get("playerJerseyNum", 0),
                       about=about,
                       operation="insert",
                       oldPlayerid="")
        flash("You Just Added " + request.form.get("playerName", None) + " in " + teamName)
        return redirect(url_for("teamPlayers", teamName=teamName))
    elif request.method == "GET":
        return render_template("playerAddForm.html")


@app.route("/editplayers/<string:teamName>/<int:playerId>", methods=["GET", "POST"])
@login_required
def editPlayers(teamName, playerId):
    if request.method == "POST":
        t = Team(teamName)
        about = request.form.get("about", None)
        if about.strip() == "":
            about = "This Player is a prominent Player in " + teamName

        t.insertPlayer(playername=request.form.get("playerName", None),
                       country=request.form.get("country", None),
                       age=request.form.get("playerAge", None),
                       dateofbirth=request.form.get("playerDateOfBirth", None),
                       numberofgoals=request.form.get("numberOfGoals", None),
                       photo=request.form.get("playerPhoto", None),
                       playerposition=request.form.get("playerPosition", None),
                       playercost=request.form.get("playerCost", None),
                       jerseynum=request.form.get("playerJerseyNum", 0),
                       about=about,
                       operation="update",
                       oldPlayerid=playerId)
        flash("You Just Updated " + request.form.get("playerName", None) + " Information", "message")
        return redirect(url_for("teamPlayers", teamName=teamName))
    elif request.method == "GET":
        conn = sqlconnection()
        conn.execute('PRAGMA FOREIGN_KEYS = ON ')
        cursor = conn.execute("SELECT * FROM PLAYER WHERE PLAYER_ID =?", (playerId,)).fetchone()
        mydict = {"Goalkeeper": "Goalkeeper",
                  "Right full back": "Right full back",
                  "Left full back": " Left full back",
                  "Right half back": "Right half back",
                  "Centre half back": "Centre half back",
                  "Left half back": "Left half back"}

        b = ["teamName", "playerId", "playerName", "country", "playerAge", "playerPhoto",
             "playerDate", "numberOfGoals", "playerPosition", "playerCost",
             "playerJerseyNum", "about"]
        abc = dict(zip(b, cursor))
        return render_template("playerEditForm.html", teamPlayerData=abc, mydict=mydict, target=abc["playerPosition"])


@app.route("/deleteplayers/<string:teamName>/<int:playerId>", methods=["POST"])
@login_required
def deletePlayers(teamName, playerId):
    if request.method == "POST":
        conn = sqlconnection()
        conn.execute('PRAGMA FOREIGN_KEYS = ON ')

        conn.execute('''DELETE FROM PLAYER WHERE PLAYER_ID =?''', (playerId,))
        conn.commit()
        conn.close()
        flash("you just deleted a player from " + teamName, "message")
        return redirect(url_for("teamPlayers", teamName=teamName))


@app.route("/viewPlayer/<string:teamName>/<int:playerId>")
def viewPlayer(teamName, playerId):
    conn = sqlconnection()
    conn.execute('PRAGMA FOREIGN_KEYS = ON ')

    cursor = conn.execute('''SELECT * FROM PLAYER WHERE PLAYER_ID =?''', (playerId,)).fetchone()
    b = ["teamName", "playerId", "playerName", "country", "playerAge", "playerPhoto",
         "playerDate", "numberOfGoals", "playerPosition", "playerCost",
         "playerJerseyNum", "about"]
    abc = dict(zip(b, cursor))
    cursorLogo = conn.execute('''SELECT TEAM_LOGO_URL FROM TEAM , PLAYER WHERE PLAYER_ID =? AND TEAM.TEAM_NAME =?''',
                              (playerId, teamName)).fetchone()
    conn.close()
    return render_template("playerinfo.html", playerData=abc, logo=cursorLogo[0])


@app.route("/feedback/", methods=["GET", "POST"])
@login_required
def feedback():
    if 'logged_in' in session or 'admin' in session:

        if request.method == "POST":
            conn = sqlconnection()
            presentation = request.form.get("presentation", None)
            idea = request.form.get("idea", None)
            objective = request.form.get("objective", None)
            suggestion = request.form.get("review", None) if request.form.get("review",
                                                                              None).strip() != "" else "No Suggestions"

            b = {"Excellent": 100, "Good": 75, "Satisfactory": 50, "Bad": 25}
            presentation_count = b[presentation]
            idea_count = b[idea]
            objective_count = b[idea]

            conn.execute(
                '''INSERT  INTO  FEEDBACK(NAME, EMAIL, PRESENTATION, IDEA, OBJECTIVES, SUGGESTION, PRESENTATION_COUNT, IDEA_COUNT, OBJECTTIVES_COUNT)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                (request.form.get("name", None),
                 request.form.get("email", None),
                 presentation, idea, objective, suggestion,
                 presentation_count, idea_count, objective_count)
            )
            conn.commit()
            conn.close()
            sendmail(request.form.get("email", None))
            return redirect(url_for("teamInfo"))
        elif request.method == "GET":
            return render_template("feedback.html")
    else:
        flash("You need to login first")
        return redirect(url_for("login"))


@app.route("/showfeedBack/")
def showFeedback():
    if 'admin' in session:
        conn = sqlconnection()
        cursor = conn.execute("SELECT NAME,EMAIL,PRESENTATION,IDEA,OBJECTIVES,SUGGESTION FROM FEEDBACK")
        cursor1 = conn.execute(
            "SELECT sum(PRESENTATION_COUNT)/COUNT(*) AS pcount ,sum(IDEA_COUNT)/COUNT(*) AS icount ,sum(OBJECTTIVES_COUNT)/COUNT(*) AS ocount , count(*) AS Tcount FROM FEEDBACK").fetchone()
        list1 = []
        b1 = ["pcount", "icount", "ocount", "Tcount"]
        b = ["name", "email", "presentation", "idea", "objective", "review"]
        for line in cursor:
            list1.append(dict(zip(b, line)))
        conn.close()
        total = 0
        if len(list1) > 0:
            x = dict(zip(b1, cursor1))
            total = x["Tcount"]

            gauge = pygal.SolidGauge(
                half_pie=True, inner_radius=0.70,
                style=pygal.style.styles['default'](value_font_size=10))

            percent_formatter = lambda x: '{:.10g}%'.format(x)
            gauge.value_formatter = percent_formatter

            gauge.add('Presentation', [{'value': x["pcount"], 'max_value': 100}])
            gauge.add('Idea', [{'value': x['icount'], 'max_value': 100}])
            gauge.add('Objective', [{'value': x['ocount'], 'max_value': 100}])

            graph_data = gauge.render_data_uri()
        else:
            graph_data = "No Feedback in database"
        return render_template("feedbackshow.html", feedback=list1, stat=graph_data, stat1=total)
    else:
        return "Need Admin Login"


@app.errorhandler(404)
def handleerror(e):
    return render_template("error.html")


def sendmail(receviermail):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("aniketcr777@gmail.com", "aniketcr777")

    msg = "Thanks for your valuable feedback. \n" \
          "Warm regards \n" \
          "Football Database Management Team"
    server.sendmail("aniketcr777@gmail.com", receviermail, msg)
    server.quit()


@app.route("/matchFixture", methods=["GET", "POST"])
def matchFixture():
    deleteMatchRelated()
    conn = sqlconnection()
    count = conn.execute("SELECT count(*) FROM TEAM").fetchone()[0]
    if count == 0:
        return render_template("back.html")
    elif count % 2 == 0:
        # fetch all teamname
        team = conn.execute("SELECT TEAM_NAME FROM TEAM").fetchall()
        # create a list of teamname
        team1 = [y for x in team for y in x]
        # permutation of team in teamN
        list1 = list(itertools.permutations(team1, r=2))

        # date format
        c = datetime.date(2017, 11, 23)

        date1 = c.isoformat()
        # itearation of permutation

        conn.close()
        for x in list1:
            y = list(x)
            y.append(date1)
            conn1 = sqlconnection()
            conn1.execute("INSERT INTO MATCH_FIXTURE(TEAM1,TEAM2,MATCH_DATE) VALUES (?,?,?)",
                          tuple(y))
            conn1.commit()

            conn1.close()

        conn2 = sqlconnection()
        countTuple = conn2.execute("SELECT MATCH_ID FROM MATCH_FIXTURE").fetchall()
        count2 = [y for x in countTuple for y in x]
        conn2.close()
        location = {"Birminghan": "Old Trafford", "North London": "Stamford Bridge", "Everton": "Ainfield"}
        for x in count2:
            randomLocation = random.choice(list(location.keys()))
            conn3 = sqlconnection()
            conn3.execute("INSERT INTO MATCH_VENUE(MATCH_ID, LOCATION, STADIUM) VALUES (?,?,?)",
                          (x, randomLocation, location[randomLocation],))
            conn3.commit()
            conn3.close()

        conn4 = sqlconnection()
        cursor = conn4.execute(
            "SELECT MATCH_DATE , TEAM1 , TEAM2 , LOCATION , STADIUM   FROM MATCH_FIXTURE ,MATCH_VENUE WHERE MATCH_VENUE.MATCH_ID=MATCH_FIXTURE.MATCH_ID").fetchall()
        b = ["date", "team1", "team2", "location", "stadium"]
        list1 = []
        for x in cursor:
            list1.append(dict(zip(b, x)))
        conn4.close()
        return render_template("matchFixture.html", fixture=list1, date=list1[0]['date'])
    else:
        conn.close()
        return render_template("back.html")


def deleteMatchRelated():
    conn11 = sqlconnection()
    conn11.execute("DELETE FROM MATCH_VENUE")
    conn11.execute("DELETE FROM MATCH_FIXTURE ")
    conn11.commit()
    conn11.close()


@app.route("/topTeam")
def topTeam():
    conn111 = sqlconnection()
    count = conn111.execute("SELECT count(*) FROM TEAM").fetchone()[0]
    conn111.close()
    if count % 2 == 0:
        conn = sqlconnection()
        cursor = conn.execute(
            "SELECT PLAYER_NAME ,NUMBER_OF_GOALS  FROM PLAYER ORDER BY NUMBER_OF_GOALS DESC ").fetchall()
        b = ["playerName", "goals"]
        topPlayers = [dict(zip(b, line)) for line in cursor]
        conn.close()

        conn1 = sqlconnection()
        conn1.execute("DELETE FROM MATCH_RESULT")
        conn1.commit()
        conn1.close()

        conn2 = sqlconnection()
        team = conn2.execute("SELECT TEAM_NAME FROM TEAM").fetchall()
        # create a list of teamname
        team1 = [y for x in team for y in x]
        # permutation of team in teamN
        list1 = list(itertools.permutations(team1, r=2))

        conn2 = sqlconnection()
        countTuple = conn2.execute("SELECT MATCH_ID FROM MATCH_FIXTURE").fetchall()
        count2 = [y for x in countTuple for y in x]
        conn2.close()

        for i, x in enumerate(list1):
            list111 = list(x)
            random.shuffle(list111)
            list12 = count2[i]
            counnection = sqlconnection()
            counnection.execute("INSERT INTO MATCH_RESULT(MATCH_ID, WIN, LOSE) VALUES (?,?,?)",
                                (list12, list111[0], list111[1]))
            counnection.commit()
            counnection.close()
        conn122 = sqlconnection()
        cursor = conn122.execute("SELECT WIN,count(WIN) FROM MATCH_RESULT GROUP BY WIN ORDER BY count(WIN)DESC")
        b = ["win", "count"]
        topTeam = [dict(zip(b, line)) for line in cursor]
        return render_template("topTeam.html", players=topPlayers, team=topTeam)
    else:
        return render_template("back.html")


@app.route("/matchResult")
def matchResult():
    conn = sqlconnection()
    cursor = conn.execute("SELECT WIN , LOSE FROM MATCH_RESULT")
    b = ["win", "lose"]
    list1 = [dict(zip(b, line)) for line in cursor]
    conn.close()
    return render_template("matchResult.html", result=list1)


@app.route("/query1")
def query1():
    conn = sqlconnection()
    cursor = conn.execute("SELECT PLAYER_NAME , JERSEY_NUMBER FROM PLAYER WHERE JERSEY_NUMBER=7").fetchall()
    conn.close()
    return render_template("demo1.html", cursor=cursor)


@app.route("/query2")
def query2():
    conn = sqlconnection()
    cursor = conn.execute("SELECT PLAYER_NAME , AGE , DATE_OF_BIRTH FROM PLAYER WHERE AGE BETWEEN 20 AND 30").fetchall()

    conn.close()
    return render_template("demo2.html", cursor=cursor)


@app.route("/query3")
def query3():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT DISTINCT (WIN)FROM MATCH_VENUE , MATCH_RESULT WHERE MATCH_VENUE.MATCH_ID=MATCH_RESULT.MATCH_ID AND STADIUM='Ainfield'").fetchall()

    conn.close()
    return render_template("demo3.html", cursor=cursor)


@app.route("/query4")
def query4():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT max(PLAYER_COST) , min(PLAYER_COST) , sum(PLAYER_COST) ,avg(PLAYER_COST) FROM PLAYER WHERE TEAM_NAME = 'Real Madrid' ").fetchall()

    conn.close()
    return render_template("demo4.html", cursor=cursor)


@app.route("/query5")
def query5():
    conn = sqlconnection()
    conn.execute("UPDATE PLAYER SET PLAYER_COST = ROUND(1.1* PLAYER_COST) WHERE NUMBER_OF_GOALS > 6")
    conn.commit()
    cursor = conn.execute(
        "SELECT PLAYER_NAME , NUMBER_OF_GOALS , PLAYER_COST FROM PLAYER WHERE NUMBER_OF_GOALS > 6").fetchall()
    conn.close()
    return render_template("demo5.html", cursor=cursor)


@app.route("/query6")
def query6():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT PLAYER_NAME ,NUMBER_OF_GOALS , PLAYER_POSITION FROM PLAYER WHERE NUMBER_OF_GOALS < 8 AND PLAYER_POSITION LIKE '%Centre half back%'").fetchall()
    conn.commit()
    conn.close()
    return render_template("demo6.html", cursor=cursor)


@app.route("/query7")
def query7():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT PLAYER_NAME , AGE FROM PLAYER WHERE AGE > 35 ").fetchall()
    conn.commit()
    conn.close()
    return render_template("demo7.html", cursor=cursor)


@app.route("/query8")
def query8():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT LOSE , COUNT(LOSE) FROM MATCH_RESULT GROUP BY LOSE HAVING COUNT(LOSE) > 3 ORDER BY LOSE DESC ").fetchall()
    conn.commit()
    conn.close()
    return render_template("demo8.html", cursor=cursor)


@app.route("/query9")
def query9():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT PLAYER_NAME  , PLAYER_POSITION FROM PLAYER WHERE PLAYER_POSITION LIKE '%keeper%'").fetchall()
    conn.commit()
    conn.close()
    return render_template("demo9.html", cursor=cursor)


@app.route("/query10")
def query10():
    conn = sqlconnection()
    cursor = conn.execute(
        '''SELECT TEAM.TEAM_NAME , PLAYER_NAME , PLAYER.COUNTRY FROM PLAYER , TEAM GROUP BY TEAM.COUNTRY HAVING TEAM.COUNTRY = PLAYER.COUNTRY ''').fetchall()
    conn.commit()
    conn.close()
    print(cursor)
    return render_template("demo10.html", cursor=cursor)


if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000)
