import requests
import json
import asyncio
import aiohttp
import os

STEAMID_DICT_FILE = "steamids.txt"
BUFFER_URL = "https://coffeeheim.sergio.run/logs?f=buffer/buffer.b61e7fc696a15e696ad18b0e9e92c26c4.log"
CHAT_MESSAGES_FILE = "chat.txt"


async def fetch_log_data(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            print(f"Error fetching log data from {url}: {e}")
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


def extract_chat_messages(log_data: str, steamid_to_name: dict) -> list:
    chat_messages = []

    for line in log_data.splitlines():
        try:
            if "I HAVE ARRIVED!" in line:
                timestamp, service, log_json = line.split("\t", 2)
                log_entry = json.loads(log_json)
                message = log_entry.get("log", "")
                parts = message.split(": ")
                if len(parts) > 1:
                    playername = parts[0].split("</color>")[0].replace("<color=orange>", "").strip()
                    chat_text = parts[1].split("</color>")[0].replace("<color=#FFEB04FF>", "").strip()
                    steamid = log_entry.get("User", "")
                    playername = steamid_to_name.get(steamid, playername)
                    formatted_message = f"{playername}: {chat_text}"
                    chat_messages.append(formatted_message)
                    print(f"Extracted chat message: {formatted_message}")
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing line: {line}\n{e}")
            continue

    return chat_messages


def write_chat_messages(messages: list):
    with open(CHAT_MESSAGES_FILE, "a") as f:
        for message in messages:
            f.write(message + "\n")


async def main():
    steamid_to_name = read_steamid_to_name(STEAMID_DICT_FILE)

    while True:
        log_data = await fetch_log_data(BUFFER_URL)
        if log_data:
            chat_messages = extract_chat_messages(log_data, steamid_to_name)
            if chat_messages:
                write_chat_messages(chat_messages)
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())