import PySimpleGUI as sg

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
              [sg.Text("Please wait", key="-TXTPENALTY-"),
               sg.Input("", key="-PENALTY-", size=(15, 1), enable_events=True)],
              [sg.Checkbox("", default=False, key="-PERCENT-", enable_events=True),
               sg.Text("Do percent quiz", key="-TXTPERCENT-")],
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


def popup_job_done(answer_streak):
    sg.popup(f"Your job is done for today, because you have answered correctly {answer_streak} times in a row")
