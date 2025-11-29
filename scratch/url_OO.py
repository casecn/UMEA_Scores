from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup, Tag


@dataclass
class RecapHeader:
    division: str
    captions: List[str]
    sub_captions: List[str]
    judges: List[str]
    table_headers: List[str]


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




url = "https://recaps.competitionsuite.com/7bd6b6ad-a3be-4b9f-8be6-de516f452b95.htm"

recap = RecapPage(url)
recap.fetch()
header = recap.parse_header()

print(header.division)
print(header.captions)
print(header.sub_captions)
print(header.judges)
print(header.table_headers)
