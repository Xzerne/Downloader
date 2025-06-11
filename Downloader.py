import os
import re
import subprocess
import requests
import pyperclip
import glob
import urllib.parse
import cloudscraper
from termcolor import colored

DOWNLOAD_PATH = "/storage/emulated/0/Download"

# --- LOG ---
def log_info(msg): print(colored(f"[INFO] {msg}", "cyan"))
def log_success(msg): print(colored(f"[SUCCESS] {msg}", "green"))
def log_error(msg): print(colored(f"[ERROR] {msg}", "red"))
def log_warning(msg): print(colored(f"[WARNING] {msg}", "yellow"))
def log_action(msg): print(colored(f"👉 {msg}", "magenta"))

# --- ARIA2C ---
def aria2c_turbo(url, filename):
    log_info("Starting aria2c download...")
    cmd = f'aria2c -x 16 -s 16 -k 1M --file-allocation=none --continue=true -o "{filename}" "{url}" -d {DOWNLOAD_PATH}'
    subprocess.run(cmd, shell=True)
    log_success(f"File saved: {os.path.join(DOWNLOAD_PATH, filename)}")

# --- GOOGLE DRIVE ---
def gdrive_download(link):
    log_info("Processing...")
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    file_id = match.group(1) if match else None
    if not file_id:
        log_error("Cannot extract file ID.")
        return

    env = os.environ.copy()
    env["GDOWN_ARIA2"] = "true"
    cmd = f"gdown 'https://drive.google.com/uc?id={file_id}'"
    subprocess.run(cmd, shell=True, env=env)

    files = sorted(glob.glob("*"), key=os.path.getmtime, reverse=True)
    for file in files:
        if os.path.isfile(file):
            dest_path = os.path.join(DOWNLOAD_PATH, file)
            os.rename(file, dest_path)
            log_success(f"File saved: {dest_path}")
            return

# --- MEGA ---
def mega_download(link):
    log_info("Downloading from Mega.nz...")
    cmd = f"megadl '{link}' --path {DOWNLOAD_PATH}"
    subprocess.run(cmd, shell=True)
    log_success("Mega.nz download completed.")

# --- MEDIAFIRE (FULL CLOUDSCRAPER FIX) ---
def mediafire_direct(link):
    log_info(" Processing...")
    scraper = cloudscraper.create_scraper()
    page = scraper.get(link).text

    match = re.search(r'href="(https://download[^"]+)"', page)
    if match:
        return match.group(1)

    match_alt = re.search(r'id="downloadButton".*?href="(https://[^\"]+)"', page, re.DOTALL)
    if match_alt:
        return match_alt.group(1)

    return None

def mediafire_download(link):
    direct = mediafire_direct(link)
    if not direct:
        log_error("Fail to decode link")
        return
    log_action(f"Direct link: {direct}")
    filename = direct.split("/")[-1].split("?")[0]
    filename = urllib.parse.unquote(filename)
    aria2c_turbo(direct, filename)

# --- ONEDRIVE ---
def onedrive_download(link):
    log_info("Downloading from OneDrive...")
    filename = link.split("/")[-1].split("?")[0]
    aria2c_turbo(link, filename)

# --- LINK DETECTOR ---
def auto_download(link):
    if "drive.google.com" in link:
        gdrive_download(link)
    elif "mega.nz" in link:
        mega_download(link)
    elif "mediafire.com" in link:
        mediafire_download(link)
    elif "1drv.ms" in link or "sharepoint.com" in link:
        onedrive_download(link)
    else:
        log_error("Unsupported link.")

# --- MAIN ---
def menu():
    while True:
        os.system("clear")
        print(colored("🚀 TERMUX TURBO DOWNLOADER PRO MAX v2 🚀", "yellow", attrs=["bold"]))
        print(colored("1️⃣ Paste link manually", "cyan"))
        print(colored("2️⃣ Read link from clipboard", "cyan"))
        print(colored("3️⃣ Read multiple links from .txt file", "cyan"))
        print(colored("4️⃣ Exit", "cyan"))

        choice = input(colored("👉 Select option: ", "magenta")).strip()

        if choice == '1':
            link = input(colored("📎 Enter link: ", "magenta")).strip()
            auto_download(link)

        elif choice == '2':
            try:
                link = pyperclip.paste()
                log_info(f"Clipboard link: {link}")
                auto_download(link)
            except:
                log_error("Clipboard error.")

        elif choice == '3':
            txt = input(colored("📄 Enter txt filename: ", "magenta")).strip()
            if os.path.exists(txt):
                with open(txt) as f:
                    links = [line.strip() for line in f if line.strip()]
                for link in links:
                    auto_download(link)
            else:
                log_error("File not found.")

        elif choice == '4':
            log_success("Goodbye!")
            break
        else:
            log_warning("Invalid selection.")

if __name__ == '__main__':
    menu()
