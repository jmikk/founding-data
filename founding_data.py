import requests
import xml.etree.ElementTree as ET
import csv
import time
from datetime import datetime, timedelta
import os
import re


def get_user_agent():
    return input("Please enter your user agent: ")


def get_months_back():
    return int(input("Please enter the number of months back to check: "))


def fetch_data(user_agent, before_id=None):
    url = "https://www.nationstates.net/cgi-bin/api.cgi?q=happenings;filter=founding;limit=100"
    if before_id:
        url += f";beforeid={before_id}"
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def parse_xml(xml_data):
    root = ET.fromstring(xml_data)
    happenings = root.find("HAPPENINGS")
    events = []
    for event in happenings.findall("EVENT"):
        event_id = event.get("id")
        timestamp = int(event.find("TIMESTAMP").text)
        text = event.find("TEXT").text
        events.append((event_id, timestamp, text))
    return events


def filter_events(events, cutoff_time):
    founded_events = []
    refounded_events = []
    all_events = []
    r_founded_events = []
    r_refounded_events = []
    r_all_events = []

    def is_valid_nation_name(nation):
        return not re.match(r"^\d", nation) and not re.match(r".*\d$", nation)

    for event_id, timestamp, text in events:
        if timestamp < cutoff_time:
            continue
        nation = text.split("@@")[1].split("@@")[0]
        if "founded" in text:
            founded_events.append((nation, timestamp))
            if is_valid_nation_name(nation):
                r_founded_events.append((nation, timestamp))
        if "refounded" in text:
            refounded_events.append((nation, timestamp))
            if is_valid_nation_name(nation):
                r_refounded_events.append((nation, timestamp))
        all_events.append((nation, timestamp))
        print(nation)
        if is_valid_nation_name(nation):
            r_all_events.append((nation, timestamp))
    return (
        founded_events,
        refounded_events,
        all_events,
        r_founded_events,
        r_refounded_events,
        r_all_events,
    )


def write_csv(filename, events, folder):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", newline="") as csvfile:
        fieldnames = ["Nation", "Timestamp"]
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        writer.writerows(events)


def main():
    user_agent = get_user_agent()
    months_back = get_months_back()
    current_time = datetime.utcnow()
    cutoff_time = int((current_time - timedelta(days=months_back * 30)).timestamp())

    founded_events = []
    refounded_events = []
    all_events = []
    r_founded_events = []
    r_refounded_events = []
    r_all_events = []

    before_id = None
    while True:
        xml_data = fetch_data(user_agent, before_id)
        events = parse_xml(xml_data)
        (
            new_founded,
            new_refounded,
            new_all,
            r_new_founded,
            r_new_refounded,
            r_new_all,
        ) = filter_events(events, cutoff_time)

        founded_events.extend(new_founded)
        refounded_events.extend(new_refounded)
        all_events.extend(new_all)
        r_founded_events.extend(r_new_founded)
        r_refounded_events.extend(r_new_refounded)
        r_all_events.extend(r_new_all)

        if not events or events[-1][1] < cutoff_time:
            break

        before_id = events[-1][0]
        time.sleep(1)

    write_csv("founded_events.csv", founded_events, "all")
    write_csv("refounded_events.csv", refounded_events, "all")
    write_csv("all_events.csv", all_events, "all")
    print("")
    print("")
    print(
        f"There was an average of {len(all_events)/ (months_back*30*24*60)} nations including puppets per minute."
    )

    write_csv("r_founded_events.csv", r_founded_events, "no_pups")
    write_csv("r_refounded_events.csv", r_refounded_events, "no_pups")
    write_csv("r_all_events.csv", r_all_events, "no_pups")
    print(
        f"There was an average of {len(r_all_events)/ (months_back*30*24*60)} nations excluding puppets per minute."
    )


if __name__ == "__main__":
    main()
