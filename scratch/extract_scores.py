from typing import List


def parse_score_row(row) -> List[str]:
    """
    Given a <tr> for a band, return:
    [school, city_state, score1, rank1, score2, rank2, ...]
    """
    # Only the top-level <td> in the row
    outer_cells = row.find_all("td", recursive=False)

    if len(outer_cells) < 3:
        raise ValueError(
            "Unexpected row structure, not enough top-level cells.")

    school = outer_cells[0].get_text(strip=True)
    city_state = outer_cells[1].get_text(strip=True)

    values: List[str] = [school, city_state]

    # The rest of the cells are score / rank blocks
    for cell in outer_cells[2:]:
        score_td = cell.find("td", class_="content score")
        rank_td = cell.find("td", class_="content rank")

        if score_td and rank_td:
            # Prefer the precise numeric value if present
            score = score_td.get(
                "data-translate-number") or score_td.get_text(strip=True)
            rank = rank_td.get_text(strip=True)
            values.extend([score, rank])
        else:
            # fallback if structure is weird; you can tighten or remove this once you’re sure
            text = cell.get_text(strip=True)
            if text:
                values.append(text)

    return values
