from datetime import datetime
# import SQL_manager as sql
from contextlib import closing
from enum import Enum, auto
# import window_manager as gui
# import question_manager as quiz
from .SQL_manager import connect_config_database, check_version, make_settings_table, connect_user_database, \
    make_data_table, Config_template, load_config, save_config, \
    load_last, load_last_session, save_record, load_record, save_last
from .window_manager import make_settings_window, update_options, WINDOW_CLOSED, make_quiz_window, popup_job_done
from .question_manager import make_question, score_number, default_percent_answer, score_percent

admin_mode = True


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
    #     if values[key][0] != ''

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
    config_con = connect_config_database()
    check_version(config_con, True)

    try:
        with closing(config_con.cursor()) as cur:
            cur.execute("SELECT * FROM settings")
    except:
        make_settings_table(config_con)
        settings_main(True, config_con)

    try:
        with closing(config_con.cursor()) as cur:
            username = cur.execute("SELECT username FROM settings").fetchone()[0]
        if username is None:
            settings_main(True, config_con)
    except:
        settings_main(True, config_con)

    with closing(config_con.cursor()) as cur:
        username = cur.execute("SELECT username FROM settings").fetchone()[0]
    with closing(config_con.cursor()) as cur:
        target_trial = cur.execute("SELECT target_trial FROM settings").fetchone()[0]

    if username != "" and target_trial is not None:
        con = connect_user_database(username)
        check_version(con, False)
        try:
            with closing(con.cursor()) as cur:
                cur.execute("SELECT question FROM tries")
        except:
            make_data_table(con)
        quiz_main(target_trial, con, config_con)


# Mains
def settings_main(is_init: bool, config_con):
    window = make_settings_window()

    if is_init:
        config = Config_template("", 20, False, 2, False, 0.3, 0.8, 10, 40, 1, 4, True)
    else:
        config = load_config(config_con)

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

                    elif values['-OPTION2-'] and values['-OPTION4-'] and \
                            config.min1 <= config.max1 and config.min2 <= config.max2:
                        save_config(config, config_con)

            break

    window.close()
    if not is_init:
        init()


def quiz_main(target_trial_number, con, config_con):
    window = make_quiz_window(target_trial_number, admin_mode)
    config = load_config(config_con)

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
        safety_lock = True
        window['-IN-'].update(visible=False)
        window['-PERCENT-'].update(record.answer, visible=True)
    else:
        window['-IN-'].update(record.answer)

    window['-TXT-'].update(f"{record.question}=")
    record.points, act_index = load_last_session(con)
    if record.points is None:
        record.points = 0
    window['-STREAK-'].update(record.points)

    last_ans_time = datetime.now()

    last_record_index = act_index - 1

    if record.points >= target_trial_number:
        popup_job_done(record.points)
        return

    while True:
        event, values = window.read()
        if event == WINDOW_CLOSED:
            break
        elif event == '-PERCENT-':
            record.answer = values['-PERCENT-']
        elif event == '-IN-' and values['-IN-']:
            record.answer = regex(window, values, "-IN-", Regex_type.negative_number)
        elif event == "-IN-" + "_Enter" and values['-IN-']:
            record.think_time = datetime.now() - last_ans_time
            last_ans_time = datetime.now()

            record.correct = score_number(record)

            if record.correct:
                record.points += 1

                window['-STREAK-'].update(record.points)
                if record.points >= target_trial_number:
                    popup_job_done(record.points)
                    break
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

            last_record_index += 1
            act_index = last_record_index + 1

            window["-TXT-"].update(f"{record.question}=")
            window['-IN-'].update(value="")

        elif event == 'PREV':
            act_index -= 1
            if act_index >= 0:
                loaded_record = load_record(con, act_index)

                if loaded_record.question[-1] == '%':
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()

                    window['-PREVIEW-'].update(f"{loaded_record.answer}%", visible=True)

                    window['-PERCENT_PREVIEW_CORRECT-'].update(loaded_record.correct_answer, visible=True)
                    window['-PERCENT_PREVIEW_USER-'].update(loaded_record.answer, visible=True)
                    window['-PERCENT-'].update(visible=False)

                    if loaded_record.correct_answer == loaded_record.answer:
                        window['-TXT-'].update(f"{loaded_record.question}=")
                    else:
                        if loaded_record.correct:
                            window['-TXT-'].update(f"{loaded_record.question}≈")
                        else:
                            window['-TXT-'].update(f"{loaded_record.question}≠")
                else:
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()

                    window['-PREVIEW-'].update(loaded_record.answer, visible=True)

                    window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                    window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                    window['-PERCENT-'].update(visible=False)

                    if loaded_record.correct:
                        window['-TXT-'].update(f"{loaded_record.question}=")
                    else:
                        window['-TXT-'].update(f"{loaded_record.question}≠")

                window['-STREAK-'].update(loaded_record.points)
            else:
                act_index = 0

        elif event == 'NEXT':
            act_index += 1
            if config.percent:
                if act_index > last_record_index + 1:  # Submit answer
                    if record.answer == default_percent_answer and safety_lock:
                        safety_lock = False
                    else:
                        safety_lock = True

                        window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                        window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                        window['-PREVIEW-'].update(visible=False)
                        window['-IN-'].update(visible=False)

                        record.think_time = datetime.now() - last_ans_time
                        last_ans_time = datetime.now()
                        record.answer = values['-PERCENT-']
                        last_record_index += 1
                        act_index = last_record_index + 1
                        record.correct = score_percent(record, config.good_threshold)

                        if values['-PERCENT-'] == record.correct_answer or record.correct:
                            record.points += 1

                            window['-STREAK-'].update(record.points)
                            if record.points >= target_trial_number:
                                save_record(record, con)
                                popup_job_done(record.points)
                                break
                            record.correct = True
                        else:
                            if config.reset_mistake:
                                record.points = 0
                                window['-STREAK-'].update(record.points)
                            else:
                                record.points -= config.point_penalty
                                if record.points < 0:
                                    record.points = 0
                                window['-STREAK-'].update(record.points)
                            record.correct = False

                        save_record(record, con)

                        points = record.points
                        record = make_question(config)
                        record.points = points

                        window['-TXT-'].update(f"{record.question}=")
                        window['-PERCENT-'].update(record.answer, visible=True)
                else:
                    window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                    window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                    window['-PREVIEW-'].update(visible=False)
                    window['-IN-'].update(visible=False)
                    window['-TXT-'].update(f"{record.question}=")
                    window['-PERCENT-'].update(visible=True)
            else:
                if act_index > last_record_index:
                    act_index = last_record_index + 1

                    window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                    window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                    window['-PERCENT-'].update(visible=False)

                    window['-PREVIEW-'].update(visible=False)

                    window['-TXT-'].update(f"{record.question}=")
                    window['-IN-'].update(visible=True)
                    window['-IN-'].set_focus()
                    window['-STREAK-'].update(record.points)

            if act_index <= last_record_index:
                loaded_record = load_record(con, act_index)

                if loaded_record.question[-1] == '%':
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()
                    window['-PREVIEW-'].update(f"{loaded_record.answer}%", visible=True)

                    window['-PERCENT_PREVIEW_CORRECT-'].update(loaded_record.correct_answer, visible=True)
                    window['-PERCENT_PREVIEW_USER-'].update(loaded_record.answer, visible=True)
                    window['-PERCENT-'].update(visible=False)

                    if loaded_record.correct_answer == loaded_record.answer:
                        window['-TXT-'].update(f"{loaded_record.question}=")
                    else:
                        if loaded_record.correct:
                            window['-TXT-'].update(f"{loaded_record.question}≈")
                        else:
                            window['-TXT-'].update(f"{loaded_record.question}≠")
                else:
                    window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                    window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                    window['-PERCENT-'].update(visible=False)

                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()

                    window['-PREVIEW-'].update(loaded_record.answer, visible=True)
                    if loaded_record.correct:
                        window['-TXT-'].update(f"{loaded_record.question}=")
                    else:
                        window['-TXT-'].update(f"{loaded_record.question}≠")

                window['-STREAK-'].update(loaded_record.points)

        elif event == 'SETTINGS':
            window.close()
            save_last(record, con)
            settings_main(False, config_con)
            break

    save_last(record, con)

    window.close()


init()
