import sqlite3, os


class Team:
    def __init__(self, teamName1):
        self.teamName = teamName1
        print(os.getcwd())
        self.conn = sqlite3.connect("football.db")

    def insert_team(self, teamLogo, country, squadpic, founded, homeground, teamcost, teamowner, sponser, teamcoach,
                    teamWebsite, about, operation):
        self.teamLogo = teamLogo
        self.country = country
        self.squadpic = squadpic
        self.founded = founded
        self.homeground = homeground
        self.teamcost = teamcost
        self.teamowner = teamowner
        self.sponser = sponser
        self.teamcoach = teamcoach
        self.teamWebsite = teamWebsite
        self.teamAbout = about

        if operation == "insert":
            self.conn.execute('PRAGMA FOREIGN_KEYS = ON ')

            self.conn.execute('''INSERT INTO TEAM(TEAM_NAME ,
                                                    TEAM_LOGO_URL ,
                                               SQUAD_PIC_URL ,
                                                  FOUNDED_ON    ,
                                                  HOMEGROUND    ,
                                                  TEAM_COST     ,
                                                  TEAM_WEBSITE  ,
                                                  TEAM_OWNER    ,
                                                  TEAM_COACH    ,
                                                  TEAM_SPONSER  ,
                                                  COUNTRY       ,
                                                  ABOUT)
                                                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (self.teamName,
                               self.teamLogo,
                               self.squadpic,
                               self.founded,
                               self.homeground,
                               self.teamcost,
                               self.teamWebsite,
                               self.teamowner,
                               self.teamcoach,
                               self.sponser,
                               self.country,
                               self.teamAbout))

            self.conn.commit()
            self.conn.close()
        elif operation == "update":
            self.conn.execute('PRAGMA FOREIGN_KEYS = ON ')

            self.conn.execute("""UPDATE TEAM SET
                                                TEAM_LOGO_URL=? ,
                                               SQUAD_PIC_URL=?,
                                                  FOUNDED_ON=?   ,
                                                  HOMEGROUND=? ,
                                                  TEAM_COST=?,
                                                  TEAM_WEBSITE=?  ,
                                                  TEAM_OWNER=?    ,
                                                  TEAM_COACH=?    ,
                                                  TEAM_SPONSER=?  ,
                                                  COUNTRY=?       ,
                                                  ABOUT=? WHERE TEAM_NAME=?""",
                              (self.teamLogo,
                               self.squadpic,
                               self.founded,
                               self.homeground,
                               self.teamcost,
                               self.teamWebsite,
                               self.teamowner,
                               self.teamcoach,
                               self.sponser,
                               self.country,
                               self.teamAbout, self.teamName))
            self.conn.commit()

            self.conn.close()

    def insertPlayer(self, playername, country, age, photo, dateofbirth, numberofgoals, playerposition, playercost,
                     jerseynum, about, operation, oldPlayerid):
        self.playerName = playername
        self.country = country
        self.age = eval(age)
        self.jersyNum = eval(jerseynum)
        self.photograph = photo
        self.cost = eval(playercost)
        self.playingPosition = playerposition
        self.dateOfBirth = dateofbirth
        self.numberofgoals = eval(numberofgoals)
        self.about = about

        if operation == "insert":
            self.conn.execute('PRAGMA FOREIGN_KEYS = ON ')
            self.conn.execute('''INSERT INTO PLAYER( 
                 TEAM_NAME,
                 PLAYER_NAME,
                 COUNTRY,
                 AGE,
                 PLAYER_PHOTOGRAPH_URL,
                 DATE_OF_BIRTH,
                 NUMBER_OF_GOALS,
                 PLAYER_POSITION,
                 PLAYER_COST,
                 JERSEY_NUMBER,
                 PLAYER_ABOUT) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                              (self.teamName,
                               self.playerName,
                               self.country,
                               self.age,
                               self.photograph,
                               self.dateOfBirth,
                               self.numberofgoals,
                               self.playingPosition,
                               self.cost,
                               self.jersyNum,
                               self.about
                               ))
            self.conn.commit()
            self.conn.close()
        elif operation == "update":
            self.conn.execute('PRAGMA FOREIGN_KEYS = ON ')
            self.conn.execute('''UPDATE PLAYER SET
 
                 PLAYER_NAME=?,
                 COUNTRY=?,
                 AGE=?,
                 PLAYER_PHOTOGRAPH_URL=?,
                 DATE_OF_BIRTH=?,
                 NUMBER_OF_GOALS=?,
                 PLAYER_POSITION=?,
                 PLAYER_COST=?,
                 JERSEY_NUMBER=?,
                 PLAYER_ABOUT=? WHERE PLAYER_ID =?''',
                              (
                                  self.playerName,
                                  self.country,
                                  self.age,
                                  self.photograph,
                                  self.dateOfBirth,
                                  self.numberofgoals,
                                  self.playingPosition,
                                  self.cost,
                                  self.jersyNum,
                                  self.about,
                                  oldPlayerid
                              ))
            self.conn.commit()
            self.conn.close()
