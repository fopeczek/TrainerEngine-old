from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import closing
import sqlite3
from typing import Optional

config_version = "4.0.0"
data_version = "4.0.0"


@dataclass
class Config_template:
    username: str
    target_trial: int
    reset_mistake: bool
    point_penalty: int
    percent: bool
    best_threshold: float
    good_threshold: float
    min1: int
    max1: int
    min2: int
    max2: int
    do_neg: bool


@dataclass
class Record_template:
    question: str
    answer: int
    correct_answer: int
    correct: Optional[bool] = None
    points: int = 0
    thinking_time: Optional[timedelta] = None
    time: Optional[datetime] = None


# SQLite userdata
def connect_user_database(username):
    con = sqlite3.connect(f"{username}.db", timeout=10)
    return con


def load_last_session(con) -> tuple[int, int]:
    template = """SELECT points FROM tries WHERE time>? ORDER BY time DESC LIMIT 1;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    with closing(con.cursor()) as cur:
        points = cur.execute(template, data).fetchone()
    if points is not None:
        points = points[0]

    template = """SELECT COUNT(*) AS amount FROM tries WHERE time>?;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    with closing(con.cursor()) as cur:
        index = cur.execute(template, data).fetchone()[0]
    return points, index


def save_record(record: Record_template, con):
    template = """INSERT INTO 'tries' ('question', 'answer', 'correct_answer', 'correct', 'points', 'thinking_time', 'time') VALUES (?, ?, ?, ?, ?, ?, ?);"""

    data = (record.question, record.answer, record.correct_answer, record.correct, record.points,
            str(record.thinking_time).split(".")[0], datetime.now())
    with closing(con.cursor()) as cur:
        cur.execute(template, data)
    con.commit()


def load_record(con, index: int) -> Record_template:  # question, correction, answertion, pointion
    template = """SELECT question, correct, answer, correct_answer, points FROM tries WHERE time>? ORDER BY time ASC LIMIT ?;"""

    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day), index + 1)
    with closing(con.cursor()) as cur:
        out = cur.execute(template, data).fetchall()
    if out is not None:
        quest, correct, ans, correct_ans, points = out[index]
        out = Record_template(quest, ans, correct_ans, correct, points)
    return out


def make_data_table(con):
    with closing(con.cursor()) as cur:
        cur.execute(
            "CREATE TABLE tries(question TEXT, answer INTEGER, correct_answer INTEGER, correct BOOL, points INTEGER, thinking_time timestamp, time timestamp)")
    con.commit()
    make_last_table(con)


# SQLite last question
def save_last(record: Record_template, con):
    clear_last_table(con)
    template = """INSERT INTO 'last' ('question', 'answer', 'correct_answer', 'time') VALUES (?, ?, ?, ?);"""

    data = (record.question, record.answer, record.correct_answer, datetime.now())
    with closing(con.cursor()) as cur:
        cur.execute(template, data)
    con.commit()


def load_last(con) -> Record_template | None:
    with closing(con.cursor()) as cur:
        out = cur.execute("""SELECT question, answer, correct_answer FROM last;""").fetchone()
    if out is None:
        return None
    quest, ans, correct_ans = out
    out = Record_template(quest, ans, correct_ans)
    return out


def clear_last_table(con):
    with closing(con.cursor()) as cur:
        cur.execute("DELETE FROM last")
    con.commit()


def make_last_table(con):
    with closing(con.cursor()) as cur:
        cur.execute(
            "CREATE TABLE last(question TEXT, answer INTEGER, correct_answer INTEGER, time timestamp)")
    con.commit()


# SQLite config
def connect_config_database():
    con = sqlite3.connect("config.db", timeout=10)
    return con


def save_config(config: Config_template, con):
    clear_settings(con)
    template = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty', 'percent', 'best_threshold', 'good_threshold', 'min1', 
    'max1', 'min2', 'max2', 'do_neg') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); """

    data = (config.username, config.target_trial, config.reset_mistake, config.point_penalty, config.percent,
            config.best_threshold, config.good_threshold, config.min1, config.max1, config.min2, config.max2,
            config.do_neg)
    with closing(con.cursor()) as cur:
        cur.execute(template, data)
    con.commit()


def load_config(con):
    with closing(con.cursor()) as cur:
        username = cur.execute("SELECT username FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        target_trial = cur.execute("SELECT target_trial FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        point_penalty = cur.execute("SELECT point_penalty FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        reset_mistake = cur.execute("SELECT reset_mistake FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        percent = cur.execute("SELECT percent FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        best_threshold = cur.execute("SELECT best_threshold FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        good_threshold = cur.execute("SELECT good_threshold FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        min1 = cur.execute("SELECT min1 FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        max1 = cur.execute("SELECT max1 FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        min2 = cur.execute("SELECT min2 FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        max2 = cur.execute("SELECT max2 FROM settings").fetchone()[0]

    with closing(con.cursor()) as cur:
        do_neg = cur.execute("SELECT do_neg FROM settings").fetchone()[0]

    return Config_template(username, target_trial, reset_mistake, point_penalty, percent, best_threshold,
                           good_threshold,
                           min1, max1, min2, max2, do_neg)


def clear_settings(con):
    with closing(con.cursor()) as cur:
        cur.execute("DELETE FROM settings")
    con.commit()


def make_settings_table(con):
    with closing(con.cursor()) as cur:
        cur.execute(
            """CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER, 
            percent BOOL, best_threshold INTEGER, good_threshold INTEGER, min1 INTEGER, max1 INTEGER, min2 INTEGER, max2 INTEGER, do_neg BOOL)""")
    con.commit()


# Versioning
def clear_versions_table(con):
    with closing(con.cursor()) as cur:
        cur.execute("DELETE FROM versions")
    con.commit()


def check_version(con, config: bool):
    global config_version
    global data_version
    try:
        with closing(con.cursor()) as cur:
            cur.execute("SELECT * FROM versions").fetchone()
    except:
        make_versions_table(con, config)
    try:
        with closing(con.cursor()) as cur:
            cur.execute("SELECT version FROM versions").fetchone()[0]
    except:
        clear_versions_table(con)
    with closing(con.cursor()) as cur:
        loaded_version = cur.execute("SELECT version FROM versions").fetchone()[0]
    if config:
        if loaded_version != config_version:
            raise Exception("Error: version missmatch! Remove your configuration file")
    else:
        if loaded_version != data_version:
            raise Exception("Error: version missmatch! Remove your user data file")


def make_versions_table(con, config):
    with closing(con.cursor()) as cur:
        cur.execute("CREATE TABLE versions(version INTEGER)")
    template = """INSERT INTO 'versions' ('version') VALUES (?);"""
    if config:
        data = (config_version,)
    else:
        data = (data_version,)
    with closing(con.cursor()) as cur:
        cur.execute(template, data)
    con.commit()
