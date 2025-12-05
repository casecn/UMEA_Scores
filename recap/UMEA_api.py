# Gathering marching band score data

import csv
import json
import random
import time
from typing import Dict, List, Set

import requests
BASE = "https://bridge.competitionsuite.com/api/orgscores"
VERSION = "1.1.5"
CALLBACK = "jQuery110209904385531594735_1763353270252?_= 1763353270271"

#'''SEASON_GUID_DICT = {'UMEA 2025': 'ff7a5f4b-b7dc-4cbc-ad0b-1295fdd971a8'}'''
SEASON_GUID_DICT = {'UMEA 2025': 'ff7a5f4b-b7dc-4cbc-ad0b-1295fdd971a8'} #, 'UMEA 2024': '9cd94b0d-a521-4280-98e3-b42b4c4441c5', 'UMEA 2023': 'baa6c584-4547-4370-b8ca-2d05018876d7', 'UMEA 2022': '6d7e8a01-34fb-49c0-bfab-8b62c8f19930'}#, 'UMEA 2021': '871de29c-53ea-4b45-b69a-cbb245861811', 'UMEA 2020': '9e9a151d-762c-4024-aa5a-aa45930939e1', 'UMEA 2019': 'a6bbdab4-a781-4a21-850a-53d42faebe2b', 'UMEA 2018': 'ad102698-0fc8-451a-a5fd-634da78d103d', 'UMEA 2017': 'ea245774-1ae0-464d-92a9-1ddf44600c51', 'UMEA 2016': '334709e3-d486-4cda-b0fb-fbbf0d64966d', 'UMEA 2015': '26b74c10-b696-428f-8463-874b147c606d', 'UMEA 2014': '6cfb281c-6122-4115-8c3b-f0a2097aa48d'}

def get_jsonp(url: str, params=None, timeout: int = 10):
    """
    Call a JSONP endpoint and return parsed JSON.
    Assumes response looks like: callback123({...});
    """
    #Be nice to API by sleeping randomly
    random_float = random.uniform(0, 3)
    time.sleep(random_float)
    
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    raw = resp.text
    # Find first "(" and last ")"
    start = raw.find("(")
    end = raw.rfind(")")

    if start == -1 or end == -1:
        raise ValueError("Response is not valid JSONP")

    json_str = raw[start+1:end]
    #print(json_str)
    return json.loads(json_str)


def get_competitions_for_season(season_id: str):
    # Accessing 'https://bridge.competitionsuite.com/api/orgscores'
    # using the 'get_jsonp' function
    url = f"{BASE}/GetCompetitionsBySeason/jsonp"
    params = {
        "season": season_id,
        "showTrainingEvents": "false",
        "version": VERSION,
        "callback": CALLBACK  # usually not needed; server supplies default
    }
    #print(url)
    data = get_jsonp(url, params=params)
    #print(data)

    competitions = data.get("competitions")
    #print(competitions[0]) 
    if competitions is None:
        raise KeyError("Cannot find competitions list in API response")

    return competitions


def get_competition_results(comp_id):
    url = f"{BASE}/GetCompetition/jsonp"
    params = {
        "competition": comp_id,
        "version": VERSION,
        "callback": "jQuery110209904385531594735_1763353270252&_=1763353270274"
    }

    data = get_jsonp(url, params=params)
    #print(data)
    return data


def flatten_competition_results(comp_data: dict, season_name: str = None):
    """
    Turn one competition's JSON (like the sample you provided)
    into a list of flat row dicts: one row per performance.
    """
    #print(f'Season NAME: {season_name}')
    #print(f'COMP_DICT: {comp_data}')
    rows: List[dict] = []

    # Top-level info
    season_guid = comp_data.get("seasonGuid")
    competition_guid = comp_data.get("competitionGuid")
    competition_name = comp_data.get("name")
    competition_date = comp_data.get("competitionDate")
    competition_location = comp_data.get("location")
    recap_url = comp_data.get("recapUrl")

    # Each "round" is basically a division/class (2A, 3A, 4A Open, etc.)
    for rnd in comp_data.get("rounds", []):
        division_guid = rnd.get("divisionGuid")
        round_guid = rnd.get("roundGuid")
        division_name = rnd.get("name")  # e.g. "4A Open", "6A Scholastic"
        full_recap_url = rnd.get("fullRecapUrl")
        #category_recap_url = rnd.get("categoryRecapUrl")

        for perf in rnd.get("performances", []):
            performance_guid = perf.get("performanceGuid")
            band_name = perf.get("name")
            city = perf.get("city")
            state = perf.get("state")
            score = perf.get("score")
            rank = perf.get("rank")

            row = {
                "season_guid": season_guid,
                "season_name": season_name,           # optional, may be None
                "competition_guid": competition_guid,
                "competition_name": competition_name,
                "competition_date": competition_date,
                "competition_location": competition_location,
                #"competition_recap_url": recap_url,

                "division_guid": division_guid,
                "division_name": division_name,
                "round_guid": round_guid,
                "full_recap_url": full_recap_url,
                #"round_category_recap_url": category_recap_url,

                "performance_guid": performance_guid,
                "band_name": band_name,
                "city": city,
                "state": state,
                "score": score,
                "rank": rank,
            }

            rows.append(row)

    return rows

################################################
################################################
def collect_scores_and_round_guids(
    season_guid_dict: Dict[str, str],
    scores_out_path: str = "umea_marching_band_scores_all_seasons.csv",
    round_guids_out_path: str | None = "umea_recap_guids.csv",
) -> List[str]:

    """
    - Fetch high-level scores for ALL seasons in `season_guid_dict`
    - Write ONE combined CSV with all rows
    - Optionally write a CSV of unique round GUIDs
    - Return sorted list of unique round GUIDs (for main.py to consume)
    """
    
    all_rows: List[dict] = []
    all_round_guids: Set[str] = set()
    
    # Loop through the SEASON_GUID_DICT dictionary
    for season_name, season_id, in season_guid_dict.items():
        for row in iter_flattened_rows_for_season(season_id, season_name):
            all_rows.append(row)

            guid = row.get("round_guid")
            if guid: 
                all_round_guids.add(guid)
    
    if not all_rows:
        print('No rows collected, nothging to write.')
        return []
    
    # Use the keys of the first row as the header
    fieldnames = list (all_rows[0].keys())
    print(fieldnames)

    #1) Write combined scores CSV
    with open(scores_out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f'Wrote {len(all_rows)} rows to {scores_out_path}')

    # 2) Optionally write GUID list
    sorted_guids = sorted(all_round_guids)
    if round_guids_out_path:
        with open(round_guids_out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for guid in sorted_guids:
                writer.writerow([guid])
        print(f"Wrote {len(sorted_guids)} unique round GUIDs to {round_guids_out_path}")

    return sorted_guids

def build_season_scores_csv(season_id: str, season_name: str, out_path: str):
    competitions = get_competitions_for_season(season_id)
    """Get scores for each season AND build csv containing all scores."""
    #print(f'Competitions: {competitions}')
    all_rows = []
    unique_round_guid = set()

    for row in iter_flattened_rows_for_season( season_id, season_name):
        all_rows.append(row)

        guid = row.get('division_guid')
        if guid:
            unique_round_guid(guid)

    if not all_rows:
        print("No rows collected, nothing to write.")
        return

    fieldnames = list(all_rows[0].keys())

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {out_path}")
    print(f"Found {len(unique_round_guid)} unique guids for {season_name}")

    return unique_round_guid


def iter_flattened_rows_for_season(season_id: str, season_name: str):
        """
        Yield flattened row dicts for every performance in a given season.
        This is the only place that calls flatten_competition_results.
        """
        competitions = get_competitions_for_season(season_id)

        for c in competitions:
            comp_id = c.get("competitionGuid")
            comp_data = get_competition_results(comp_id)

            rows = flatten_competition_results(
                comp_data=comp_data,
                season_name=season_name
            )
            for row in rows:
                yield row

"""
all_unique_urls = set()
i = 0
for key, value in season_guid_dict.items():
    #print(f"Key: {key}, Value: {value}")
    season_urls = build_scores_csv(value, key, f'umea_marching_band_scores_{key}.csv')
    all_unique_urls.update(season_urls)

unique_urls_list = sorted(all_unique_urls)
#print(f'Unique URL List: {unique_urls_list}')
with open('umea_recap_guids.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    for item in unique_urls_list:
        writer.writerow([item])
"""
