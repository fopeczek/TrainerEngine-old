from typing import Tuple, Any

import PySimpleGUI as sg
import sqlite3
from random import randint
from datetime import datetime
from collections import namedtuple

con = None
cur = None
res = None

config_con = None
config_cur = None
config_res = None


# Utility

def clamp(min, max, value):
    if value > max:
        return max
    if value < min:
        return min
    return value


def allow_only_number(window, values, key):
    value = ""
    minus_ok = False
    if values[key][0] == '-':
        minus_ok = True
    for char in values[key]:
        if (
                char == "1" or char == "2" or char == "3" or char == "4" or char == "5" or char == "6" or char == "7" or char == "8" or char == "9" or char == "0" or (
                char == "-" and minus_ok)):
            if char == '-':
                minus_ok = False
            value += char
    window[key].update(value)
    if value:
        if not (len(value) == 1 and value[0] == "-"):
            return int(value)


def allow_no_space(window, values, key):
    value = ""
    for char in values[key]:
        if (char != " "):
            value += char

    window[key].update(value)
    return value


# SQLite userdata
def load_last_session_penalty() -> tuple[Any, Any]:
    template = """SELECT SUM(correct) AS good, SUM(1-correct) AS bad FROM tries WHERE time>?;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    record = cur.execute(template, data).fetchone()
    return record[0], record[1]


def load_last_session_streak() -> int:
    template = """SELECT count(*) 
    FROM tries 
    WHERE correct = 1 
    AND time > coalesce((SELECT time FROM tries WHERE correct = 0 ORDER BY time DESC LIMIT 1) , 0)
    AND time > ?"""

    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    record = cur.execute(template, data).fetchone()
    streak = 0
    if (record[0] > 0):
        streak = record[0]
    print(streak)
    return streak


def save_record(value: int, question: str, correct: bool, think_time):
    template = """INSERT INTO 'tries' ('question', 'answer', 'correct', 'thinking_time', 'time') VALUES (?, ?, ?, ?, ?);"""

    data = (question, value, correct, str(think_time).split(".")[0], datetime.now())
    cur.execute(template, data)
    con.commit()


# SQLite config
def load_config():
    config_res = config_cur.execute("SELECT username FROM settings")
    username = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT target_trial FROM settings")
    target_trial = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT point_penalty FROM settings")
    point_penalty = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT reset_mistake FROM settings")
    reset_mistake = config_res.fetchone()[0]

    config_res = config_cur.execute("SELECT min1 FROM settings")
    min1 = config_res.fetchone()[0]

    config_res = config_cur.execute("SELECT max1 FROM settings")
    max1 = config_res.fetchone()[0]

    config_res = config_cur.execute("SELECT min2 FROM settings")
    min2 = config_res.fetchone()[0]

    config_res = config_cur.execute("SELECT max2 FROM settings")
    max2 = config_res.fetchone()[0]

    config_res = config_cur.execute("SELECT do_neg FROM settings")
    do_neg = config_res.fetchone()[0]

    template = namedtuple('template', 'username target_trial reset_mistake point_penalty min1 max1 min2 max2 do_neg')
    return template(username, target_trial, reset_mistake, point_penalty, min1, max1, min2, max2, do_neg)


def make_settings_table():
    config_cur.execute(
        "CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER, "
        "min1 INTEGER, max1 INTEGER, min2 INTEGER, max2 INTEGER, do_neg BOOL)")


def save_config(username: str, target_trial: int, reset_mistake: bool, point_penalty: int,min1: int, max1: int,
                min2: int, max2: int, do_neg: bool):
    template = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty', 'min1', 
    'max1', 'min2', 'max2', 'do_neg') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?); """

    data = (username, target_trial, reset_mistake, point_penalty, min1, max1, min2, max2, do_neg)
    config_cur.execute(template, data)
    config_con.commit()


# Questioning
def make_question(first_range: tuple[int, int], second_range: tuple[int, int], do_neg) -> tuple[
    str, int]:
    num1 = randint(first_range[0], first_range[1])
    num2 = randint(second_range[0], second_range[1])
    is_neg = 0
    if (do_neg):
        is_neg = randint(0, 1)
    if is_neg == 1:
        num2 = -num2  # negate num
    if num2 > 0:
        question = f"{num1}+{num2}"
    else:
        question = f"{num1}{num2}"  # no need to add - cuz the num is already with minus
    return question, num1 + num2


def make_quiz_window(target_trial_number):
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Text("Please wait", key="-TXT-"), sg.Text("", visible=False, key="-PREVIEW-"),
               sg.Input(size=(15, 1), key="-IN-", enable_events=True, focus=True)],
              [sg.Push(), sg.ProgressBar(target_trial_number, orientation='h', size=(50, 20), key='-STREAK-'),
               sg.Push()],
              [sg.Button('< Prev', enable_events=True, key='PREV', mouseover_colors=("white", "black")), sg.Push(),
               sg.Button('Settings', enable_events=True, key='SETTINGS', mouseover_colors=("white", "black")),
               sg.Push(),
               sg.Button('Next >', enable_events=True, key='NEXT', mouseover_colors=("white", "black"))]]

    window = sg.Window('Time to learn', layout, font=("Fira", 30), finalize=True)  # Part 3 - Window Defintion
    window['-IN-'].bind("<Return>", "_Enter")

    window.Element('-IN-').SetFocus()
    return window


# Config
def make_settings_window():
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Text("Please wait", key="-TXTUSR-"), sg.Input("", key='-USER-', size=(15, 1), enable_events=True)],
              [sg.Text("Please wait", key="-TXTTARGET-"),
               sg.Input("", key="-TARGET-", size=(15, 1), enable_events=True)],
              [sg.Checkbox("", default=False, key="-RESET-", enable_events=True),
               sg.Text("Reset after mistake", key="-TXTRESET-")],
              [sg.Text("Please wait", key="-TXTPENALTY-"), sg.Input("", key="-PENALTY-", enable_events=True)],
              [sg.Text("Please wait", key="-TXTNUM1-"), sg.Text("Please wait", key="-TXTMAX1-"),
               sg.Input("", key="-MAX1-", size=(15, 1), enable_events=True),
               sg.Text("Please wait", key="-TXTMIN1-"), sg.Input("", key="-MIN1-", size=(15, 1), enable_events=True)],
              [sg.Text("Please wait", key="-TXTNUM2-"), sg.Text("Please wait", key="-TXTMAX2-"),
               sg.Input("", key="-MAX2-", size=(15, 1), enable_events=True),
               sg.Text("Please wait", key="-TXTMIN2-"), sg.Input("", key="-MIN2-", size=(15, 1), enable_events=True)],
              [sg.Checkbox("", default=True, key="-NEG-", enable_events=True),
               sg.Text("Do negation?", key="-TXTNEG-")],
              [sg.Button("Done", key="DONE", mouseover_colors=("white", "black"), enable_events=True)]]

    window = sg.Window('Settings', layout, font=("Fira", 30), finalize=True, force_toplevel=True)
    window['-USER-'].bind("<Return>", "_Enter")
    window['-TARGET-'].bind("<Return>", "_Enter")
    window['-PENALTY-'].bind("<Return>", "_Enter")
    window['-MAX1-'].bind("<Return>", "_Enter")
    window['-MAX2-'].bind("<Return>", "_Enter")
    window['-MIN1-'].bind("<Return>", "_Enter")
    window['-MIN2-'].bind("<Return>", "_Enter")

    window.Element('-USER-').SetFocus()
    return window


# Text filters


def init():
    global config_con
    global config_cur
    global config_res
    if config_con is None:
        config_con = sqlite3.connect("config.db")
    config_cur = config_con.cursor()

    try:
        config_res = config_cur.execute("SELECT username FROM settings")
        if (config_res.fetchone()[0] is None):
            config_res.execute("DROP TABLE settings")
            settings_main(True)
    except:
        try:
            config_res.execute("DROP TABLE settings")
        except:
            config_res  # Ignore
        settings_main(True)

    config_res = config_cur.execute("SELECT username FROM settings")
    username = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT target_trial FROM settings")
    target_trial = config_res.fetchone()[0]

    if username != "" and target_trial is not None:
        global con
        global cur
        global res
        if con is None:
            con = sqlite3.connect(f"{username}.db")
        cur = con.cursor()
        try:
            res = cur.execute("SELECT question FROM tries")
        except:
            cur.execute(
                "CREATE TABLE tries(question TEXT, answer INTEGER, correct BOOL, thinking_time timestamp, time timestamp)")
        quiz_main(target_trial)


# Mains
def settings_main(is_init: bool):
    window = make_settings_window()
    window['-TXTTARGET-'].update("Target points")
    window['-TXTPENALTY-'].update("Point penalty")
    window['-TXTUSR-'].update("Username")
    window['-TXTNUM1-'].update("Range num 1:")
    window['-TXTMAX1-'].update("Max:")
    window['-TXTMIN1-'].update("Min:")
    window['-TXTNUM2-'].update("Range num 2:")
    window['-TXTMAX2-'].update("Max:")
    window['-TXTMIN2-'].update("Min:")

    if is_init:
        make_settings_table()

        window['-TARGET-'].update("20")
        window['-RESET-'].update(False)
        window['-PENALTY-'].update("2")
        window['-USER-'].update("")
        window['-MAX1-'].update(40)
        window['-MIN1-'].update(10)
        window['-MAX2-'].update(4)
        window['-MIN2-'].update(1)
        window['-NEG-'].update(True)
    else:
        username, target_trial, reset_mistake, point_penalty, max1, min1, max2, min2, do_neg = load_config()

        window['-TARGET-'].update(target_trial)
        window['-USER-'].update(username)
        window['-RESET-'].update(reset_mistake)
        window['-PENALTY-'].update(point_penalty)

        if reset_mistake:
            window["-TXTPENALTY-"].update(visible=False)
            window["-PENALTY-"].update(visible=False)
        else:
            window["-TXTPENALTY-"].update(visible=True)
            window["-PENALTY-"].update(visible=True)

        window['-MIN1-'].update(min1)
        window['-MAX1-'].update(max1)
        window['-MIN2-'].update(min2)
        window['-MAX2-'].update(max2)
        window['-NEG-'].update(do_neg)

        config_res.execute("DROP TABLE settings")
        make_settings_table()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break

        elif event == '-TARGET-' and values['-TARGET-']:
            allow_only_number(window, values, '-TARGET-')

        elif event == '-PENALTY-' and values['-PENALTY-']:
            allow_only_number(window, values, '-PENALTY-')

        elif event == '-MIN1-' and values['-MIN1-']:
            allow_only_number(window, values, '-MIN1-')

        elif event == '-MAX1-' and values['-MAX1-']:
            allow_only_number(window, values, '-MAX1-')

        elif event == '-MIN2-' and values['-MIN2-']:
            allow_only_number(window, values, '-MIN2-')

        elif event == '-MAX2-' and values['-MAX2-']:
            allow_only_number(window, values, '-MAX2-')

        elif event == '-USER-' and values['-USER-']:
            allow_no_space(window, values, '-USER-')

        elif event == '-RESET-':
            if values['-RESET-']:
                window["-TXTPENALTY-"].update(visible=False)
                window["-PENALTY-"].update(visible=False)
            else:
                window["-TXTPENALTY-"].update(visible=True)
                window["-PENALTY-"].update(visible=True)

        elif (event == "-USER-" + "_Enter" or event == "-TARGET-" + "_Enter" or event == "DONE") and values[
            '-USER-'] and values['-TARGET-'] and values['-MIN1-'] and values['-MAX1-'] and values['-MIN2-'] and values[
            '-MAX2-'] and ((not values['-RESET-'] and values['-PENALTY-']) or values['-RESET-']):

            save_config(values['-USER-'], values['-TARGET-'], values['-RESET-'], values['-PENALTY-'], values['-MIN1-'],
                        values['-MAX1-'], values['-MIN2-'], values['-MAX2-'], values['-NEG-'])

            break

    window.close()
    if (is_init == False):
        global con
        con = None

        global cur
        cur = None

        global res
        res = None
        init()


def quiz_main(target_trial_number):
    window = make_quiz_window(target_trial_number)
    loaded_config = load_config()

    if loaded_config.reset_mistake:
        loaded_streak = load_last_session_streak()
    else:
        good, bad = load_last_session_penalty()
        if good is not None and bad is not None:
            loaded_streak = good - bad * loaded_config.point_penalty
        else:
            loaded_streak = 0

    question, correct_answer = make_question((loaded_config.min1, loaded_config.max1),
                                             (loaded_config.min2, loaded_config.max2), loaded_config.do_neg)

    window['-TXT-'].update(f"{question}=")
    window['-IN-'].update("")
    window['-STREAK-'].update(loaded_streak)

    last_ans_time = datetime.now()
    answer_streak = loaded_streak

    last_question = None
    last_ans = None
    last_correct = None
    act_ans = None

    if answer_streak >= target_trial_number:
        sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times in a row")
        return
        window.close()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == '-IN-' and values['-IN-']:
            act_ans = allow_only_number(window, values, "-IN-")
        elif (event == "-IN-" + "_Enter" or event == "Submit") and values['-IN-']:
            value = allow_only_number(window, values, "-IN-")

            think_time = datetime.now() - last_ans_time
            last_ans_time = datetime.now()

            correct = value == correct_answer
            last_question = question
            last_ans = value
            last_correct = correct
            act_ans = None
            if correct:
                answer_streak += 1

                window['-STREAK-'].update(answer_streak)
                if answer_streak >= target_trial_number:
                    sg.popup(f"Good job, you have answered correctly {answer_streak} times in a row")
                    break
            else:
                if loaded_config.reset_mistake:
                    answer_streak = 0
                    window['-STREAK-'].update(answer_streak)
                else:
                    answer_streak -= loaded_config.point_penalty
                    if answer_streak < 0:
                        answer_streak = 0
                    window['-STREAK-'].update(answer_streak)

            save_record(value, question, correct, think_time)

            question, correct_answer = make_question((loaded_config.min1, loaded_config.max1),
                                                     (loaded_config.min2, loaded_config.max2), loaded_config.do_neg)
            window["-TXT-"].update(f"{question}=")
            window['-IN-'].update(value="")

        elif event == 'PREV' and last_question:
            window['-IN-'].update(visible=False)
            window['-PREVIEW-'].update(last_ans, visible=True)
            if last_correct:
                window['-TXT-'].update(f"{last_question}=")
            else:
                window['-TXT-'].update(f"{last_question}≠")
        elif event == 'NEXT' and not window['-IN-'].visible:
            window['-IN-'].update(act_ans, visible=True)
            window['-TXT-'].update(f"{question}=")
            window['-PREVIEW-'].update(visible=False)
        elif event == 'SETTINGS':
            window.close()
            settings_main(False)
            break

    window.close()

