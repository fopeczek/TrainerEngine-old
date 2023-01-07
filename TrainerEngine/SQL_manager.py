from datetime import datetime
from collections import namedtuple
import sqlite3

config_version = "2.0.0"
data_version = "4.0.0"


# SQLite userdata
def connect_user_database(username):
    con = sqlite3.connect(f"{username}.db")
    cur = con.cursor()
    return con, cur


def load_last_session(con) -> tuple[int, int]:
    template = """SELECT points FROM tries WHERE time>? ORDER BY time DESC LIMIT 1;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    cur = con.cursor()
    points = cur.execute(template, data).fetchone()
    if points is not None:
        points = points[0]

    template = """SELECT COUNT(*) AS amount FROM tries WHERE time>?;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    cur = con.cursor()
    index = cur.execute(template, data).fetchone()[0]
    return points, index


def save_record(answer: int, correct_answer: int, question: str, correct: int, points: int, think_time, con):
    template = """INSERT INTO 'tries' ('question', 'answer', 'correct_answer', 'correct', 'points', 'thinking_time', 'time') VALUES (?, ?, ?, ?, ?, ?, ?);"""

    data = (question, answer, correct_answer, correct, points, str(think_time).split(".")[0], datetime.now())
    cur = con.cursor()
    cur.execute(template, data)
    con.commit()


def load_record(con, index: int) -> tuple[str, int, int, int, int]:  # question, correction, answertion, pointion
    template = """SELECT question, correct, answer, correct_answer, points FROM tries WHERE time>? ORDER BY time ASC LIMIT ?;"""

    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day), index + 1)
    cur = con.cursor()
    out = cur.execute(template, data).fetchall()
    if out is not None:
        out = out[index]
    return out


def clear_last_table(con):
    cur = con.cursor()
    cur.execute("DELETE FROM last")
    con.commit()


def check_version(con, config: bool):
    cur = con.cursor()
    global config_version
    global data_version
    try:
        tmp = cur.execute("SELECT * FROM versions").fetchone()
    except:
        make_versions_table(con, config)
    try:
        loaded_version = cur.execute("SELECT version FROM versions").fetchone()[0]
    except:
        clear_versions_table(con, config)
    loaded_version = cur.execute("SELECT version FROM versions").fetchone()[0]
    if config:
        if loaded_version != config_version:
            raise Exception("Error: version missmatch! Remove your configuration file")
    else:
        if loaded_version != data_version:
            raise Exception("Error: version missmatch! Remove your user data file")


# SQLite last question
def save_last(value: int, question: str, correct_answer: int, con):
    clear_last_table(con)
    template = """INSERT INTO 'last' ('question', 'answer', 'correct_answer', 'time') VALUES (?, ?, ?, ?);"""

    data = (question, value, correct_answer, datetime.now())
    cur = con.cursor()
    cur.execute(template, data)
    con.commit()


def load_last(con) -> tuple[str, int, int] | None:
    cur = con.cursor()
    out = cur.execute("""SELECT question, answer, correct_answer FROM last;""").fetchone()
    return out


# SQLite config
def connect_config_database():
    con = sqlite3.connect("config.db")
    cur = con.cursor()
    return con, cur


def save_config(username: str, target_trial: int, reset_mistake: bool, point_penalty: int, percent: bool, min1: int,
                max1: int,
                min2: int, max2: int, do_neg: bool, con):
    cur = con.cursor()
    clear_settings(con)
    template = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty', 'percent', 'min1', 
    'max1', 'min2', 'max2', 'do_neg') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?); """

    data = (username, target_trial, reset_mistake, point_penalty, percent, min1, max1, min2, max2, do_neg)
    cur.execute(template, data)
    con.commit()


def load_config(con):
    cur = con.cursor()
    res = cur.execute("SELECT username FROM settings")
    username = res.fetchone()[0]
    res = cur.execute("SELECT target_trial FROM settings")
    target_trial = res.fetchone()[0]
    res = cur.execute("SELECT point_penalty FROM settings")
    point_penalty = res.fetchone()[0]
    res = cur.execute("SELECT reset_mistake FROM settings")
    reset_mistake = res.fetchone()[0]

    res = cur.execute("SELECT percent FROM settings")
    percent = res.fetchone()[0]

    res = cur.execute("SELECT min1 FROM settings")
    min1 = res.fetchone()[0]

    res = cur.execute("SELECT max1 FROM settings")
    max1 = res.fetchone()[0]

    res = cur.execute("SELECT min2 FROM settings")
    min2 = res.fetchone()[0]

    res = cur.execute("SELECT max2 FROM settings")
    max2 = res.fetchone()[0]

    res = cur.execute("SELECT do_neg FROM settings")
    do_neg = res.fetchone()[0]

    template = namedtuple('template',
                          'username target_trial reset_mistake point_penalty percent min1 max1 min2 max2 do_neg')
    return template(username, target_trial, reset_mistake, point_penalty, percent, min1, max1, min2, max2, do_neg)


def clear_settings(con):
    cur = con.cursor()
    cur.execute("DELETE FROM settings")
    con.commit()


def make_settings_table(con, commit: bool):
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER, percent BOOL, "
        "min1 INTEGER, max1 INTEGER, min2 INTEGER, max2 INTEGER, do_neg BOOL)")
    if commit:
        con.commit()


def clear_versions_table(con, config):
    cur = con.cursor()
    cur.execute("DELETE FROM versions")
    con.commit()


def make_versions_table(con, config):
    cur = con.cursor()
    cur.execute("CREATE TABLE versions(version INTEGER)")
    template = """INSERT INTO 'versions' ('version') VALUES (?);"""
    if config:
        data = (config_version,)
    else:
        data = (data_version,)
    cur.execute(template, data)
    con.commit()


def make_data_table(con):
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE tries(question TEXT, answer INTEGER, correct_answer INTEGER, correct INTEGER, points INTEGER, thinking_time timestamp, time timestamp)")
    con.commit()
    make_last_table(con)


def make_last_table(con):
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE last(question TEXT, answer INTEGER, correct_answer INTEGER, time timestamp)")
    con.commit()
