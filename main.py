from pathlib import Path

from recap.recap_page import RecapPage, load_multiple_recaps
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


def build_recap_url(round_guid: str) -> str:
    """Turn a round GUID into a full recap URL."""
    return f"{BASE_RECAP_URL}/{round_guid}.htm"


def main() -> None:
    # ---------------------------------------------------------------
    # 1. Get high-level scores + unique round GUIDs from the API
    # ---------------------------------------------------------------
    round_guid_list = collect_scores_and_round_guids(
        season_guid_dict=SEASON_GUID_DICT,
        scores_out_path=str(SCORES_CSV_PATH),
        round_guids_out_path=str(ROUND_GUIDS_CSV_PATH),
    )

    if not round_guid_list:
        print("No round GUIDs returned; stopping.")
        return

    print(f"Collected {len(round_guid_list)} unique round GUIDs.")

    # ---------------------------------------------------------------
    # 2. Build recap URLs from GUIDs
    # ---------------------------------------------------------------
    recap_urls = [build_recap_url(guid) for guid in round_guid_list]
    print(f"Built {len(recap_urls)} recap URLs.")

    # ---------------------------------------------------------------
    # 3. Load ALL recap pages into a single DataFrame
    # ---------------------------------------------------------------
    # Assumes RecapPage.load_multiple_recaps(urls: list[str]) -> pd.DataFrame
    df_all_recaps = load_multiple_recaps(recap_urls)

    if df_all_recaps is None or df_all_recaps.empty:
        print("No recap rows parsed; nothing to write.")
        return

    print(
        f"Loaded {len(df_all_recaps)} recap rows from {len(recap_urls)} pages.")

    # ---------------------------------------------------------------
    # 4. Save combined recap DataFrame to one CSV
    # ---------------------------------------------------------------
    df_all_recaps.to_csv(ALL_RECAPS_CSV_PATH, index=False)
    print(f"Wrote combined recap data to '{ALL_RECAPS_CSV_PATH}'.")


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
