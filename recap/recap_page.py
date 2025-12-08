from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

CITY_DICT = {'American Fork': 'American Fork, UT', 'Viewmont': 'Bountiful, UT', 'Gallatin': 'Bozeman, MT', 'Canyon View': 'Cedar City, UT', 'Clearfield': 'Clearfield, UT', 'Brighton': 'Cottonwood Heights, UT', 'Delta': 'Delta, UT', 'Cedar Valley': 'Eagle Mountain, UT', 'Elko': 'Elko, NV', 'Tintic': 'Eureka, UT', 'Farmington': 'Farmington, UT', 'Bear River': 'Garland, UT', 'Wasatch': 'Heber City, UT', 'Herriman': 'Herriman, UT', 'Mountain Ridge': 'Herriman, UT', 'Lone Peak': 'Highland, UT', 'Mountain Crest': 'Hyrum, UT', 'Davis': 'Kaysville, UT', 'Kearns': 'Kearns, UT', 'Lehi': 'Lehi, UT', 'Skyridge': 'Lehi, UT', 'Hillcrest': 'Midvale, UT', 'Ridgeline': 'Millville, UT', 'Green Canyon': 'North Logan, UT', 'Ogden': 'Ogden, UT', 'Orem': 'Orem, UT', 'Timpanogos': 'Orem, UT', 'Payson': 'Payson, UT', 'Pleasant Grove': 'Pleasant Grove, UT', 'Carbon': 'Price, UT', 'Provo': 'Provo, UT', 'Timpview': 'Provo, UT', 'Riverton': 'Riverton, UT',
             'Salem Hills': 'Salem, UT', 'Alta': 'Sandy, UT', 'Westlake': 'Saratoga Springs, UT', 'Sky View': 'Smithfield, UT', 'Bingham': 'South Jordan, UT', 'Mountain Star': 'South Ogden, UT', 'Maple Mountain': 'Spanish Fork, UT', 'Spanish Fork': 'Spanish Fork, UT', 'Springville': 'Springville, UT', 'Stansbury': 'Stansbury, UT', 'Deseret Peak': 'Tooele, UT', 'Tooele': 'Tooele, UT', 'Uintah': 'Vernal, UT', 'Copper Hills': 'West Jordan, UT', 'West Jordan': 'West Jordan, UT', 'High Desert': 'Ammon, ID', 'Nampa': 'Nampa ID', 'Idaho Falls': 'Idaho Falls, ID', 'Columbia': 'Nampa, ID', 'Skyview (ID)': 'Nampa ID', 'Century': 'Pocatello, ID', 'Pocatello': 'Pocatello, ID', 'Timberline': 'Boise, ID', 'Madison': 'Rexburg, ID', 'Highland': 'Pocatello, ID', 'Orem City': 'Orem, UT', 'Grand County': 'Moab, UT', 'Roy': 'Roy, UT', 'Murray': 'Murray, UT', 'Fremont': 'Plain City, UT', 'Mountain View': 'Meridian, ID', 'Capital': 'Boise, ID', 'Fruitland': 'Fruitland, ID', 'Kelly Walsh': 'Casper, WY', 'Blackfoot': 'Blackfoot, ID', 'Centennial': 'Boise, ID'}

@dataclass
class RecapHeader:
    '''A simple data container that stores the header information extracted from a recap table. It holds the division name, caption lists, judge names, and raw table headers, along with an optional list of renamed headers. Depends on List from typing and field from dataclasses.'''
    division: str
    captions: List[str]
    sub_captions: List[str]
    judges: List[str]
    table_headers: List[str]          # raw headers from the HTML
    renamed_headers: List[str] = field(default_factory=list)  # optional processed version

class RecapPage:
    '''Represents a single recap webpage. Handles downloading HTML, finding the relevant table, parsing header info, and extracting score rows. Depends on BeautifulSoup, Tag, RecapHeader, List, Optional.'''
    def __init__(self, url: str, table_index: int = 1):
        '''Stores the recap URL and which table to parse, and initializes placeholders for soup, table, rows, and header. Depends on type hints: str, int, Optional, List, RecapHeader.'''
        self.url = url
        self.table_index = table_index

        self._soup: Optional[BeautifulSoup] = None
        self._table: Optional[Tag] = None
        self._table_rows: List[Tag] = []

        self.header: Optional[RecapHeader] = None

    # ---------- Public API ----------

    def fetch(self) -> None:
        '''Sends an HTTP GET request to self.url, builds a BeautifulSoup object from the HTML, and locates the target table. Depends on requests, BeautifulSoup, and _set_table_of_interest.'''
        try:
            response = requests.get(self.url)
            #response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f'Caught a 403 Forbidden error: {e}')
                # Handle the 403 error specifically (e.g., inform the user, log the event)
            else:
                print(f"Caught another HTTP error: {e}")

        self._soup = BeautifulSoup(response.text, "html.parser")
        self._set_table_of_interest()

    def parse_header(self) -> RecapHeader:
        '''Extracts division name, captions, sub-captions, judges, and raw table headers from specific table rows, then builds and stores a RecapHeader. Depends on _extract_row_text, _table_rows, and RecapHeader.'''

        if self._table is None or not self._table_rows:
            raise RuntimeError("Call fetch() before parse_header().")

        division = self._table_rows[0].get_text(strip=True)
        
        captions = self._extract_row_text(2)
        sub_captions = self._extract_row_text(3)
        judges = self._extract_row_text(4)
        table_headers = self._extract_row_text(5)

        self.header = RecapHeader(
            division=division,
            captions=captions,
            sub_captions=sub_captions,
            judges=judges,
            table_headers=table_headers,
        )

        return self.header
    #########################




    def parse_scores(self, first_data_row: int = 6) -> List[List[str]]:
        '''Iterates over data rows starting at first_data_row, parses each with _parse_score_row, and returns a list of score rows. Skips rows with too few <td> cells. Depends on _table_rows, _parse_score_row, List.'''
        
        if self._table is None or not self._table_rows:
            raise RuntimeError("Call fetch() before parse_scores().")

        data_rows: List[List[str]] = []

        for idx, row in enumerate(self._table_rows[first_data_row:], start=first_data_row):
            # Look only at top-level cells, same as _parse_score_row
            outer_cells = row.find_all("td", recursive=False)
            
            # Skip rows that don't have at least school + city/state
            if len(outer_cells) < 2:
                # Optional debug:
                # print(f"Skipping row {idx}: only {len(outer_cells)} top-level <td> cells")
                continue

            parsed = self._parse_score_row(row)



            def is_number(value: str) -> bool:
                try:
                    float(value)
                    return True
                except ValueError:
                    return False
                
            if is_number(parsed[1]):
                parsed.insert(1, CITY_DICT[parsed[0]])
                parsed.insert(2, parsed[2][:2])
                parsed[3] = parsed[3][-1]
            
            if len(parsed) >= 3:
                data_rows.append(parsed)
        return data_rows


    def _parse_score_row(self, row: Tag) -> List[str]:
        '''Pulls school and city/state from the first two <td> cells, then extracts score/rank pairs from nested cells using class names "content score" and "content rank". Depends on Tag, List, and BeautifulSoup’s find/get_text.'''
        outer_cells = row.find_all("td", recursive=False)

        school = outer_cells[0].get_text(strip=True)
        city_state = outer_cells[1].get_text(strip=True)

        values: List[str] = [school, city_state]

        for cell in outer_cells[2:]:
            score_td = cell.find("td", class_="content score")
            rank_td = cell.find("td", class_="content rank")

            if score_td and rank_td:
                score = score_td.get(
                    "data-translate-number") or score_td.get_text(strip=True)
                rank = rank_td.get_text(strip=True)
                values.extend([score, rank])
            else:
                text = cell.get_text(strip=True)
                if text:
                    values.append(text)
        return values

########################################

    # ---------- Internal helpers ----------

    def _set_table_of_interest(self) -> None:
        '''using soup, this functin finds all <table> elements in the soup and selects the one at self.table_index. Also caches its <tr> rows. Raises errors if soup isn’t initialized or index is invalid. Depends on BeautifulSoup, Tag, List.'''
        if self._soup is None:
            raise RuntimeError("Soup has not been created yet.")

        tables = self._soup.find_all("table")
        try:
            self._table = tables[self.table_index]
        except IndexError:
            raise ValueError(
                f"Could not find table at index {self.table_index}. "
                f"Found only {len(tables)} table(s)."
            )

        self._table_rows = self._table.find_all("tr")

    def _extract_row_text(self, row_index: int) -> List[str]:
        '''Retrieves the row at row_index, grabs text from all th/td cells, strips whitespace, and filters out empties. Used for headers and metadata. Depends on _table_rows, Tag, and list comprehension.'''
        """Return non-empty cell texts from a given row index."""
        try:
            row = self._table_rows[row_index]
        except IndexError:
            raise ValueError(
                f"Row index {row_index} out of range for this table.")

        texts = [
            cell.get_text(strip=True)
            for cell in row.find_all(["th", "td"])
            ]
        # filter out empty values
        return [t for t in texts if t]
    
class TransformHeader:
    '''Builds standardized column names for recap score tables. It generates prefixes from sub-captions and rewrites raw headers into structured score/rank fields.'''

    def _build_prefix_list(self, sub_captions: List[str]) -> List[str]:
        '''Creates short prefixes by taking the first three characters of each word in a sub-caption. Depends on List.
        
        Build prefixes from each sub-caption.
        Example: "Music Ensemble" -> "MusEns"
                 "Visual Performance" -> "VisPer" (depending on your rules)
        Right now: take first 3 chars of each word and join them.
        '''
        prefix_list: List[str] = []
        for text in sub_captions:
            words = text.split()
            first_chunks = [w[:3] for w in words if w]  # guard empty
            prefix = "".join(first_chunks)
            prefix_list.append(prefix)
        return prefix_list

    def update_header(self, header: RecapHeader) -> List[str]:
        '''Rebuilds all table headers using captions, prefixes, and fixed block rules. Outputs renamed, structured headers for downstream DataFrame use. Depends on RecapHeader, _build_prefix_list, and string/list operations.'''
        captions_list = header.captions

        # Build prefix_list from the header itself
        prefix_list = self._build_prefix_list(header.sub_captions)

        # copy so we don't trash the original
        table_header_list = list(header.table_headers)

        # (caption_index, prefix_index, num_columns, has_caption_total)
        blocks = [
            (0, 0, 3, False),  # Music + MusEns
            (0, 1, 4, True),   # Music + MusEff
            (1, 2, 3, False),  # Visual + VisEns
            (1, 3, 4, True),   # Visual + VisEff
            (2, 4, 4, True),   # Percussion + Per
            (3, 5, 4, True),   # Color Guard + ColGua
            #(5, 6, 2, False),   # Penalties + Pen
        ]

        new_headers = []
        idx = 0  # pointer into table_header_list

        for cap_idx, pre_idx, n_cols, has_caption_total in blocks:
            caption = captions_list[cap_idx]
            prefix = prefix_list[pre_idx]

            # Take the next n_cols raw headers for this block
            cols = table_header_list[idx:idx + n_cols]
            idx += n_cols #resetting current index

            # If the block has a caption total, treat the last column as total
            if has_caption_total:
                judge_cols = cols[:-1]
                
                total_col = cols[-1]
            else:
                judge_cols = cols
                total_col = None

            # 1) Prefix judge columns: MusEns_Musc, MusEns_Tech, MusEns_*Tot, etc.
            for c in judge_cols:
                new_headers.append(f'{prefix}_{c}_score')
                new_headers.append(f'{prefix}_{c}_rank')

            # 2) If this block ends in a caption total, rename it and add a caption rank
            if total_col is not None:
                # e.g. "Music_Total" (you were adding 'al' at the end, so mirror that)
                new_headers.append(f'{caption}_{total_col}al')
                new_headers.append(f'{caption}_Rank')

        # Global totals and subtotals at the very end
        new_headers.insert(0,'city/state')
        new_headers.insert(0, 'school')

        new_headers.append('SubTotal')
        new_headers.append('SubTotal_Rank')
        new_headers.append('Penalties')
        new_headers.append('SPACER')
        new_headers.append('Penalties_Total')
        new_headers.append('SPACER')
        new_headers.append('Total')
        new_headers.append('Rank')
       # '''

        return(new_headers)


@staticmethod
def load_recap(url: str, header_cols) -> pd.DataFrame:
    """
    load_recap fetches the recap webpage, parses its scoring table, and returns the results as a clean pandas DataFrame.
    """
    page = RecapPage(url)
    page.fetch()

    # 1) parse header info from the table
    header = page.parse_header()

    # 2) transform header names
    # If header cols wasn't provided, fall back to parsing  each url
    renamed_headers: List[dict] = []
    if header_cols is None:
        transformer = TransformHeader()
        renamed_headers = transformer.update_header(header)
        header.renamed_headers = renamed_headers  # optional, for later reuse

     # 3) parse data rows (scores)
    rows = page.parse_scores(first_data_row=6)

    # 4) zip headers + row values into records
    records1: List[dict] = []
    for row_values in rows:
        if len(row_values) != len(renamed_headers):
            with open("mismatched_header.txt", "a") as file:
                file.write(f'\n{url}')

        # Combine using dictionary comprehension
        record_dict = {header_cols[i]: row_values[i] for i in range(len(header_cols))}

        records1.append(record_dict)
        df = pd.DataFrame.from_records(records1, columns=header_cols)

        # Add round_guid so we can join with UMEA_api metadata later
        guid = url.rstrip("/").split("/")[-1]
        if guid.endswith(".htm"):
            guid = guid[:-4]
        df["round_guid"] = guid
    return df
    
@staticmethod
def load_multiple_recaps(urls: List[str], header_cols: List[str]) -> pd.DataFrame:
        '''
        load_multiple_recaps takes a list of recap URLs, loads each one with load_recap, and combines all resulting DataFrames into a single DataFrame. It handles multiple recaps at once, stitching them into one unified table so you don't process or analyze each recap separately.'''
        df_list: list[pd.DataFrame] = []
        for url in urls:
            df = load_recap(url, header_cols=header_cols)
            df["source_url"] = url
            df_list.append(df)
        if not df_list:
            return pd.DataFrame()

        return pd.concat(df_list, ignore_index=True)

def get_header_from_url(url: str) -> List[str]:
    page = RecapPage(url)
    page.fetch()

    header = page.parse_header()

    transformer = TransformHeader()
    renamed = transformer.update_header(header)

    return renamed