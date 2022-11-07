import PySimpleGUI as sg
import sqlite3
from random import randint
from datetime import datetime
from collections import namedtuple

config_version = "1.0.0"
data_version = "2.0.0"

admin_mode = False


# Utility

def clamp(mini, maxi, value):
    if value > maxi:
        return maxi
    if value < mini:
        return mini
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


def save_record(value: int, question: str, correct: bool, points: int, think_time, con):
    template = """INSERT INTO 'tries' ('question', 'answer', 'correct', 'points', 'thinking_time', 'time') VALUES (?, ?, ?, ?, ?, ?);"""

    data = (question, value, correct, points, str(think_time).split(".")[0], datetime.now())
    cur = con.cursor()
    cur.execute(template, data)
    con.commit()


def load_record(con, index: int) -> tuple[str, bool, str, int]:  # question, correction, answertion, pointion
    template = """SELECT question, correct, answer, points FROM tries WHERE time>? ORDER BY time ASC LIMIT ?;"""

    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day), index + 1)
    cur = con.cursor()
    out = cur.execute(template, data).fetchall()
    if out is not None:
        out = out[index]
    return out


def save_config(username: str, target_trial: int, reset_mistake: bool, point_penalty: int, min1: int, max1: int,
                min2: int, max2: int, do_neg: bool, con):
    cur = con.cursor()
    template = """INSERT INTO 'settings' ('username', 'target_trial', 'reset_mistake', 'point_penalty', 'min1', 
    'max1', 'min2', 'max2', 'do_neg') VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?); """

    data = (username, target_trial, reset_mistake, point_penalty, min1, max1, min2, max2, do_neg)
    cur.execute(template, data)
    con.commit()


# SQLite config
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

    template = namedtuple('template', 'username target_trial reset_mistake point_penalty min1 max1 min2 max2 do_neg')
    return template(username, target_trial, reset_mistake, point_penalty, min1, max1, min2, max2, do_neg)


def clear_settings(con):
    cur = con.cursor()
    cur.execute("DROP TABLE settings")
    con.commit()
    make_settings_table(con)


def make_settings_table(con):
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE settings(username TEXT, target_trial INTEGER, reset_mistake BOOL, point_penalty INTEGER, "
        "min1 INTEGER, max1 INTEGER, min2 INTEGER, max2 INTEGER, do_neg BOOL)")
    con.commit()


def make_data_table(con):
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE tries(question TEXT, answer INTEGER, correct BOOL, points INTEGER, thinking_time timestamp, time timestamp)")
    con.commit()


def clear_versions_table(con, config):
    cur = con.cursor()
    cur.execute("DROP TABLE versions")
    con.commit()
    make_versions_table(con, config)


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
               sg.Button('Settings', visible=admin_mode, enable_events=True, key='SETTINGS', mouseover_colors=("white", "black")),
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
              [sg.Text("Please wait", key="-TXTNUM1-"), sg.Text("Please wait", key="-TXTMIN1-"),
               sg.Input("", key="-MIN1-", size=(15, 1), enable_events=True),
               sg.Text("Please wait", key="-TXTMAX1-"), sg.Input("", key="-MAX1-", size=(15, 1), enable_events=True)],
              [sg.Text("Please wait", key="-TXTNUM2-"), sg.Text("Please wait", key="-TXTMIN2-"),
               sg.Input("", key="-MIN2-", size=(15, 1), enable_events=True),
               sg.Text("Please wait", key="-TXTMAX2-"), sg.Input("", key="-MAX2-", size=(15, 1), enable_events=True)],
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


def init():
    config_con = sqlite3.connect("config.db")
    config_cur = config_con.cursor()

    check_version(config_con, True)

    try:
        config_res = config_cur.execute("SELECT * FROM settings")
    except:
        make_settings_table(config_con)
        settings_main(True, config_con)

    try:
        config_res = config_cur.execute("SELECT username FROM settings")
        username = config_res.fetchone()[0]
        if username is None:
            clear_settings(config_con)
            settings_main(True, config_con)
    except:
        clear_settings(config_con)
        settings_main(True, config_con)

    config_res = config_cur.execute("SELECT username FROM settings")
    username = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT target_trial FROM settings")
    target_trial = config_res.fetchone()[0]

    if username != "" and target_trial is not None:
        con = sqlite3.connect(f"{username}.db")
        cur = con.cursor()
        try:
            cur.execute("SELECT question FROM tries")
            check_version(con, False)
        except:
            make_data_table(con)
        quiz_main(target_trial, con, config_con)


# Mains
def settings_main(is_init: bool, config_con):
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
        username, target_trial, reset_mistake, point_penalty, min1, max1, min2, max2, do_neg = load_config(config_con)

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

        clear_settings(config_con)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            window.close()
            return

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
            '-MAX2-'] and values['-MAX1-'] > values['-MIN1-'] and values['-MAX2-'] > values['-MIN1-'] and (
                (not values['-RESET-'] and values['-PENALTY-']) or values['-RESET-']):

            save_config(values['-USER-'], values['-TARGET-'], values['-RESET-'], values['-PENALTY-'], values['-MIN1-'],
                        values['-MAX1-'], values['-MIN2-'], values['-MAX2-'], values['-NEG-'], config_con)

            break

    window.close()
    if not is_init:
        init()


def quiz_main(target_trial_number, con, config_con):
    window = make_quiz_window(target_trial_number)
    loaded_config = load_config(config_con)

    question, correct_answer = make_question((loaded_config.min1, loaded_config.max1),
                                             (loaded_config.min2, loaded_config.max2), loaded_config.do_neg)

    window['-TXT-'].update(f"{question}=")
    window['-IN-'].update("")
    answer_streak, act_index = load_last_session(con)
    if answer_streak is None:
        answer_streak = 0
    window['-STREAK-'].update(answer_streak)

    last_ans_time = datetime.now()

    act_question = question
    act_correct_answer = correct_answer
    act_answer = ""
    initial_index = act_index - 1

    if answer_streak >= target_trial_number:
        sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times in a row")
        return

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == '-IN-' and values['-IN-']:
            act_answer = allow_only_number(window, values, "-IN-")
        elif (event == "-IN-" + "_Enter" or event == "Submit") and values['-IN-']:
            value = allow_only_number(window, values, "-IN-")

            think_time = datetime.now() - last_ans_time
            last_ans_time = datetime.now()

            correct = value == correct_answer

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

            save_record(value, question, correct, answer_streak, think_time, con)

            question, correct_answer = make_question((loaded_config.min1, loaded_config.max1),
                                                     (loaded_config.min2, loaded_config.max2), loaded_config.do_neg)
            act_question = question
            act_answer = ""
            act_correct_answer = correct_answer
            initial_index = act_index - 1
            act_index += 1

            window["-TXT-"].update(f"{question}=")
            window['-IN-'].update(value="")

        elif event == 'PREV':
            act_index -= 1
            if act_index >= 0:
                question, correct, answer, points = load_record(con, act_index)
                window['-IN-'].update(visible=False)
                window['-PREVIEW-'].update(answer, visible=True)
                window['-STREAK-'].update(points)
                if correct:
                    window['-TXT-'].update(f"{question}=")
                else:
                    window['-TXT-'].update(f"{question}≠")
            else:
                act_index = 0

        elif event == 'NEXT':
            act_index += 1
            if act_index >= initial_index:
                act_index = initial_index
                question = act_question
                correct_answer = act_correct_answer
                window['-IN-'].update(act_answer, visible=True)
                window['-TXT-'].update(f"{act_question}=")
                window['-PREVIEW-'].update(visible=False)
                window['-STREAK-'].update(answer_streak)
            else:
                question, correct, answer, points = load_record(con, act_index)
                window['-IN-'].update(visible=False)
                window['-PREVIEW-'].update(answer, visible=True)
                window['-STREAK-'].update(points)
                if correct:
                    window['-TXT-'].update(f"{question}=")
                else:
                    window['-TXT-'].update(f"{question}≠")

        elif event == 'SETTINGS':
            window.close()
            settings_main(False, config_con)
            break

    window.close()


init()
