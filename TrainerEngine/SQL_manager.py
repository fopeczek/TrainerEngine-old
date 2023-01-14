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
    if username == "":
        raise Exception("Error: username is empty, probably corrupted config file")
    con = sqlite3.connect(f"{username}.db", timeout=10)
    initialize_user_database(con)
    return con


def initialize_user_database(con):
    with closing(con.cursor()) as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS tries(question TEXT, answer INTEGER, correct_answer INTEGER, correct BOOL, points INTEGER, thinking_time timestamp, time timestamp)""")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS last(question TEXT, answer INTEGER, correct_answer INTEGER, time timestamp)")
        cur.execute("CREATE TABLE IF NOT EXISTS versions(version TEXT)")

        existing_version = cur.execute("SELECT version FROM versions").fetchone()

        if existing_version is None:
            template = """INSERT INTO 'versions' ('version') VALUES (?);"""
            data = (data_version,)
            cur.execute(template, data)
        else:
            check_version(con, False)
    con.commit()


def load_last_record(con) -> tuple[int, int]:
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
        load = cur.execute(template, data).fetchall()
    if load is not None and len(load) > index:
        quest, correct, ans, correct_ans, points = load[index]
        out = Record_template(quest, ans, correct_ans, correct, points)
    return out


# Last question
def save_last(record: Record_template, con):
    with closing(con.cursor()) as cur:
        cur.execute("""DELETE FROM last;""")
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


# SQLite config
def connect_config_database():
    config_con = sqlite3.connect("config.db", timeout=10)
    initialize_config_database(config_con)
    return config_con


def initialize_config_database(config_con):
    with closing(config_con.cursor()) as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER, 
            percent BOOL, best_threshold INTEGER, good_threshold INTEGER, min1 INTEGER, max1 INTEGER, min2 INTEGER, max2 INTEGER, do_neg BOOL)""")
        cur.execute("CREATE TABLE IF NOT EXISTS versions(version INTEGER)")

        existing_version = cur.execute("SELECT version FROM versions").fetchone()

        if existing_version is None:
            template = """INSERT INTO 'versions' ('version') VALUES (?);"""
            data = (config_version,)
            cur.execute(template, data)
        else:
            check_version(config_con, True)
    config_con.commit()


def save_config(config: Config_template, config_con):
    with closing(config_con.cursor()) as cur:
        cur.execute("DELETE FROM settings")
    template = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty', 'percent', 'best_threshold', 'good_threshold', 'min1', 
    'max1', 'min2', 'max2', 'do_neg') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); """

    data = (config.username, config.target_trial, config.reset_mistake, config.point_penalty, config.percent,
            config.best_threshold, config.good_threshold, config.min1, config.max1, config.min2, config.max2,
            config.do_neg)
    with closing(config_con.cursor()) as cur:
        cur.execute(template, data)
    config_con.commit()


def load_config(config_con):
    try:
        with closing(config_con.cursor()) as cur:
            username = cur.execute("SELECT username FROM settings").fetchone()[0]
            if username == "":
                raise Exception("Error: Username value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            target_trial = cur.execute("SELECT target_trial FROM settings").fetchone()[0]
            if target_trial < 0:
                raise Exception("Error: Target trial value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            point_penalty = cur.execute("SELECT point_penalty FROM settings").fetchone()[0]
            if point_penalty < 0:
                raise Exception("Error: Point penalty value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            reset_mistake = cur.execute("SELECT reset_mistake FROM settings").fetchone()[0]

        with closing(config_con.cursor()) as cur:
            percent = cur.execute("SELECT percent FROM settings").fetchone()[0]

        with closing(config_con.cursor()) as cur:
            best_threshold = cur.execute("SELECT best_threshold FROM settings").fetchone()[0]
            if best_threshold < 0:
                raise Exception("Error: Best threshold value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            good_threshold = cur.execute("SELECT good_threshold FROM settings").fetchone()[0]
            if good_threshold < 0:
                raise Exception("Error: Good threshold value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            min1 = cur.execute("SELECT min1 FROM settings").fetchone()[0]
            if min1 < 0:
                raise Exception("Error: Min1 value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            max1 = cur.execute("SELECT max1 FROM settings").fetchone()[0]
            if max1 < 0:
                raise Exception("Error: Max1 value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            min2 = cur.execute("SELECT min2 FROM settings").fetchone()[0]
            if min2 < 0:
                raise Exception("Error: Min2 value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            max2 = cur.execute("SELECT max2 FROM settings").fetchone()[0]
            if max2 < 0:
                raise Exception("Error: Max2 value is corrupted, check config file")

        with closing(config_con.cursor()) as cur:
            do_neg = cur.execute("SELECT do_neg FROM settings").fetchone()[0]

        if min1 > max1:
            raise Exception("Error: Min1 is greater than Max1, check config file")
        if min2 > max2:
            raise Exception("Error: Min2 is greater than Max2, check config file")

    except:
        raise Exception("Error: configuration file is corrupted or not initialized")

    config = Config_template(username, target_trial, reset_mistake, point_penalty, percent, best_threshold,
                             good_threshold, min1, max1, min2, max2, do_neg)

    return config


# Versioning
def check_version(con, config: bool):
    global config_version
    global data_version

    try:
        with closing(con.cursor()) as cur:
            loaded_version = cur.execute("SELECT version FROM versions").fetchone()[0]
    except:
        if config:
            raise Exception("Error: Configuration version is corrupted or not initialized")
        else:
            raise Exception("Error: Database version is corrupted or not initialized")

    if config:
        if loaded_version != config_version:
            raise Exception(
                "Error: version missmatch! Your configuration file is outdated. Please delete it and restart the program.")
    else:
        if loaded_version != data_version:
            raise Exception(
                "Error: version missmatch! Your user data file is outdated. Please delete it and restart the program.")
