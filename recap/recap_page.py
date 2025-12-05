from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd

import requests
from bs4 import BeautifulSoup, Tag

#print("i'm in too")
@dataclass
class RecapHeader:
    division: str
    captions: List[str]
    sub_captions: List[str]
    judges: List[str]
    table_headers: List[str]          # raw headers from the HTML
    renamed_headers: List[str] = field(default_factory=list)  # optional processed version

class RecapPage:
    def __init__(self, url: str, table_index: int = 1):
        self.url = url
        self.table_index = table_index

        self._soup: Optional[BeautifulSoup] = None
        self._table: Optional[Tag] = None
        self._table_rows: List[Tag] = []

        self.header: Optional[RecapHeader] = None

    # ---------- Public API ----------

    def fetch(self) -> None:
        """Download the HTML and build the soup object."""
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
        """Parse division, captions, sub-captions, judges, and table headers."""
        if self._table is None or not self._table_rows:
            raise RuntimeError("Call fetch() before parse_header().")

        division = self._table_rows[0].get_text(strip=True)
        test = self._extract_row_text(6)
        #print(test)
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
        #####print(self.url, "------", self.header)
        return self.header
    #########################


    def parse_scores(self, first_data_row: int = 6) -> List[List[str]]:
        #print("First Row: ", first_data_row)
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

            if len(parsed) >= 3:
                data_rows.append(parsed)

        return data_rows


    def _parse_score_row(self, row: Tag) -> List[str]:
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
    """Transforms RecapHeader.table_headers using prefixes built from sub_captions."""

    def _build_prefix_list(self, sub_captions: List[str]) -> List[str]:
        """
        Build prefixes from each sub-caption.
        Example: "Music Ensemble" -> "MusEns"
                 "Visual Performance" -> "VisPer" (depending on your rules)
        Right now: take first 3 chars of each word and join them.
        """
        prefix_list: List[str] = []
        for text in sub_captions:
            words = text.split()
            first_chunks = [w[:3] for w in words if w]  # guard empty
            prefix = "".join(first_chunks)
            prefix_list.append(prefix)
        return prefix_list
    
    def update_header(self, header: RecapHeader) -> List[str]: #59 lines
        captions_list = header.captions

        # Build prefix_list from the header itself
        prefix_list = self._build_prefix_list(header.sub_captions)

        # copy so we don't trash the original
        table_header_list = list(header.table_headers)

        # (caption_index, prefix_index, num_columns, has sub_rank, has_caption_total)
        blocks = [
            (0, 0, 3, False),  # Music + MusEns
            (0, 1, 4, True),   # Music + MusEff
            (1, 2, 3, False),  # Visual + VisEns
            (1, 3, 4, True),   # Visual + VisEff
            (2, 4, 4, True),   # Percussion + Per
            (3, 5, 4, True),   # Color Guard + ColGua
            (5, 6, 2, False),   # Penalties + Pen
        ]
        #print(blocks)
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


            # 2) Add a rank for this judge block
            #if has_sub_rank: 
            #new_headers.append(f'{prefix}_rank')

            # 3) If this block ends in a caption total, rename it and add a caption rank
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

        return(new_headers)


@staticmethod
def load_recap(url: str) -> pd.DataFrame:
    page = RecapPage(url)
    page.fetch()

    # 1) parse header info from the table
    header = page.parse_header()

    # 2) transform header names
    transformer = TransformHeader()
    renamed_headers = transformer.update_header(header)
    header.renamed_headers = renamed_headers  # optional, for later reuse

     # 3) parse data rows (scores)
    rows = page.parse_scores(first_data_row=6)

    # 4) zip headers + row values into records
    records: List[dict] = []
    for row_values in rows:
        if len(row_values) != len(renamed_headers):
            # 1. Log URL
            with open("mismatched_header.txt", "a") as file:
                file.write(f'\n{url}')

            # 2. Truncate the row_values list to match renamed_headers list

            # 3 Proceed
            # This is where you want to catch structural mismatches early
            """raise ValueError(
                f"Header/data length mismatch: {len(renamed_headers)} headers vs "
                f"{len(row_values)} values"

            )
            """
            records.append(dict(zip(renamed_headers, row_values)))
            # print(records)
        df = pd.DataFrame.from_records(records)

        return df
    
    @staticmethod
    def load_multiple_recaps(urls: List[str]) -> pd.DataFrame:
        df_list = []
        for url in urls:
            df = RecapPage.load_recap(url)
            df = df.copy()
            df["source_url"] = url
            df_list.append(df)

        if not df_list:
            return pd.DataFrame()

        return pd.concat(df_list, ignore_index=True)
