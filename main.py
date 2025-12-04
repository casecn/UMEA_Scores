# main.py
from recap.recap_page import RecapPage

from recap.UMEA_api import collect_scores_and_round_guids, SEASON_GUID_DICT

                    
if __name__ == "__main__":
  round_guid_list = collect_scores_and_round_guids(season_guid_dict=SEASON_GUID_DICT, scores_out_path="umea_marching_band_scores_all_seasons.csv", round_guids_out_path="umea_recap_guids.csv") # or None if you don't care)

  for i, guid in enumerate(round_guid_list):
    #print(guid)
    url = f'https://recaps.competitionsuite.com/{guid}.htm'
    df = RecapPage.load_recap(url)
    #print(df.head())    # preview
    df.to_csv(f'umea_recap_{i}.csv', index=True)

    
