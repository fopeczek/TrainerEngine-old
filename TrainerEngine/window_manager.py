import PySimpleGUI as sg
import SQL_manager as sql

WINDOW_CLOSED = sg.WINDOW_CLOSED


# Window makers
def make_quiz_window(target_trial_number, admin_mode):
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Push(),
               sg.ProgressBar(100, orientation='h', size=(30, 20), visible=False, key='-PERCENT_PREVIEW_CORRECT-')],
              [sg.Text("Please wait", key="-TXT-"), sg.Text("", visible=False, key="-PREVIEW-"),
               sg.ProgressBar(100, orientation='h', size=(30, 20), visible=False, key='-PERCENT_PREVIEW_USER-'),
               sg.Input(size=(15, 1), key="-IN-", enable_events=True, focus=True),
               sg.Slider((0, 100), orientation='h', size=(15, 20), visible=False, key='-PERCENT-',
                         disable_number_display=True, enable_events=True)],
              [sg.Push(), sg.ProgressBar(target_trial_number, orientation='h', size=(50, 20), key='-STREAK-'),
               sg.Push()],
              [sg.Button('< Prev', enable_events=True, key='PREV', mouseover_colors=("white", "black")), sg.Push(),
               sg.Button('Settings', visible=admin_mode, enable_events=True, key='SETTINGS',
                         mouseover_colors=("white", "black")),
               sg.Push(),
               sg.Button('Next >', enable_events=True, key='NEXT', mouseover_colors=("white", "black"))]]

    window = sg.Window('Time to learn', layout, font=("Fira", 30), finalize=True)
    window['-IN-'].bind("<Return>", "_Enter")

    window.Element('-IN-').SetFocus()
    return window


# Config
def make_settings_window():
    sg.theme('Black')
    sg.theme_button_color("white on black")
    layout = [[sg.Text("Username", key="-TXT_USR-"), sg.Input("", key='-USER-', size=(15, 1), enable_events=True)],

              [sg.Text("Target points", key="-TXT_TARGET-"),
               sg.Input("", key="-TARGET-", size=(8, 1), enable_events=True)],

              [sg.Checkbox("", default=False, key="-RESET-", enable_events=True),
               sg.Text("Reset after mistake", key="-TXT_RESET-")],

              [sg.Text("Point penalty", key="-TXT_PENALTY-"),
               sg.Input("", key="-PENALTY-", size=(8, 1), enable_events=True)],

              [sg.Checkbox("", default=False, key="-PERCENT-", enable_events=True),
               sg.Text("Do percent quiz", key="-TXT_PERCENT-")],

              [sg.Text("Please wait", key="-TXT_OPTION1-"),
               sg.Input("", key="-OPTION1-", size=(8, 1), enable_events=True),
               sg.Text("Please wait", key="-TXT_OPTION2-"),
               sg.Input("", key="-OPTION2-", size=(8, 1), enable_events=True)],

              [sg.Text("Please wait", key="-TXT_OPTION3-"),
               sg.Input("", key="-OPTION3-", size=(8, 1), enable_events=True),
               sg.Text("Please wait", key="-TXT_OPTION4-"),
               sg.Input("", key="-OPTION4-", size=(8, 1), enable_events=True)],

              [sg.Checkbox("", default=True, key="-NEG-", enable_events=True),
               sg.Text("Do negation?", key="-TXT_NEG-")],

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


def update_options(window, config: sql.Config_template):
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


def popup_job_done(answer_streak):
    sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times in a row")
