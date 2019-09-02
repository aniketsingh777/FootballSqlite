import sqlite3, datetime, random, itertools
import tabulate
from prettytable import PrettyTable

def sqlconnection():
    conn = sqlite3.connect("football.db")
    return conn

def query10():
    conn = sqlconnection()
    cursor = conn.execute(
        "SELECT P.PLAYER_NAME , P.COUNTRY FROM PLAYER P , TEAM T WHERE P.COUNTRY = T.COUNTRY ").fetchall()
    conn.commit()
    conn.close()
    print(cursor)


if __name__ == '__main__':
    query10()