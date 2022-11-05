import PySimpleGUI as sg
import sqlite3
from random import randint
from datetime import datetime
import os

con = None
cur = None
res = None

config_con = None
config_cur = None
config_res = None


# SQLite userdata

def load_last_session_penalty() -> int:
    template = """SELECT SUM(correct) AS good, SUM(1-correct) AS bad FROM tries WHERE time>?;"""
    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day),)
    record = cur.execute(template, data).fetchone()
    return (record[0], record[1])


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
    return username, target_trial, reset_mistake, point_penalty


def save_config(username: str, target_trial: int, reset_mistake: bool, point_penalty: int):
    teamplate = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty') VALUES (?, ?, ?, ?);"""

    data = (username, target_trial, reset_mistake, point_penalty)
    config_cur.execute(teamplate, data)
    config_con.commit()


# Questioning
def make_question(first_range: tuple[int, int] = (1, 20), second_range: tuple[int, int] = (1, 1), do_neg=True) -> tuple[
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
    layout = [[sg.Text("Please wait", key="-TXTUSR-"), sg.Input("", key='-USER-', size=(15, 1), enable_events=True)],
              [sg.Text("Please wait", key="-TXTTARGET-"),
               sg.Input("", key="-TARGET-", size=(15, 1), enable_events=True)],
              [sg.Checkbox("", default=False, key="-RESET-", enable_events=True),
               sg.Text("Reset after mistake", key="-TXTRESET-")],
              [sg.Text("Please wait", key="-TXTPENALTY-"), sg.Input("", key="-PENALTY-", enable_events=True)],
              [sg.Button("Done", key="DONE", mouseover_colors=("white", "black"), enable_events=True)]]

    window = sg.Window('Settings', layout, font=("Fira", 30), finalize=True, force_toplevel=True)
    window['-USER-'].bind("<Return>", "_Enter")
    window['-TARGET-'].bind("<Return>", "_Enter")
    window['-PENALTY-'].bind("<Return>", "_Enter")

    window.Element('-USER-').SetFocus()
    return window


# Text filters
def allow_only_number(window, values, key):
    value = ""
    for char in values[key]:
        if (
                char == "1" or char == "2" or char == "3" or char == "4" or char == "5" or char == "6" or char == "7" or char == "8" or char == "9" or char == "0"):
            value += char
    window[key].update(value)
    if value:
        return int(value)


def allow_no_space(window, values, key):
    value = ""
    for char in values[key]:
        if (char != " "):
            value += char

    window[key].update(value)
    return value


def init():
    global config_con
    global config_cur
    global config_res
    if config_con is None:
        config_con = sqlite3.connect("config.db")
    config_cur = config_con.cursor()
    try:
        config_res = config_cur.execute("SELECT username FROM settings")
        if (config_res.fetchone() is None):
            settings_main(True)
    except:
        if (os.path.isfile("config.db")):
            try:
                config_res.execute("DROP TABLE settings")
                settings_main(True)
            except:
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

    if (is_init == True):
        config_cur.execute(
            "CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER)")

        window['-TARGET-'].update("20")
        window['-PENALTY-'].update("2")
        window['-USER-'].update("")
    else:
        username, target_trial, reset_mistake, point_penalty = load_config()

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
        config_res.execute("DROP TABLE settings")
        config_cur.execute(
            "CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER)")

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == '-TARGET-' and values['-TARGET-']:
            allow_only_number(window, values, '-TARGET-')
        elif event == '-PENALTY-' and values['-PENALTY-']:
            allow_only_number(window, values, '-PENALTY-')
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
            '-USER-'] and values['-TARGET-'] and ((not values['-RESET-'] and values['-PENALTY-']) or values['-RESET-']):
            save_config(values['-USER-'], values['-TARGET-'], values['-RESET-'], values['-PENALTY-'])
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


def quiz_main(target_trial_number: int = 20):
    window = make_quiz_window(target_trial_number)
    username, target_trial, reset_mistake, point_penalty = load_config()

    if reset_mistake:
        loaded_streak = load_last_session_streak()
    else:
        good, bad = load_last_session_penalty()
        if good is not None and bad is not None:
            loaded_streak = good - bad * point_penalty
        else:
            loaded_streak = 0

    question, correct_answer = make_question()

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
                if reset_mistake:
                    answer_streak = 0
                    window['-STREAK-'].update(answer_streak)
                else:
                    answer_streak -= point_penalty
                    window['-STREAK-'].update(answer_streak)

            save_record(value, question, correct, think_time)

            question, correct_answer = make_question()
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


# Initialization
init()
