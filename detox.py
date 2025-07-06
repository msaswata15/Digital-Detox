import os
import sys
import json

import psutil
import webbrowser
from colorama import init, Fore, Style
try:
    import pygame
    pygame_available = True
except ImportError:
    pygame_available = False
import datetime
import time
try:
    import schedule
except ImportError:
    schedule = None

CONFIG_PATH = 'config.json'
HOSTS_PATH = r'C:\Windows\System32\drivers\etc\hosts'
REDIRECT_IP = '127.0.0.1'

init(autoreset=True)

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

def log(msg, color=Fore.GREEN):
    print(color + msg + Style.RESET_ALL)

def block_websites(sites):
    config = load_config()
    whitelist = set(config.get('website_whitelist', []))
    try:
        with open(HOSTS_PATH, 'r+') as file:
            content = file.read()
            file.seek(0, os.SEEK_END)
            blocked = 0
            for site in sites:
                if site in whitelist:
                    continue
                for variant in [site, f"www.{site}"]:
                    entry = f"{REDIRECT_IP} {variant}\n"
                    if entry not in content:
                        file.write(entry)
                        blocked += 1
            if blocked:
                log(f"Websites blocked: {blocked} entries added.")
            else:
                log("No new websites were blocked (already present or whitelisted).", Fore.YELLOW)
    except PermissionError:
        log("Run as administrator to modify hosts file.", Fore.RED)
    except Exception as e:
        log(f"Error blocking websites: {e}", Fore.RED)

def unblock_websites(sites):
    try:
        with open(HOSTS_PATH, 'r') as file:
            lines = file.readlines()
        with open(HOSTS_PATH, 'w') as file:
            for line in lines:
                if not any(site in line for site in sites):
                    file.write(line)
        log("Websites unblocked.")
    except PermissionError:
        log("Run as administrator to modify hosts file.", Fore.RED)

def block_apps(apps):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in apps:
            try:
                proc.kill()
                log(f"Killed {proc.info['name']}")
            except Exception as e:
                log(f"Failed to kill {proc.info['name']}: {e}", Fore.RED)

def play_focus_music(config):
    if config['focus_music']['type'] == 'noisli':
        webbrowser.open('https://www.noisli.com/')
        log("Opened Noisli in browser.")
    else:
        path = config['focus_music']['local_path']
        if os.path.exists(path):
            if pygame_available:
                try:
                    pygame.mixer.init()
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play()
                    log("Playing local focus music (press Ctrl+C to stop).")
                    while pygame.mixer.music.get_busy():
                        time.sleep(1)
                except Exception as e:
                    log(f"Error playing music: {e}", Fore.RED)
            else:
                log("pygame is not installed. Please install it to play local music.", Fore.RED)
        else:
            log("Local music file not found.", Fore.RED)

def show_status(config):
    log("Blocked websites:", Fore.CYAN)
    for site in config['blocked_websites']:
        print("  ", site)
    log("Blocked apps:", Fore.CYAN)
    for app in config['blocked_apps']:
        print("  ", app)
    log(f"Focus music: {config['focus_music']}", Fore.CYAN)

def main():
    config = load_config()
    locked = False
    session_active = False
    usage_start = None
    usage_minutes = 0
    def start_detox():
        nonlocal session_active, usage_start
        if config.get('locked_mode', False):
            log("Locked mode enabled. You cannot exit until session ends.", Fore.YELLOW)
        session_active = True
        usage_start = datetime.datetime.now()
        block_websites(config['blocked_websites'])
        block_apps(config['blocked_apps'])
        play_focus_music(config)

    def end_detox():
        nonlocal session_active, usage_minutes, usage_start
        if config.get('locked_mode', False):
            log("Locked mode: Cannot end session until time is up!", Fore.RED)
            return
        unblock_websites(config['blocked_websites'])
        session_active = False
        if usage_start:
            usage_minutes += int((datetime.datetime.now() - usage_start).total_seconds() // 60)
            usage_start = None

    def check_time_limit():
        nonlocal session_active, usage_minutes, usage_start
        if config.get('daily_time_limit', {}).get('enabled', False):
            limit = config['daily_time_limit']['minutes']
            if usage_start:
                total = usage_minutes + int((datetime.datetime.now() - usage_start).total_seconds() // 60)
            else:
                total = usage_minutes
            if total >= limit:
                log(f"Daily time limit of {limit} minutes reached! Ending session.", Fore.RED)
                end_detox()
                return True
        return False

    def schedule_session():
        if not schedule:
            log("Install the 'schedule' package for scheduling support.", Fore.RED)
            return
        st = config.get('schedule', {}).get('start_time', None)
        et = config.get('schedule', {}).get('end_time', None)
        if st and et:
            schedule.every().day.at(st).do(start_detox)
            schedule.every().day.at(et).do(end_detox)
            log(f"Scheduled detox from {st} to {et}.", Fore.YELLOW)
            while True:
                schedule.run_pending()
                if check_time_limit():
                    break
                time.sleep(10)

    while True:
        config = load_config()
        print("\n" + Fore.YELLOW + "Digital Detox Console App")
        print("1. Start Detox (block sites/apps, play music)")
        print("2. End Detox (unblock sites)")
        print("3. Show Status/Config")
        print("4. Edit Config")
        print("5. Enable Locked Mode")
        print("6. Schedule Detox Session")
        print("7. Exit")
        if session_active:
            print(Fore.MAGENTA + "[Session Active]" + Style.RESET_ALL)
        choice = input("Select an option: ")
        if choice == '1':
            if not session_active:
                start_detox()
            else:
                log("Session already active.", Fore.YELLOW)
        elif choice == '2':
            if session_active:
                end_detox()
            else:
                log("No active session.", Fore.YELLOW)
        elif choice == '3':
            show_status(config)
        elif choice == '4':
            os.system(f'notepad {CONFIG_PATH}')
        elif choice == '5':
            config['locked_mode'] = True
            save_config(config)
            log("Locked mode enabled.", Fore.YELLOW)
        elif choice == '6':
            schedule_session()
        elif choice == '7':
            if session_active and config.get('locked_mode', False):
                log("Locked mode: Cannot exit during session!", Fore.RED)
            else:
                break
        else:
            log("Invalid option.", Fore.RED)
        if session_active:
            if check_time_limit():
                continue

if __name__ == '__main__':
    main()
