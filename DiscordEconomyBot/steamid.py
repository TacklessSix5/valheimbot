import requests
import json

LOG_URLS = [
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-25.0000_0.log",
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-26.0000_0.log",
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-27.0000_0.log",
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-28.0000_0.log",
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-29.0000_0.log",
    "https://coffeeheim.sergio.run/logs?f=docker.valheim.2024-07-30.0000_0.log"
]
STEAMID_DICT_FILE = "steamids.txt"


def get_log_data(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching log data from {url}: {e}")
        return ""


def extract_steamid_to_name(log_data: str) -> dict:
    steamid_to_name = {}

    for line in log_data.splitlines():
        try:
            timestamp, service, log_json = line.split("\t", 2)
            log_entry = json.loads(log_json)
            message = log_entry.get("log", "")

            # Extract player name and SteamID from "I HAVE ARRIVED!" messages
            if "I HAVE ARRIVED!" in message:
                parts = message.split(": ")
                if len(parts) > 1:
                    playername = parts[0].split("</color>")[0].split("<color=#FFEB04FF>")[0].strip()
                    steamid = log_entry.get("User", "")
                    if steamid and steamid != "0":
                        steamid_to_name[steamid] = playername
                        print(f"Mapped {steamid} to {playername}")

            # Extract player name and SteamID from disconnection messages
            if "disconnected" in message:
                parts = message.split(" ")
                for part in parts:
                    if "[" in part and "]" in part:
                        steamid = part.split("[")[1].split("]")[0]
                        playername = part.split("[")[0]
                        if steamid and steamid != "0":
                            steamid_to_name[steamid] = playername
                            print(f"Mapped {steamid} to {playername}")

        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing line: {line}\n{e}")
            continue

    return steamid_to_name


def read_existing_steamid_file(file_path: str) -> dict:
    steamid_to_name = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                if "[" in line and "]" in line:
                    playername = line.split("[")[0].strip()
                    steamid = line.split("[")[1].split("]")[0]
                    if steamid and steamid != "0":
                        steamid_to_name[steamid] = playername
    except FileNotFoundError:
        pass  # If the file does not exist, return an empty dictionary

    return steamid_to_name


def main():
    existing_steamid_to_name = read_existing_steamid_file(STEAMID_DICT_FILE)

    for url in LOG_URLS:
        log_data = get_log_data(url)
        if log_data:
            new_steamid_to_name = extract_steamid_to_name(log_data)
            # Only update the dictionary with new entries
            for steamid, playername in new_steamid_to_name.items():
                if steamid not in existing_steamid_to_name:
                    existing_steamid_to_name[steamid] = playername

    # Sort by player names
    sorted_steamid_to_name = dict(sorted(existing_steamid_to_name.items(), key=lambda item: item[1]))

    with open(STEAMID_DICT_FILE, "w") as f:
        for steamid, playername in sorted_steamid_to_name.items():
            if steamid != "0":
                f.write(f"{playername}[{steamid}]\n")


if __name__ == "__main__":
    main()