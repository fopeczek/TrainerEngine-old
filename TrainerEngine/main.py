from datetime import datetime
import SQL_manager as sql
import window_manager as gui
import question_manager as quiz

admin_mode = True


# Regex
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


# Init
def init():
    config_con, config_cur = sql.connect_config_database()
    sql.check_version(config_con, True)

    try:
        config_res = config_cur.execute("SELECT * FROM settings")
    except:
        sql.make_settings_table(config_con, True)
        settings_main(True, config_con)

    try:
        config_res = config_cur.execute("SELECT username FROM settings")
        username = config_res.fetchone()[0]
        if username is None:
            settings_main(True, config_con)
    except:
        settings_main(True, config_con)

    config_res = config_cur.execute("SELECT username FROM settings")
    username = config_res.fetchone()[0]
    config_res = config_cur.execute("SELECT target_trial FROM settings")
    target_trial = config_res.fetchone()[0]

    if username != "" and target_trial is not None:
        con, cur = sql.connect_user_database(username)
        sql.check_version(con, False)
        try:
            cur.execute("SELECT question FROM tries")
        except:
            sql.make_data_table(con)
        quiz_main(target_trial, con, config_con)


# Mains
def settings_main(is_init: bool, config_con):
    window = gui.make_settings_window()

    window['-TXTUSR-'].update("Username")

    window['-TXTTARGET-'].update("Target points")
    window['-TXTPENALTY-'].update("Point penalty")

    window['-TXTNUM1-'].update("Range num 1:")
    window['-TXTMAX1-'].update("Max:")
    window['-TXTMIN1-'].update("Min:")

    window['-TXTNUM2-'].update("Range num 2:")
    window['-TXTMAX2-'].update("Max:")
    window['-TXTMIN2-'].update("Min:")

    if is_init:
        window['-USER-'].update("")
        window['-TARGET-'].update("20")

        window['-RESET-'].update(False)
        window['-PENALTY-'].update("2")

        window['-PERCENT-'].update(False)

        window['-MIN1-'].update(10)
        MIN1 = 10
        window['-MAX1-'].update(40)
        MAX1 = 40

        window['-MIN2-'].update(1)
        MIN2 = 1
        window['-MAX2-'].update(4)
        MAX2 = 4

        window['-NEG-'].update(True)
    else:
        username, target_trial, reset_mistake, point_penalty, percent, min1, max1, min2, max2, do_neg = sql.load_config(
            config_con)

        window['-USER-'].update(username)
        window['-TARGET-'].update(target_trial)

        window['-RESET-'].update(reset_mistake)
        window['-PENALTY-'].update(point_penalty)

        window['-PERCENT-'].update(percent)

        if reset_mistake:
            window["-TXTPENALTY-"].update(visible=False)
            window["-PENALTY-"].update(visible=False)
        else:
            window["-TXTPENALTY-"].update(visible=True)
            window["-PENALTY-"].update(visible=True)

        if percent:
            window['-MIN1-'].update(min1, visible=False)
            MIN1 = min1
            window['-MAX1-'].update(max1, visible=False)
            MAX1 = max1

            window['-MIN2-'].update(min2, visible=False)
            MIN2 = min2
            window['-MAX2-'].update(max2, visible=False)
            MAX2 = max2

            window['-NEG-'].update(do_neg, visible=False)
            window['-TXTNEG-'].update(visible=False)

            window['-TXTNUM1-'].update(visible=False)
            window['-TXTMAX1-'].update(visible=False)
            window['-TXTMIN1-'].update(visible=False)

            window['-TXTNUM2-'].update(visible=False)
            window['-TXTMAX2-'].update(visible=False)
            window['-TXTMIN2-'].update(visible=False)
        else:
            window['-MIN1-'].update(min1)
            MIN1 = min1
            window['-MAX1-'].update(max1)
            MAX1 = max1

            window['-MIN2-'].update(min2)
            MIN2 = min2
            window['-MAX2-'].update(max2)
            MAX2 = max2

            window['-NEG-'].update(do_neg)

    while True:
        event, values = window.read()
        if event == gui.WINDOW_CLOSED:
            window.close()
            return

        elif event == '-TARGET-' and values['-TARGET-']:
            allow_only_number(window, values, '-TARGET-')

        elif event == '-PENALTY-' and values['-PENALTY-']:
            allow_only_number(window, values, '-PENALTY-')

        elif event == '-MIN1-' and values['-MIN1-']:
            MIN1 = allow_only_number(window, values, '-MIN1-')

        elif event == '-MAX1-' and values['-MAX1-']:
            MAX1 = allow_only_number(window, values, '-MAX1-')

        elif event == '-MIN2-' and values['-MIN2-']:
            MIN2 = allow_only_number(window, values, '-MIN2-')

        elif event == '-MAX2-' and values['-MAX2-']:
            MAX2 = allow_only_number(window, values, '-MAX2-')

        elif event == '-USER-' and values['-USER-']:
            allow_no_space(window, values, '-USER-')

        elif event == '-RESET-':
            if values['-RESET-']:
                window["-TXTPENALTY-"].update(visible=False)
                window["-PENALTY-"].update(visible=False)
            else:
                window["-TXTPENALTY-"].update(visible=True)
                window["-PENALTY-"].update(visible=True)

        elif event == '-PERCENT-':
            if values['-PERCENT-']:
                window['-MIN1-'].update(visible=False)
                window['-MAX1-'].update(visible=False)
                window['-MIN2-'].update(visible=False)
                window['-MAX2-'].update(visible=False)
                window['-NEG-'].update(visible=False)
                window['-TXTNEG-'].update(visible=False)

                window['-TXTNUM1-'].update(visible=False)
                window['-TXTMAX1-'].update(visible=False)
                window['-TXTMIN1-'].update(visible=False)

                window['-TXTNUM2-'].update(visible=False)
                window['-TXTMAX2-'].update(visible=False)
                window['-TXTMIN2-'].update(visible=False)
            else:
                window['-TXTNUM1-'].update(visible=True)

                window['-TXTMIN1-'].update(visible=True)
                window['-MIN1-'].update(visible=True)

                window['-TXTMAX1-'].update(visible=True)
                window['-MAX1-'].update(visible=True)


                window['-TXTNUM2-'].update(visible=True)

                window['-TXTMIN2-'].update(visible=True)
                window['-MIN2-'].update(visible=True)

                window['-TXTMAX2-'].update(visible=True)
                window['-MAX2-'].update(visible=True)


                window['-NEG-'].update(visible=True)
                window['-TXTNEG-'].update(visible=True)


        elif (event == "-USER-" + "_Enter" or event == "-TARGET-" + "_Enter" or event == "DONE") and values[
            '-USER-'] and values['-TARGET-'] and (values["-PERCENT-"] or (
                values['-MIN1-'] and values['-MAX1-'] and values['-MIN2-'] and values[
            '-MAX2-'] and MIN1 <= MAX1 and MIN2 <= MAX2 and (
                        (not values['-RESET-'] and values['-PENALTY-']) or values['-RESET-']))):

            sql.save_config(values['-USER-'], values['-TARGET-'], values['-RESET-'], values['-PENALTY-'],
                            values['-PERCENT-'], values['-MIN1-'],
                            values['-MAX1-'], values['-MIN2-'], values['-MAX2-'], values['-NEG-'], config_con)

            break

    window.close()
    if not is_init:
        init()


def quiz_main(target_trial_number, con, config_con):
    window = gui.make_quiz_window(target_trial_number, admin_mode)
    loaded_config = sql.load_config(config_con)

    loaded_last = sql.load_last(con)

    if loaded_last is None:
        question, correct_answer, answer = quiz.make_question(loaded_config)
    else:
        question, answer, correct_answer = loaded_last
        if loaded_config.percent:
            if int(question[:-1]) != correct_answer:
                question = quiz.make_percent_question()
                correct_answer = int(question[:-1])
                answer = "0%"

    if loaded_config.percent:
        safety_lock = True
        window['-IN-'].update(visible=False)
        window['-PERCENT-'].update(answer, visible=True)
    else:
        window['-IN-'].update(answer)

    window['-TXT-'].update(f"{question}=")
    answer_streak, act_index = sql.load_last_session(con)
    if answer_streak is None:
        answer_streak = 0
    window['-STREAK-'].update(answer_streak)

    last_ans_time = datetime.now()

    last_record_index = act_index - 1

    if answer_streak >= target_trial_number:
        gui.popup_job_done(answer_streak)
        return

    while True:
        event, values = window.read()
        if event == gui.WINDOW_CLOSED:
            break
        elif event == '-PERCENT-':
            answer = values['-PERCENT-']
        elif event == '-IN-' and values['-IN-']:
            allow_only_number(window, values, "-IN-")
        elif event == "-IN-" + "_Enter" and values['-IN-'] and not loaded_config.percent:
            answer = allow_only_number(window, values, "-IN-")

            think_time = datetime.now() - last_ans_time
            last_ans_time = datetime.now()

            correct = quiz.score_number(answer, correct_answer)

            if correct:
                answer_streak += 1

                window['-STREAK-'].update(answer_streak)
                if answer_streak >= target_trial_number:
                    gui.popup_job_done(answer_streak)
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

            sql.save_record(answer, correct_answer, question, correct, answer_streak, think_time, con)

            question, correct_answer, answer = quiz.make_question(loaded_config)

            last_record_index += 1
            act_index = last_record_index + 1

            window["-TXT-"].update(f"{question}=")
            window['-IN-'].update(value="")

        elif event == 'PREV':
            act_index -= 1
            if act_index >= 0:
                quest, correct, ans, correct_ans, points = sql.load_record(con, act_index)
                if quest[-1] == '%':
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()
                    window['-PREVIEW-'].update(f"{ans}%", visible=True)

                    window['-PERCENT_PREVIEW_CORRECT-'].update(correct_ans, visible=True)
                    window['-PERCENT_PREVIEW_USER-'].update(ans, visible=True)
                    window['-PERCENT-'].update(visible=False)

                    if correct_ans==ans:
                        window['-TXT-'].update(f"{quest}=")
                    else:
                        if correct:
                            window['-TXT-'].update(f"{quest}≈")
                        else:
                            window['-TXT-'].update(f"{quest}≠")
                else:
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()
                    window['-PREVIEW-'].update(ans, visible=True)
                    if correct:
                        window['-TXT-'].update(f"{quest}=")
                    else:
                        window['-TXT-'].update(f"{question}≠")
                window['-STREAK-'].update(points)
            else:
                act_index = 0

        elif event == 'NEXT':
            act_index += 1
            if loaded_config.percent:
                if act_index > last_record_index + 1:  # Submit answer
                    if answer == quiz.default_percent_answer and safety_lock:
                        safety_lock = False
                    else:
                        safety_lock = True

                        window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                        window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                        window['-PREVIEW-'].update(visible=False)
                        window['-IN-'].update(visible=False)

                        think_time = datetime.now() - last_ans_time
                        last_ans_time = datetime.now()
                        last_record_index += 1
                        act_index = last_record_index + 1
                        correct = quiz.score_percent(values['-PERCENT-'], correct_answer)

                        if values['-PERCENT-'] == correct_answer or correct:
                            answer_streak += 1

                            window['-STREAK-'].update(answer_streak)
                            if answer_streak >= target_trial_number:
                                sql.save_record(values['-PERCENT-'], correct_answer, question, correct, answer_streak, think_time, con)
                                gui.popup_job_done(answer_streak)
                                break
                            correct = True
                        else:
                            if loaded_config.reset_mistake:
                                answer_streak = 0
                                window['-STREAK-'].update(answer_streak)
                            else:
                                answer_streak -= loaded_config.point_penalty
                                if answer_streak < 0:
                                    answer_streak = 0
                                window['-STREAK-'].update(answer_streak)
                            correct = False

                        sql.save_record(values['-PERCENT-'], correct_answer, question, correct, answer_streak, think_time, con)
                        question, correct_answer, answer = quiz.make_question(loaded_config)
                        window['-TXT-'].update(f"{question}=")
                        window['-PERCENT-'].update(answer, visible=True)
                else:
                    window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
                    window['-PERCENT_PREVIEW_USER-'].update(visible=False)
                    window['-PREVIEW-'].update(visible=False)
                    window['-IN-'].update(visible=False)
                    window['-TXT-'].update(f"{question}=")
                    window['-PERCENT-'].update(visible=True)
            else:
                if act_index > last_record_index:
                    act_index = last_record_index + 1
                    window['-IN-'].update(visible=True)
                    window['-IN-'].set_focus()
                    window['-TXT-'].update(f"{question}=")
                    window['-PREVIEW-'].update(visible=False)
                    window['-STREAK-'].update(answer_streak)

            if act_index <= last_record_index:
                quest, correct, ans, correct_ans, points = sql.load_record(con, act_index)

                if quest[-1] == '%':
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()
                    window['-PREVIEW-'].update(f"{ans}%", visible=True)

                    window['-PERCENT_PREVIEW_CORRECT-'].update(correct_ans, visible=True)
                    window['-PERCENT_PREVIEW_USER-'].update(ans, visible=True)
                    window['-PERCENT-'].update(visible=False)

                    if correct_ans==ans:
                        window['-TXT-'].update(f"{quest}=")
                    else:
                        if correct:
                            window['-TXT-'].update(f"{quest}≈")
                        else:
                            window['-TXT-'].update(f"{quest}≠")
                else:
                    window['-PREVIEW-'].update(ans, visible=True)
                    window['-IN-'].update(visible=False)
                    window['-IN-'].block_focus()
                    if correct:
                        window['-TXT-'].update(f"{quest}=")
                    else:
                        window['-TXT-'].update(f"{quest}≠")

                window['-STREAK-'].update(points)

        elif event == 'SETTINGS':
            window.close()
            settings_main(False, config_con)
            break

    sql.save_last(answer, question, correct_answer, con)

    window.close()


init()
