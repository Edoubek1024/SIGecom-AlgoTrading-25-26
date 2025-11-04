import datetime

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
NAME = "main"

def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = get_color(level)
    log_message = f"{color}{timestamp} - {NAME} [{level}]: {message}{RESET}"
    print(log_message)

def get_color(level):
    if level == "ERROR":
        return RED
    elif level == "WARNING":
        return YELLOW
    return GREEN