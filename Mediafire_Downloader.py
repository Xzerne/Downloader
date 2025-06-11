import os
import requests
import re
import cloudscraper
import multiprocessing
import math
from termcolor import colored
import urllib.parse

DOWNLOAD_PATH = "/storage/emulated/0/Download"
CHUNK_COUNT = 8

def log_info(msg): print(colored(f"[INFO] {msg}", "cyan"))
def log_success(msg): print(colored(f"[SUCCESS] {msg}", "green"))
def log_error(msg): print(colored(f"[ERROR] {msg}", "red"))
def log_action(msg): print(colored(f"👉 {msg}", "magenta"))

def get_direct_link(link):
    log_info("Resolving Mediafire direct link...")
    scraper = cloudscraper.create_scraper()
    page = scraper.get(link).text
    match = re.search(r'href="(https://download[^"]+)"', page)
    if match:
        return match.group(1)
    match_alt = re.search(r'id="downloadButton".*?href="(https://[^\"]+)"', page, re.DOTALL)
    if match_alt:
        return match_alt.group(1)
    return None

def get_file_info(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.head(url, headers=headers, allow_redirects=True)
    size = int(r.headers.get('Content-Length', 0))
    filename = url.split("/")[-1].split("?")[0]
    filename = urllib.parse.unquote(filename)
    return filename, size

def download_part(url, start, end, part_num, filename):
    headers = {'Range': f'bytes={start}-{end}'}
    log_info(f"Downloading part {part_num} ({start}-{end})...")
    r = requests.get(url, headers=headers, stream=True)
    part_path = f"{filename}.part{part_num}"
    with open(part_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    log_success(f"Part {part_num} completed.")

def merge_parts(filename):
    log_info("Merging parts...")
    with open(filename, 'wb') as outfile:
        for i in range(CHUNK_COUNT):
            part_path = f"{filename}.part{i}"
            with open(part_path, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(part_path)
    log_success(f"File merged: {filename}")

def turbo_download(link):
    direct_link = get_direct_link(link)
    if not direct_link:
        log_error("Failed to resolve direct link.")
        return
    filename, filesize = get_file_info(direct_link)
    log_action(f"Filename: {filename} | Size: {filesize / (1024*1024):.2f} MB")

    chunk_size = math.ceil(filesize / CHUNK_COUNT)
    processes = []

    for i in range(CHUNK_COUNT):
        start = i * chunk_size
        end = min(start + chunk_size - 1, filesize - 1)
        p = multiprocessing.Process(target=download_part, args=(direct_link, start, end, i, filename))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    merge_parts(filename)
    os.rename(filename, os.path.join(DOWNLOAD_PATH, filename))
    log_success(f"✅ Download complete: {os.path.join(DOWNLOAD_PATH, filename)}")

if __name__ == '__main__':
    link = input("Enter Mediafire link: ").strip()
    turbo_download(link)
    