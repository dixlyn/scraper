import json
import os
import requests
import re
import datetime
from rich.console import Console
import time

console = Console(highlight=False)

class count:
    total_emojis = 0
    total_stickers = 0
    current_emojis = 0
    current_stickers = 0

class color:
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GREEN = '\033[92m'
    UNDERLINE = '\033[4m'

def reset_console():
    e = datetime.datetime.now()
    if os.name in ('nt', 'dos'):  
        os.system("cls")
    else:
        os.system("clear")

    print("""
    ░██████╗░█████╗░██████╗░░█████╗░██████╗░███████╗██████╗░
    ██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
    ╚█████╗░██║░░╚═╝██████╔╝███████║██████╔╝█████╗░░██████╔╝
    ░╚═══██╗██║░░██╗██╔══██╗██╔══██║██╔═══╝░██╔══╝░░██╔══██╗
    ██████╔╝╚█████╔╝██║░░██║██║░░██║██║░░░░░███████╗██║░░██║
    ╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝\n""")

def find_guild(id, token):
    result = requests.get(url = f"https://discordapp.com/api/v7/guilds/{id}", headers = {"authorization": token}).json()
    emojis = None

    if ("message" in result):
        if (result["code"] == 0):
            print("The provided Discord token is invalid, please fix this and try again!")
            quit()
        else:
            print(" Unable to scrape emojis from {}.".format(id))
        return None
    else:
        stickers = requests.get(url = f"https://discordapp.com/api/v9/guilds/{id}/stickers", headers={"authorization": token}).json()
        emojis = requests.get(url = f"https://discordapp.com/api/v7/guilds/{id}/emojis", headers = {"authorization": token}).json()
        count.total_stickers += len(stickers)
        count.total_emojis += len(emojis)
        name = result["name"]
        print(" Found {} ({} emojis | {} stickers).".format(name,  len(emojis), len(stickers)))

        return {
            "name": fix_string(name),
            "guild": result,
            "emojis": emojis,
            "stickers": stickers
        }

def emoji_content(emoji):
    id = emoji["id"]
    bytes = None
    while True:
        try:
            result = requests.get(url = f"https://cdn.discordapp.com/emojis/{id}")
            if (result.content):
                bytes = result.content
        except Exception as exception:
            if exception == KeyboardInterrupt or exception == SystemExit:
                print("User interrupted, closing program!")
                raise
        else:
            break
    return bytes

def sticker_content(sticker):
    id = sticker["id"]
    bytes = None
    while True:
        try:
            result = requests.get(url = f"https://media.discordapp.net/stickers/{id}")
            if (result.content):
                bytes = result.content
        except Exception as exception:
            if exception == KeyboardInterrupt or exception == SystemExit:
                print("User interrupted, closing program!")
                raise
        else:
            break
    return bytes

def create_dir(name):
    path = os.path.join(name)
    if not os.path.isdir(path):
        os.mkdir(path)

def save(path, bytes):
    result = open(path, 'wb')
    result.write(bytes)
    result.close()

def emoji_type(bytes):
    if str(bytes)[0:7].find("GIF") != -1:
        return ".gif"
    return ".png"

def get_data(ids, token):
    result = []
    if (len(ids) == 0):
        print(" You have provided no guild IDs in the 'config.json' file")
        input(" Press enter to continue...")
        quit()

    for id in ids:
        guild = find_guild(id, token)
        if (guild): result.append(guild)   

    print(" \n You are about to scrape all emojis and stickers from the provided guilds")
    input(" Press Enter to continue...")
    reset_console()
    return result 

def fix_string(string):
    result = re.sub('[^\w\s-]', '', string)
    return ' '.join(result.split())

def scrape(config): 
    token = config["token"]
    guilds = get_data(config["guilds"], token)
    guild_count = 0

    start_time = time.time()
    for key in guilds:
        guild_count += 1
        count.current_emojis = 0
        count.current_stickers = 0
        count.current_total = 0

        guild = key["guild"]

        if (len(guild["emojis"]) == 0 and len(guild["stickers"]) == 0):
            print(" No emojis or stickers were found in {}".format(guild["name"]))
            continue

        create_dir(config["emoji_path"] + "/" + key["name"])
        create_dir(config["sticker_path"] + "/" + key["name"])

        with console.status("", spinner="simpleDotsScrolling", spinner_style="white") as status:
            for sticker in guild["stickers"]:
                status.update("Scraping stickers from {} (guild {}/{} | {} remaining)".format(guild["name"], guild_count, len(guilds), (len(guild["stickers"]) + len(guild["emojis"]) - count.current_total)))
                bytes = sticker_content(sticker)
                
                if (bytes):
                    file_format = ".png"
                    path = os.path.join(config["sticker_path"], key["name"], (fix_string(sticker["name"]) + file_format))
                    if not os.path.isfile(path):
                        save(path, bytes)

                    count.current_stickers += 1 
                    count.current_total += 1 
                    console.print(" [{}/{}] Downloaded {}{} ({}) from {}".format(count.current_stickers, len(guild["stickers"]), sticker["name"], file_format, sticker["id"], guild["name"]))

            for emoji in guild["emojis"]:
                status.update("Scraping emojis from {} (guild {}/{} | {} remaining)".format(guild["name"], guild_count, len(guilds), (len(guild["stickers"]) + len(guild["emojis"]) - count.current_total)))
                bytes = emoji_content(emoji)
                path = os.path.join(config["emoji_path"], key["name"], (fix_string(emoji["name"]) + emoji_type(bytes)))

                if (bytes):
                    if not os.path.isfile(path):
                        save(path, bytes) 
                    count.current_emojis += 1 
                    count.current_total += 1 
                    console.print(" [{}/{}] Downloaded {}{} ({}) from {}".format(count.current_emojis, len(guild["emojis"]), emoji["name"], emoji_type(bytes), emoji["id"], guild["name"]))

            print("\n Task complete ({:.2f} secs)".format(time.time() - start_time))
            
def main():
    try: 
        reset_console()
        
        with open("config.json") as json_data_file:
            config = json.load(json_data_file)
            create_dir(config["emoji_path"])
            create_dir(config["sticker_path"])
            scrape(config)
    except FileNotFoundError:
        print("\n An error has occured, this is most likely an issue with your 'config.json' file.")
        input("Press Enter to continue...")
    time.sleep()
main()