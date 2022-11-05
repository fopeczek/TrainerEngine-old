import PySimpleGUI as sg
import sqlite3
from random import randint
from datetime import datetime

con = None
cur = None
res = None


def load_last_session():
    teamplate = """SELECT SUM(correct) AS n_correct, COUNT(*) AS n_total FROM 'tries' WHERE time BETWEEN ? AND ?;"""


    data = (datetime(datetime.now().year, datetime.now().month, datetime.now().day), datetime.now())
    record=cur.execute(teamplate, data).fetchone()
    streak=0
    if (record[1]>0):
        streak=record[0]

    return streak


def save_record(value: int, question: str, correct: bool, think_time):
    teamplate = """INSERT INTO 'tries' ('question', 'answer', 'correct', 'thinking_time', 'time') VALUES (?, ?, ?, ?, ?);"""

    data = (question, value, correct, str(think_time).split(".")[0], datetime.now())
    cur.execute(teamplate, data)
    con.commit()


def make_question(first_range:tuple[int, int]=(1,20), second_range:tuple[int, int]=(1,1), do_neg=True) -> tuple[str, int]:
    num1 = randint(first_range[0], first_range[1])
    num2 = randint(second_range[0], second_range[1])
    is_neg = 0
    if (do_neg):
        is_neg = randint(0, 1)
    if is_neg == 1:
        num2 = -num2 #negate num
    if num2 > 0:
        question = f"{num1}+{num2}"
    else:
        question = f"{num1}{num2}" #no need to add - cuz the num is already with minus
    return question, num1 + num2


def make_quiz_window(target_trial_number):
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Text("Please wait", key="-TXT-"), sg.Input(size=(10, 1), key="-IN-", enable_events=True, focus=True),
               sg.Button('Submit', mouseover_colors=("white", "black"))],
              [sg.Push(), sg.ProgressBar(target_trial_number, orientation='h', size=(50, 20), key='-STREAK-'),
               sg.Push()],
              [sg.Push(), sg.Image(data=correct_incorrect[0]), sg.Push()]]

    window = sg.Window('Time to learn', layout, font=("Fira", 30), finalize=True)  # Part 3 - Window Defintion
    window['-IN-'].bind("<Return>", "_Enter")
    # window['-IN-'].bind("<Alt_L><o>", "_Settings")
    window.Element('-IN-').SetFocus()
    return window


# def make_settings_window():
#     sg.theme('Default')
#     layout = [[sg.Radio("Reset after mistake", "mistakes", default=True, key="-RESET-")],
#               [sg.Radio("Lose point after mistake", "mistakes", key="-LOSE-")]]
#
#     window = sg.Window('Settings', layout, font=("Fira", 30), finalize=True, force_toplevel=True)  # Part 3 - Window Defintion
#     return window


def allow_only_number(window, values):
    try:
        value = int(values['-IN-'])
    except:
        if not (len(values['-IN-']) == 1 and values['-IN-'][0] == '-'):
            window['-IN-'].update(values['-IN-'][:-1])
            return
    return int(value)


def init():
    global con
    global cur
    global res
    if con is None:
        con = sqlite3.connect("Sofi.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master")
    if (res.fetchone() is None):
        cur.execute(
            "CREATE TABLE tries(question TEXT, answer INTEGER, correct BOOL, thinking_time timestamp, time timestamp)")
    streak=load_last_session()
    main(20, streak)


def main(target_trial_number: int = 20, loaded_streak=0):
    window = make_quiz_window(target_trial_number)

    question, correct_answer = make_question()

    window['-TXT-'].update(f"{question}=")
    window['-IN-'].update("")
    window['-STREAK-'].update(loaded_streak)

    last_ans = datetime.now()
    answer_streak = loaded_streak

    if answer_streak >= target_trial_number:
        sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times in a row")
        return
        window.close()

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == "Exit":
            break
        elif event == '-IN-' and values['-IN-']:
            allow_only_number(window, values)
        elif (event == "-IN-" + "_Enter" or event == "Submit") and values['-IN-']:
            value = allow_only_number(window, values)

            think_time = datetime.now() - last_ans
            last_ans = datetime.now()

            correct = value == correct_answer
            if (correct):
                answer_streak += 1

                window['-STREAK-'].update(answer_streak)
                if answer_streak >= target_trial_number:
                    sg.popup(f"Good job, you have answered correctly {answer_streak} times in a row")
                    break
            else:
                answer_streak = 0
                window['-STREAK-'].update(answer_streak)

            save_record(value, question, correct, think_time)

            question, correct_answer = make_question()
            window["-TXT-"].update(f"{question}=")
            window['-IN-'].update(value="")
        # elif (event == "-IN-" + "_Settings"):
        #     settings=make_settings_window()


    # Finish up by removing from the screen
    window.close()


init()