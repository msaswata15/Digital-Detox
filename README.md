# Digital Detox App

A modern, user-friendly app to help you focus by blocking distracting websites and apps, with a beautiful cross-platform GUI.

## Features
- **Block Websites:** Modifies Windows hosts file to block distracting sites.
- **Block Apps:** Kills distracting apps (e.g., browsers, games).
- **Website Exceptions:** Whitelist for allowed sites.
- **Scheduled Sessions:** Set start/end times for automatic detox.
- **Locked Mode:** Prevents interruption during focus sessions.
- **Ambient Focus Music:** Play Noisli or local MP3s.
- **Daily Time Limit:** Restrict total focus time per day.
- **Modern GUI:** Easy-to-use interface with PySimpleGUI.

## Requirements
- Python 3.8+
- Run as Administrator (for website blocking)
- Install dependencies:
  ```
  pip install PySimpleGUI psutil pygame schedule
  ```
  (If you see a message about a private PySimpleGUI server, follow the instructions in your terminal.)

## Usage
1. **Edit `config.json`** to set blocked sites, apps, music, etc.
2. **Run the GUI:**
   ```
   python detox_gui.py
   ```
   (Or use your full python path if needed)
3. **Start/End Detox** with the GUI buttons.
4. **Set schedule, locked mode, and daily limit** directly in the GUI.

## Notes
- For website blocking, always run as Administrator.
- To unblock a site, use "End Detox" or remove it from `config.json` and restart the app.
- For browser insight/limits, a browser extension is required (not included).

## Screenshots
![screenshot](screenshot.png)

---

Made with ❤️ for focus and productivity.# Digital Detox Console App

A Windows console app to help you focus by blocking distracting websites and apps, and playing focus music.

## Features
- Interactive console UI
- Block websites (hosts file)
- Block apps (kill processes)
- Configurable via `config.json`
- Play focus music (Noisli or local MP3)
- Console logs/status

## Usage
1. Edit `config.json` to set blocked sites/apps/music.
2. Run `python detox.py`.
