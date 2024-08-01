import requests
import json
from datetime import datetime, timedelta

LOG_URL = "https://coffeeheim.sergio.run/logs?f=buffer/buffer.b61e7fc696a15e696ad18b0e9e92c26c4.log"
STEAMID_DICT_FILE = "steamids.txt"
OUTPUT_FILE = "steamid_connections.txt"

def get_log_data(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching log data: {e}")
        return ""

def read_steamid_to_name(file_path: str) -> dict:
    steamid_to_name = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                if "[" in line and "]" in line:
                    playername = line.split("[")[0].strip()
                    steamid = line.split("[")[1].split("]")[0]
                    steamid_to_name[steamid] = playername
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    return steamid_to_name

def extract_steamid_connections(log_data: str, steamid_to_name: dict) -> list:
    steamid_connections = []
    last_event_time = {}

    def should_log_event(steamid, current_time, event_type):
        if steamid in last_event_time:
            last_time, last_type = last_event_time[steamid]
            if current_time - last_time < timedelta(seconds=5) and last_type == event_type:
                return False
        last_event_time[steamid] = (current_time, event_type)
        return True

    for line in log_data.splitlines():
        try:
            timestamp, service, log_json = line.split("\t", 2)
            log_entry = json.loads(log_json)
            message = log_entry.get("log", "")
            current_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')

            # Extract player name and SteamID from disconnection messages
            if "disconnected" in message:
                parts = message.split(" ")
                for part in parts:
                    if "[" in part and "]" in part:
                        steamid = part.split("[")[1].split("]")[0]
                        playername = steamid_to_name.get(steamid, "Unknown")
                        if should_log_event(steamid, current_time, "disconnected"):
                            formatted_message = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: {playername}[{steamid}] disconnected."
                            steamid_connections.append(formatted_message)

            # Extract SteamID connections
            if "Got connection SteamID" in message and "Console" not in message:
                steamid = message.split("SteamID")[1].strip()
                playername = steamid_to_name.get(steamid, "Unknown")
                if should_log_event(steamid, current_time, "connected"):
                    formatted_message = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: {playername}[{steamid}] connected."
                    steamid_connections.append(formatted_message)

        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing line: {line}\n{e}")
            continue

    return steamid_connections

def main():
    steamid_to_name = read_steamid_to_name(STEAMID_DICT_FILE)
    log_data = get_log_data(LOG_URL)
    if log_data:
        steamid_connections = extract_steamid_connections(log_data, steamid_to_name)
        with open(OUTPUT_FILE, "w") as f:
            for connection in steamid_connections:
                f.write(connection + "\n")

if __name__ == "__main__":
    main()