import PySimpleGUI as sg
import json
import os
import webbrowser
import psutil
import datetime
import time

CONFIG_PATH = 'config.json'
HOSTS_PATH = r'C:\Windows\System32\drivers\etc\hosts'
REDIRECT_IP = '127.0.0.1'

# --- Utility functions ---
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def block_websites(sites, whitelist):
    try:
        with open(HOSTS_PATH, 'r+') as file:
            content = file.read()
            file.seek(0, os.SEEK_END)
            for site in sites:
                if site in whitelist:
                    continue
                for variant in [site, f"www.{site}"]:
                    entry = f"{REDIRECT_IP} {variant}\n"
                    if entry not in content:
                        file.write(entry)
        return True, "Websites blocked."
    except PermissionError:
        return False, "Run as administrator to modify hosts file."
    except Exception as e:
        return False, f"Error: {e}"

def unblock_websites(sites):
    try:
        with open(HOSTS_PATH, 'r') as file:
            lines = file.readlines()
        with open(HOSTS_PATH, 'w') as file:
            for line in lines:
                if not any(site in line for site in sites):
                    file.write(line)
        return True, "Websites unblocked."
    except PermissionError:
        return False, "Run as administrator to modify hosts file."
    except Exception as e:
        return False, f"Error: {e}"

def block_apps(apps):
    killed = []
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in apps:
            try:
                proc.kill()
                killed.append(proc.info['name'])
            except Exception:
                pass
    return killed

def play_focus_music(config):
    if config['focus_music']['type'] == 'noisli':
        webbrowser.open('https://www.noisli.com/')
        return "Opened Noisli in browser."
    else:
        path = config['focus_music']['local_path']
        if os.path.exists(path):
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                return "Playing local focus music."
            except Exception as e:
                return f"Error playing music: {e}"
        else:
            return "Local music file not found."

def show_status(config):
    status = f"Blocked websites: {', '.join(config['blocked_websites'])}\n"
    status += f"Blocked apps: {', '.join(config['blocked_apps'])}\n"
    status += f"Focus music: {config['focus_music']}\n"
    return status

# --- GUI Layout ---

sg.theme('DarkBlue14')
layout = [
    [sg.Image(data=None, key='-LOGO-', size=(1,1)), sg.Text('Digital Detox', font=('Segoe UI', 22, 'bold'), justification='center', expand_x=True)],
    [sg.Frame('Status', [[sg.Multiline('', size=(60, 8), key='-STATUS-', disabled=True, autoscroll=True)]], expand_x=True)],
    [sg.Button('Start Detox', size=(18,2), button_color=('white', '#007ACC')), 
     sg.Button('End Detox', size=(18,2), button_color=('white', '#D9534F')), 
     sg.Button('Show Status', size=(18,2), button_color=('white', '#5BC0DE'))],
    [sg.Text('Locked Mode:'), sg.Checkbox('', key='-LOCKED-', default=False, enable_events=True),
     sg.Text('Daily Limit (min):'), sg.Input(key='-LIMIT-', size=(5,1), default_text='60'),
     sg.Button('Set Limit', size=(10,1), button_color=('white', '#5CB85C'))],
    [sg.Text('Schedule:'), sg.Input(key='-START-', size=(6,1), default_text='09:00'), sg.Text('to'), sg.Input(key='-END-', size=(6,1), default_text='17:00'),
     sg.Button('Set Schedule', size=(12,1), button_color=('white', '#5BC0DE'))],
    [sg.Button('Edit Config', size=(18,2), button_color=('white', '#5CB85C')), 
     sg.Button('Exit', size=(18,2), button_color=('white', '#292B2C'))]
]

window = sg.Window('Digital Detox', layout, finalize=True)

# --- Main Event Loop ---
session_active = False
locked_mode = False
remaining_minutes = 60
schedule_start = '09:00'
schedule_end = '17:00'
import threading
import schedule as sched

def detox_session():
    global session_active, remaining_minutes
    config = load_config()
    ok, msg = block_websites(config['blocked_websites'], set(config.get('website_whitelist', [])))
    window['-STATUS-'].update(msg)
    killed = block_apps(config['blocked_apps'])
    music_msg = play_focus_music(config)
    session_active = True
    start_time = datetime.datetime.now()
    # Re-read hosts file to verify block
    try:
        with open(HOSTS_PATH, 'r') as f:
            hosts_content = f.read()
        blocked_now = [site for site in config['blocked_websites'] if site in hosts_content or f"www.{site}" in hosts_content]
    except Exception:
        blocked_now = []
    while session_active and remaining_minutes > 0:
        window['-STATUS-'].update(f"{msg}\nBlocked: {', '.join(blocked_now)}\nKilled apps: {', '.join(killed) if killed else 'None'}\n{music_msg}\nTime left: {remaining_minutes} min")
        time.sleep(60)
        remaining_minutes -= 1
    if session_active:
        window['-STATUS-'].update("Daily time limit reached. Detox ended.")
        end_detox()

def end_detox():
    global session_active
    config = load_config()
    ok, msg = unblock_websites(config['blocked_websites'])
    session_active = False
    window['-STATUS-'].update(msg)

def schedule_detox():
    sched.clear()
    sched.every().day.at(schedule_start).do(lambda: threading.Thread(target=detox_session, daemon=True).start())
    sched.every().day.at(schedule_end).do(end_detox)
    def run_schedule():
        while True:
            sched.run_pending()
            time.sleep(10)
    threading.Thread(target=run_schedule, daemon=True).start()
    window['-STATUS-'].update(f"Scheduled detox from {schedule_start} to {schedule_end}.")

while True:
    event, values = window.read(timeout=100)
    if event == sg.WINDOW_CLOSED or event == 'Exit':
        if session_active and locked_mode:
            window['-STATUS-'].update('Locked mode enabled. Cannot exit during session.')
            continue
        break
    config = load_config()
    if event == 'Start Detox':
        if not session_active:
            threading.Thread(target=detox_session, daemon=True).start()
        else:
            window['-STATUS-'].update('Session already active.')
    elif event == 'End Detox':
        if locked_mode and session_active:
            window['-STATUS-'].update('Locked mode enabled. Cannot end session.')
        else:
            end_detox()
    elif event == 'Show Status':
        window['-STATUS-'].update(show_status(config))
    elif event == 'Edit Config':
        os.system(f'notepad {CONFIG_PATH}')
        window['-STATUS-'].update('Config file opened. Please save and close Notepad to apply changes.')
    elif event == '-LOCKED-':
        locked_mode = values['-LOCKED-']
        window['-STATUS-'].update(f'Locked mode set to {locked_mode}')
    elif event == 'Set Limit':
        try:
            remaining_minutes = int(values['-LIMIT-'])
            window['-STATUS-'].update(f'Daily time limit set to {remaining_minutes} minutes.')
        except Exception:
            window['-STATUS-'].update('Invalid time limit.')
    elif event == 'Set Schedule':
        schedule_start = values['-START-']
        schedule_end = values['-END-']
        schedule_detox()
window.close()
