from datetime import datetime
from contextlib import closing
from enum import Enum, auto
import sys

from .SQL_manager import connect_config_database, connect_user_database, Config_template, load_config, save_config, \
    load_last, save_last, load_last_record, save_record, load_record

from .window_manager import make_settings_window, update_options, WINDOW_CLOSED, make_quiz_window, popup_job_done, \
    show_preview, hide_preview

from .question_manager import make_question, score_anwser, default_percent_answer

admin_mode = False


class Regex_type(Enum):
    negative_number = auto()
    positive_number = auto()
    floating = auto()
    no_space = auto()


# Regex
def regex(window, values, key, type: Regex_type):
    out = ""

    if type == Regex_type.negative_number:
        minus = False
        if values[key][0] == '-':
            minus = True
    elif type == Regex_type.floating:
        dot = True

    for char in values[key]:
        if type == Regex_type.no_space:
            if char != ' ':
                out += char
        elif type == Regex_type.negative_number:
            if char.isdigit() or (char == "-" and minus):
                if char == '-':
                    minus = False

                out += char
        elif type == Regex_type.positive_number:
            if char.isdigit():
                out += char
        elif type == Regex_type.floating:
            if char.isdigit() or (char == '.' and dot):
                if char == '.':
                    dot = False

                out += char

    window[key].update(out)
    if out:
        if type == Regex_type.no_space:
            return out
        elif type == Regex_type.negative_number:
            if not (len(out) == 1 and out[0] == "-"):
                return int(out)
        elif type == Regex_type.positive_number:
            return int(out)
        elif type == Regex_type.floating:
            if not (len(out) == 1 and out[0] == '.'):
                return float(out)


# Init
def init():
    global admin_mode

    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        admin_mode = True
    else:
        admin_mode = False

    config_con = connect_config_database()

    try:
        config = load_config(config_con)
    except:
        config = settings_main(True, config_con, None)

    con = connect_user_database(config.username)

    quiz_main(con, config, config_con)


# Mains
def settings_main(is_init: bool, config_con, con):
    if is_init:
        config = Config_template("", 20, False, 2, False, 0.3, 0.8, 10, 40, 1, 4, True)
    else:
        config = load_config(config_con)

    window = make_settings_window(config)

    update_options(window, config)

    while True:
        event, values = window.read()
        if event == WINDOW_CLOSED:
            window.close()
            return

        elif event == '-TARGET-' and values['-TARGET-']:
            config.target_trial = regex(window, values, '-TARGET-', Regex_type.positive_number)

        elif event == '-PENALTY-' and values['-PENALTY-']:
            config.point_penalty = regex(window, values, '-PENALTY-', Regex_type.positive_number)

        elif event == '-OPTION1-' and values['-OPTION1-']:
            if config.percent:
                config.best_threshold = regex(window, values, '-OPTION1-', Regex_type.floating)
            else:
                config.min1 = regex(window, values, '-OPTION1-', Regex_type.positive_number)

        elif event == '-OPTION2-' and values['-OPTION2-']:
            config.max1 = regex(window, values, '-OPTION2-', Regex_type.positive_number)

        elif event == '-OPTION3-' and values['-OPTION3-']:
            if config.percent:
                config.good_threshold = regex(window, values, '-OPTION3-', Regex_type.floating)
            else:
                config.min2 = regex(window, values, '-OPTION3-', Regex_type.positive_number)

        elif event == '-OPTION4-' and values['-OPTION4-']:
            config.max2 = regex(window, values, '-OPTION4-', Regex_type.positive_number)

        elif event == '-USER-' and values['-USER-']:
            config.username = regex(window, values, '-USER-', Regex_type.no_space)

        elif event == '-RESET-':
            config.reset_mistake = values['-RESET-']
            update_options(window, config)

        elif event == '-PERCENT-':
            config.percent = values['-PERCENT-']
            update_options(window, config)


        elif "_Enter" in event or event == "DONE":

            if values['-USER-'] and values['-TARGET-'] and (
                    (not values['-RESET-'] and values['-PENALTY-']) or values['-RESET-']):

                if values['-OPTION1-'] and values['-OPTION3-']:
                    if values["-PERCENT-"]:
                        save_config(config, config_con)
                        break

                    elif values['-OPTION2-'] and values['-OPTION4-'] and \
                            config.min1 <= config.max1 and config.min2 <= config.max2:
                        save_config(config, config_con)
                        break

    window.close()
    if not is_init:
        quiz_main(con, config, config_con)
    else:
        return config


def submit_user_input(window, con, config, record, last_ans_time):
    record.think_time = datetime.now() - last_ans_time
    last_ans_time = datetime.now()

    record.correct = score_anwser(config, record)

    if record.correct:
        record.points += 1

        window['-STREAK-'].update(record.points)
        if record.points >= config.target_trial:
            save_record(record, con)
            window.close()
            popup_job_done(record.points, config.target_trial)
            return [True, last_ans_time]
    else:
        if config.reset_mistake:
            record.points = 0
            window['-STREAK-'].update(record.points)
        else:
            record.points -= config.point_penalty
            if record.points < 0:
                record.points = 0
            window['-STREAK-'].update(record.points)

    save_record(record, con)

    points = record.points
    record = make_question(config)
    record.points = points

    window["-TXT-"].update(f"{record.question}=")
    if config.percent:
        window['-PERCENT-'].update(record.answer, visible=True)
    else:
        window['-IN-'].update(value="")
    return [False, record, last_ans_time]


def quiz_main(con, config: Config_template, config_con):
    window = make_quiz_window(config, admin_mode)

    last = load_last(con)
    if last is None:
        record = make_question(config)
    else:
        record = last
        if config.percent:
            if record.question[-1] != '%':
                record = make_question(config)
        else:
            if record.question[-1] == '%':
                record = make_question(config)

    if config.percent:
        window['-PERCENT-'].update(record.answer)
        window['-IN-'].update(visible=False)
    else:
        window['-IN-'].update(record.answer)
        window['-PERCENT-'].update(visible=False)

    window['-TXT-'].update(f"{record.question}=")

    safety_lock = True

    index = 0
    record.points, act_index = load_last_record(con)
    if record.points is None:
        record.points = 0
        act_index = index
    else:
        index = act_index

    window['-STREAK-'].update(record.points)

    last_ans_time = datetime.now()

    if record.points >= config.target_trial:
        window.close()
        popup_job_done(record.points, config.target_trial)
        return

    while True:
        event, values = window.read()
        if event == WINDOW_CLOSED:
            break
        elif event == '-PERCENT-':
            record.answer = values['-PERCENT-']
            safety_lock = True
        elif event == '-IN-' and values['-IN-']:
            record.answer = regex(window, values, "-IN-", Regex_type.negative_number)
        elif event == "-IN-" + "_Enter" and values['-IN-']:
            act_index += 1
            index = act_index

            stop, record, last_ans_time = submit_user_input(window, con, config, record, last_ans_time)
            if stop:
                break

        elif event == 'NEXT':
            index += 1
            if config.percent and index > act_index:  # Submit answer
                if record.answer == default_percent_answer and safety_lock:  # Safety lock
                    safety_lock = False

                    index = act_index

                    continue
                else:
                    safety_lock = True

                    act_index += 1
                    index = act_index

                    stop, record, last_ans_time = submit_user_input(window, con, config, record, last_ans_time)
                    if stop:
                        break

                    continue
            elif not config.percent and index > act_index:
                index = act_index

            if index == act_index:  # Load act record
                hide_preview(window, config, record)
            else:
                loaded_record = load_record(con, index)
                show_preview(window, loaded_record)

            safety_lock = True

        elif event == 'PREV':
            index -= 1
            if index < 0:
                index = 0
                continue
            if index < act_index:
                loaded_record = load_record(con, index)
                show_preview(window, loaded_record)

            safety_lock = True

        elif event == 'END':
            index = act_index
            hide_preview(window, config, record)

            safety_lock = True

        elif event == 'HOME':
            index = 0
            if index < act_index:
                loaded_record = load_record(con, index)
                show_preview(window, loaded_record)

            safety_lock = True

        elif event == 'SETTINGS':
            save_last(record, con)
            window.close()
            settings_main(False, config_con, con)
            break

    save_last(record, con)

    window.close()
