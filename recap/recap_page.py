from dataclasses import dataclass, field
from typing import List, Optional

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
        response = requests.get(self.url)
        response.raise_for_status()

        self._soup = BeautifulSoup(response.text, "html.parser")
        self._set_table_of_interest()

    def parse_header(self) -> RecapHeader:
        """Parse division, captions, sub-captions, judges, and table headers."""
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

    def apply(self, header: RecapHeader) -> List[str]:
        """
        Use sub_captions to build prefix_list, then apply your header renaming logic.
        Mutates header.renamed_headers and returns the new list.
        """
        if not header.sub_captions:
            raise ValueError(
                "Header must have sub_captions before transformation.")

        captions_list = header.captions
        # copy so we don't trash the original
        table_header_list = list(header.table_headers)

        # Build prefix_list from the header itself
        prefix_list = self._build_prefix_list(header.sub_captions)

        # ---------- Your existing renaming logic using prefix_list + captions_list ----------

        # Music Caption
        table_header_list[0] = f'{prefix_list[0]}_{table_header_list[0]}'
        table_header_list[1] = f'{prefix_list[0]}_{table_header_list[1]}'
        table_header_list[2] = f'{prefix_list[0]}_{table_header_list[2]}'

        table_header_list.insert(3, f'{prefix_list[0]}_rank')

        table_header_list[4] = f'{prefix_list[1]}_{table_header_list[4]}'
        table_header_list[5] = f'{prefix_list[1]}_{table_header_list[5]}'
        table_header_list[6] = f'{prefix_list[1]}_{table_header_list[6]}'

        table_header_list.insert(7, f'{prefix_list[1]}_rank')

        table_header_list[8] = f'{captions_list[0]}_{table_header_list[8]}al'
        table_header_list.insert(9, f'{captions_list[0]}_rank')

        # Music Effect Caption
        table_header_list[10] = f'{prefix_list[2]}_{table_header_list[10]}'
        table_header_list[11] = f'{prefix_list[2]}_{table_header_list[11]}'
        table_header_list[12] = f'{prefix_list[2]}_{table_header_list[12]}'

        table_header_list.insert(13, f'{prefix_list[2]}_rank')

        table_header_list[14] = f'{prefix_list[3]}_{table_header_list[14]}'
        table_header_list[15] = f'{prefix_list[3]}_{table_header_list[15]}'
        table_header_list[16] = f'{prefix_list[3]}_{table_header_list[16]}'

        table_header_list.insert(17, f'{prefix_list[3]}_rank')

        table_header_list[18] = f'{captions_list[1]}_{table_header_list[18]}al'
        table_header_list.insert(19, f'{captions_list[1]}_rank')

        # Percussion Caption
        table_header_list[20] = f'{prefix_list[4]}_{table_header_list[20]}'
        table_header_list[21] = f'{prefix_list[4]}_{table_header_list[21]}'
        table_header_list[22] = f'{prefix_list[4]}_{table_header_list[22]}'

        table_header_list[23] = f'{captions_list[2]}_{table_header_list[23]}al'
        table_header_list.insert(24, f'{captions_list[2]}_rank')

        # Color Guard Caption
        table_header_list[25] = f'{prefix_list[5]}_{table_header_list[25]}'
        table_header_list[26] = f'{prefix_list[5]}_{table_header_list[26]}'
        table_header_list[27] = f'{prefix_list[5]}_{table_header_list[27]}'

        table_header_list[28] = f'{captions_list[3]}_{table_header_list[28]}al'
        table_header_list.insert(29, f'{captions_list[3]}_rank')

        # Sub Total
        table_header_list.insert(30, captions_list[4])
        table_header_list.insert(31, f'{captions_list[4]}_rank')

        # Penalty
        table_header_list[32] = f'{prefix_list[6]}_{table_header_list[32]}'
        table_header_list[33] = f'{captions_list[5]}_{table_header_list[33]}al'

        # Final total + rank
        table_header_list.append('Total')
        table_header_list.append('Rank')

        # Save result on header and return it
        header.renamed_headers = table_header_list
        return table_header_list
