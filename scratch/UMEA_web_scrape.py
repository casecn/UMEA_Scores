# Gathering marching band score data

import csv
import requests
import re
from bs4 import BeautifulSoup
import json

BASE = "https://bridge.competitionsuite.com/api/orgscores"
VERSION = "1.1.5"
CALLBACK = "jQuery110209904385531594735_1763353270252?_= 1763353270271"


def get_jsonp(url, params=None, timeout=10):
    """
    Call a JSONP endpoint and return parsed JSON.
    Assumes response looks like: callback123({...});
    """
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    raw = resp.text

    # Find first "(" and last ")"
    start = raw.find("(")
    end = raw.rfind(")")

    if start == -1 or end == -1:
        raise ValueError("Response is not valid JSONP")

    json_str = raw[start+1:end]
    return json.loads(json_str)


def get_competitions_for_season(season_id):
    url = f"{BASE}/GetCompetitionsBySeason/jsonp"
    params = {
        "season": season_id,
        "showTrainingEvents": "false",
        "version": VERSION,
        "callback": CALLBACK  # usually not needed; server supplies default
    }

    data = get_jsonp(url, params=params)

    # At this point you need to inspect the structure once:
    print(data.keys())
    # print(json.dumps(data, indent=2)[:1000])

    # I'm going to *guess* competitions live under "Competitions" or "competitions"
    competitions = data.get("Competitions") or data.get("competitions")
    if competitions is None:
        raise KeyError("Cannot find competitions list in API response")

    return competitions


def get_competition_results(comp_id):
    url = f"{BASE}/GetCompetition/jsonp"
#/GetCompetition/jsonp?competition = c172b001-d1b4-4b36-819a-eb54424da634 & version = 1.1.5 & callback = jQuery110209904385531594735_1763353270252 & _ = 1763353270274


#https://bridge.competitionsuite.com/api/orgscores"
#https://bridge.competitionsuite.com/api/orgscores/GetCompetition/jsonp?competition=c172b001-d1b4-4b36-819a-eb54424da634&version=1.1.5&callback=jQuery110209904385531594735_1763353270252&_=1763353270274
    params = {
        "competition": comp_id,
        "version": VERSION,
        "callback": "jQuery110209904385531594735_1763353270252&_=1763353270274"
    }

    data = get_jsonp(url, params=params)

    # Again, inspect once to see structure:
    # print(data.keys())
    # print(json.dumps(data, indent=2)[:1500])

    return data


def flatten_competition_results(comp_data, season_name=None):
    """
    Turn one competition's JSON (like the sample you provided)
    into a list of flat row dicts: one row per performance.

    comp_data: dict parsed from the CompetitionSuite JSON/JSONP.
    season_name: optional human-readable season label you can pass in
                 (e.g. "2023 UMEA Marching Band").
    """

    rows = []

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
        category_recap_url = rnd.get("categoryRecapUrl")

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
                "competition_recap_url": recap_url,

                "division_guid": division_guid,
                "division_name": division_name,
                "round_guid": round_guid,
                "round_full_recap_url": full_recap_url,
                "round_category_recap_url": category_recap_url,

                "performance_guid": performance_guid,
                "band_name": band_name,
                "city": city,
                "state": state,
                "score": score,
                "rank": rank,
            }

            rows.append(row)

    return rows


def build_scores_csv(season_id, season_name, out_path):
    competitions = get_competitions_for_season(season_id)
    print(competitions)
    all_rows = []

    for c in competitions:
        comp_id = c.get("competitionGuid") #or c.get("CompetitionId")
        comp_name = c.get("name") #or c.get("CompetitionName")

        print(f"Fetching competition: {comp_name} ({comp_id})")

        comp_data = get_competition_results(comp_id)

        rows = flatten_competition_results(
            comp_data=comp_data,
            season_name=season_name
        )
        all_rows.extend(rows)

    if not all_rows:
        print("No rows collected, nothing to write.")
        return

    fieldnames = list(all_rows[0].keys())

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {out_path}")

season_id = "6d7e8a01-34fb-49c0-bfab-8b62c8f19930"
#comps = get_competitions_for_season(season_id)
#print(len(comps))
#print(comps[6])
season_name = "2024 Utah Marching Band"  # or whatever is appropriate

build_scores_csv(season_id, season_name, "umea_marching_band_scores.csv")




#Get a list of all the GUIDs as event_id

#for each year
#Hit the API for each event
#Parse the response
#call the detailed scores table
#parse and store the scores table