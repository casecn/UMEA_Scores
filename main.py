from pathlib import Path
from typing import List

import pandas as pd

from recap.recap_page import (load_multiple_recaps, get_header_from_url,)

from recap.UMEA_api import (
    SEASON_GUID_DICT,
    collect_scores_and_round_guids,
)

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

BASE_RECAP_URL = "https://recaps.competitionsuite.com"
SCORES_CSV_PATH = Path("umea_marching_band_scores_all_seasons.csv")
ROUND_GUIDS_CSV_PATH = Path("umea_recap_guids.csv")
ALL_RECAPS_CSV_PATH = Path("umea_all_recaps.csv")


def build_recap_url(round_guids: List[str]) -> List[str]:
    """Turn a round GUID into a full recap URL."""
    return [f"{BASE_RECAP_URL}/{guid}.htm" for guid in round_guids]

def build_all_recaps_with_metadata(
        recap_urls: List[str], 
        scores_csv_path: Path,
  ) -> pd.DataFrame:
    """
    1) Load all recap tables (detail rows) from recap URLs.
    2) Load high-level scores/metadata from the UMEA_api CSV.
    3) Join on round_guid, adding season / competition / division metadata
    """
    # 1) Detail scores from recap pages
    header_cols = get_header_from_url(recap_urls[0])
    recap_df = load_multiple_recaps(recap_urls, header_cols=header_cols)
  
    # 2) High-Level scores and metadata from API
    scores_df = pd.read_csv(scores_csv_path)


    meta_cols = [
        'round_guid',
        'season_name',
        'competition_name',
        'competition_date',
        'competition_location',
        'division_name',
    ]

    meta_df = scores_df[meta_cols].drop_duplicates(subset='round_guid')

    # 4) Join detail rows with metadata
    final_df = recap_df.merge(meta_df, on='round_guid', how='left')

    return final_df

# -------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------


def main() -> None:
    # 1) Call UMEA_api helper:
    #    - writes SCORES_CSV_PATH (with the header you showed)
    #    - writes ROUND_GUIDS_CSV_PATH
    #    - returns the list of round GUIDs

    round_guid_list = collect_scores_and_round_guids(
        season_guid_dict=SEASON_GUID_DICT,
        scores_out_path=str(SCORES_CSV_PATH),
        round_guids_out_path=str(ROUND_GUIDS_CSV_PATH),
    )

    # 2) Build recap URLs from the round GUIDs
    recap_urls = build_recap_url(round_guid_list)

    header_cols = get_header_from_url(recap_urls[0])

    # 3)Build a single recap DataFrame with metadata
    all_recaps_df = build_all_recaps_with_metadata(
        recap_urls=recap_urls, 
        scores_csv_path=SCORES_CSV_PATH,
    )

    # 4 Write to disk
    all_recaps_df.to_csv(ALL_RECAPS_CSV_PATH, index=True)

if __name__ == "__main__":
    main()

"""


from recap.recap_page import RecapPage, load_recap
import recap.UMEA_api as UMEA_api
#from recap.UMEA_api import #collect_scores_and_round_guids, SEASON_GUID_DICT

                    
if __name__ == "__main__":
  round_guid_list = UMEA_api.collect_scores_and_round_guids(season_guid_dict=UMEA_api.SEASON_GUID_DICT, scores_out_path="umea_marching_band_scores_all_seasons.csv", round_guids_out_path="umea_recap_guids.csv") # or None if you don't care)
  #print(round_guid_list)
  for i, guid in enumerate(round_guid_list):
    #print(guid)
    url = f'https://recaps.competitionsuite.com/{guid}.htm'
    #print(f'URL: {url}')
    df = load_recap(url)
    #print(f'RECAP_DF: {df.head()}')    # preview
    df.to_csv(f'umea_recap_{i}.csv', index=True)

    
"""
