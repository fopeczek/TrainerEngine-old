import PySimpleGUI as sg
from .SQL_manager import Config_template

WINDOW_CLOSED = sg.WINDOW_CLOSED


# Window makers
def make_quiz_window(config: Config_template, admin_mode):
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Push(),
               sg.ProgressBar(100, orientation='h', size=(30, 20), visible=False, key='-PERCENT_PREVIEW_CORRECT-')],
              [sg.Text("", key="-TXT-"), sg.Text("", visible=False, key="-PREVIEW-"),
               sg.ProgressBar(100, orientation='h', size=(30, 20), visible=False, key='-PERCENT_PREVIEW_USER-'),
               sg.Input(size=(15, 1), key="-IN-", enable_events=True, visible=not config.percent),
               sg.Slider((0, 100), orientation='h', size=(15, 20), visible=config.percent, key='-PERCENT-',
                         enable_events=True, disable_number_display=True)],
              [sg.Push(), sg.ProgressBar(config.target_trial, orientation='h', size=(50, 20), key='-STREAK-'),
               sg.Push()],
              [sg.Button('<<', enable_events=True, key='HOME', mouseover_colors=("white", "black")), sg.Push(),
               sg.Button('<', visible=True, enable_events=True, key='PREV',
                         mouseover_colors=("white", "black")),
               sg.Button('Settings', visible=admin_mode, enable_events=True, key='SETTINGS',
                         mouseover_colors=("white", "black")),
               sg.Button('>', visible=True, enable_events=True, key='NEXT',
                         mouseover_colors=("white", "black")),
               sg.Push(),
               sg.Button('>>', enable_events=True, key='END', mouseover_colors=("white", "black"))]]

    window = sg.Window('Time to learn', layout, font=("Fira", 30), finalize=True)
    window['-IN-'].bind("<Return>", "_Enter")

    window.Element('-IN-').SetFocus()
    return window


# Config
def make_settings_window(config: Config_template):
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Text("Username", key="-TXT_USR-"), sg.Input("", key='-USER-', size=(15, 1), enable_events=True)],

              [sg.Text("Target points", key="-TXT_TARGET-"),
               sg.Input("", key="-TARGET-", size=(8, 1), enable_events=True)],

              [sg.Checkbox("", default=config.reset_mistake, key="-RESET-", enable_events=True),
               sg.Text("Reset after mistake", key="-TXT_RESET-")],

              [sg.Text("Point penalty", key="-TXT_PENALTY-", visible=not config.reset_mistake),
               sg.Input("", key="-PENALTY-", size=(8, 1), enable_events=True, visible=not config.reset_mistake)],

              [sg.Checkbox("", default=config.percent, key="-PERCENT-", enable_events=True),
               sg.Text("Do percent quiz", key="-TXT_PERCENT-")],

              [sg.Text("", key="-TXT_OPTION1-"),
               sg.Input("", key="-OPTION1-", size=(8, 1), enable_events=True),
               sg.Text("", key="-TXT_OPTION2-", visible=not config.percent),
               sg.Input("", key="-OPTION2-", size=(8, 1), enable_events=True, visible=not config.percent)],

              [sg.Text("", key="-TXT_OPTION3-"),
               sg.Input("", key="-OPTION3-", size=(8, 1), enable_events=True),
               sg.Text("", key="-TXT_OPTION4-", visible=not config.percent),
               sg.Input("", key="-OPTION4-", size=(8, 1), enable_events=True, visible=not config.percent)],

              [sg.Checkbox("", default=config.do_neg, key="-NEG-", enable_events=True, visible=not config.percent),
               sg.Text("Do negation?", key="-TXT_NEG-", visible=not config.percent)],

              [sg.Button("Done", key="DONE", mouseover_colors=("white", "black"), enable_events=True)]]

    window = sg.Window('Settings', layout, font=("Fira", 30), finalize=True, force_toplevel=True)
    window['-USER-'].bind("<Return>", "_Enter")
    window['-TARGET-'].bind("<Return>", "_Enter")
    window['-PENALTY-'].bind("<Return>", "_Enter")

    window['-OPTION1-'].bind("<Return>", "_Enter")
    window['-OPTION2-'].bind("<Return>", "_Enter")
    window['-OPTION3-'].bind("<Return>", "_Enter")
    window['-OPTION4-'].bind("<Return>", "_Enter")

    window.Element('-USER-').SetFocus()
    return window


def update_options(window, config: Config_template):
    window['-USER-'].update(config.username)
    window['-TARGET-'].update(config.target_trial)

    window['-RESET-'].update(config.reset_mistake)

    if config.reset_mistake:
        window["-TXT_PENALTY-"].update(visible=False)
        window["-PENALTY-"].update(config.point_penalty, visible=False)
    else:
        window["-TXT_PENALTY-"].update(visible=True)
        window["-PENALTY-"].update(config.point_penalty, visible=True)

    window['-PERCENT-'].update(config.percent)

    if config.percent:
        window['-TXT_OPTION1-'].update("Best accuracy threshold: ")
        window['-OPTION1-'].update(config.best_threshold)
        window['-TXT_OPTION2-'].update(visible=False)
        window['-OPTION2-'].update(visible=False)

        window['-TXT_OPTION3-'].update("Good accuracy threshold: ")
        window['-OPTION3-'].update(config.good_threshold)
        window['-TXT_OPTION4-'].update(visible=False)
        window['-OPTION4-'].update(visible=False)

        window['-NEG-'].update(visible=False)
        window['-TXT_NEG-'].update(visible=False)
    else:
        window['-TXT_OPTION1-'].update("Range num 1: Min: ")
        window['-OPTION1-'].update(config.min1)
        window['-TXT_OPTION2-'].update("Max: ", visible=True)
        window['-OPTION2-'].update(config.max1, visible=True)

        window['-TXT_OPTION3-'].update("Range num 2: Min: ")
        window['-OPTION3-'].update(config.min2)
        window['-TXT_OPTION4-'].update("Max: ", visible=True)
        window['-OPTION4-'].update(config.max2, visible=True)

        window['-NEG-'].update(config.do_neg, visible=True)
        window['-TXT_NEG-'].update(visible=True)


def hide_preview(window, config, record):
    if config.percent:
        window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
        window['-PERCENT_PREVIEW_USER-'].update(visible=False)
        window['-PREVIEW-'].update(visible=False)

        window['-IN-'].update(visible=False)

        window['-TXT-'].update(f"{record.question}=")
        window['-PERCENT-'].update(visible=True)
    else:
        window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
        window['-PERCENT_PREVIEW_USER-'].update(visible=False)
        window['-PREVIEW-'].update(visible=False)

        window['-PERCENT-'].update(visible=False)

        window['-TXT-'].update(f"{record.question}=")
        window['-IN-'].update(visible=True)

    window['-STREAK-'].update(record.points)


def show_preview(window, record):
    window['-IN-'].update(visible=False)
    window['-PERCENT-'].update(visible=False)
    window['-STREAK-'].update(record.points)

    if record.question[-1] == '%':  # Percent
        window['-PREVIEW-'].update(f"{record.answer}%", visible=True)
        window['-PERCENT_PREVIEW_CORRECT-'].update(record.correct_answer, visible=True)
        window['-PERCENT_PREVIEW_USER-'].update(record.answer, visible=True)

        if record.correct_answer == record.answer:
            window['-TXT-'].update(f"{record.question}=")
        else:
            if record.correct:
                window['-TXT-'].update(f"{record.question}≈")
            else:
                window['-TXT-'].update(f"{record.question}≠")
    else:  # Number
        window['-PERCENT_PREVIEW_CORRECT-'].update(visible=False)
        window['-PERCENT_PREVIEW_USER-'].update(visible=False)

        window['-PREVIEW-'].update(record.answer, visible=True)

        if record.correct:
            window['-TXT-'].update(f"{record.question}=")
        else:
            window['-TXT-'].update(f"{record.question}≠")


def popup_job_done(answer_streak, target_trial):
    sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times out of {target_trial}.", font=("Fira", 30), keep_on_top=True)
