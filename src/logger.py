import csv
import datetime
import os
import platform
import subprocess


def log_event(log_file, state, avg_ear, perclos, face_detected, message):
    directory = os.path.dirname(log_file)
    if directory:
        os.makedirs(directory, exist_ok=True)

    file_exists = os.path.isfile(log_file)
    now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

    with open(log_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "state", "ear", "perclos", "face_detected", "message"])
        writer.writerow([now, state, f"{avg_ear:.2f}", f"{perclos:.2f}", face_detected, message])


def send_system_notification(title, message):
    system = platform.system()
    if system == "Darwin":
        try:
            subprocess.run([
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"'
            ], check=False)
        except Exception:
            pass
    elif system == "Linux":
        try:
            subprocess.run(["notify-send", title, message], check=False)
        except Exception:
            pass
    elif system == "Windows":
        try:
            subprocess.run([
                "powershell",
                "-Command",
                f"New-BurntToastNotification -Text '{title}', '{message}'"
            ], check=False)
        except Exception:
            pass
