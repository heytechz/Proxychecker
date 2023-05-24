import socket
import queue
import threading
import time
from struct import pack
import os
from colorama import Fore, Back, Style
import requests
import geocoder


print("MADE BY ADITYA")
time.sleep(5)
# Configuration
timeout = 10
threads = 40
bot_token = os.environ['token']
chat_id = "6068365157"

if os.path.exists('saved.txt'):
    try:
        os.remove('saved.txt')
        print(Fore.RED + "[$] Cleaning old proxy")
        time.sleep(5)
    except FileNotFoundError:
        pass
else:
    print(Fore.RED + "[$] No old proxy file found")

print(Fore.GREEN + "[$] Started checking ..")

class ThreadChecker(threading.Thread):
    def __init__(self, queue, timeout, user_agent):
        super().__init__()
        self.timeout = timeout
        self.q = queue
        self.user_agent = user_agent
    
    def is_socks4(self, host, port, soc):
        ipaddr = socket.inet_aton(host)
        packet4 = b"\x04\x01" + pack(">H", port) + ipaddr + b"\x00"
        soc.sendall(packet4)
        data = soc.recv(8)
        if len(data) < 2 or data[0] != 0 or data[1] != 0x5A:
            return False
        return True

    def is_socks5(self, host, port, soc):
        soc.sendall(b"\x05\x01\x00")
        data = soc.recv(2)
        if len(data) < 2 or data[0] != 0x05 or data[1] != 0:
            return False
        return True

    def get_socks_version(self, proxy):
        host, port = proxy.split(":")
        try:
            port = int(port)
            if not 0 < port <= 65536:
                print(Fore.RED + "Invalid port: " + proxy)
                return 0
        except ValueError:
            print("Invalid port: " + proxy)
            return 0
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)

        try:
            s.connect((host, port))
            if self.is_socks4(host, port, s):
                return 4
            elif self.is_socks5(host, port, s):
                return 5
            else:
                print(Fore.RED + "Not a SOCKS proxy: " + proxy)
                return 0
        except socket.timeout:
            print(Fore.YELLOW + "Timeout: " + proxy)
            return 0
        except socket.error:
            print(Fore.RED + "Connection refused: " + proxy)
            return 0
        finally:
            s.close()

    def check_proxy_country(self, proxy):
        ip_address = proxy.split(":")[0]
        g = geocoder.ip(ip_address)
        if g.ok:
            country = g.country
            with open("saved.txt", 'a') as output_file:
                output_file.write(f"{proxy} | Country: {country}\n")
            print(Fore.GREEN + f"Working Proxy: {proxy} | Country: {country}")
        else:
            print(f"Failed to retrieve geolocation information for proxy: {proxy}")

    def run(self):
        while True:
            proxy = self.q.get()
            version = self.get_socks_version(proxy)
            if version in (4, 5):
                self.check_proxy_country(proxy)
            self.q.task_done()

check_queue = queue.Queue()
with open("proxy.txt", 'r') as input_file:
    for line in input_file:
        check_queue.put(line.strip())

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
for _ in range(threads):
    t = ThreadChecker(check_queue, timeout, user_agent)
    t.daemon = True
    t.start()
    time.sleep(0.25)
check_queue.join()
print(Fore.GREEN + "[$] Saved all proxy to file")

# Telegram
if not bot_token:
    print(Fore.RED + "Telegram bot token not provided. Skipping sending proxy list to Telegram.")
    exit()
with open("saved.txt", "r") as file:
    proxy_list = file.read().strip().split("\n")
message = "WORKING PROXY LIST :\n\n" + "\n".join(proxy_list) + "\n\n MADE BY ADITYA"
api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
response = requests.post(api_url, json={"chat_id": chat_id, "text": message})
if response.status_code == 200:
    print(Fore.GREEN + "Proxy list sent successfully to Telegram.")
else:
    print(Fore.RED + "Failed to send proxy list to Telegram.")
#END MADE BY ADITYA ALWAYS REMEMBER