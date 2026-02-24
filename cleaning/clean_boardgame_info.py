import re
from typing import Optional, cast

from backend.database.db import get_db_session
from backend.repositories.raw_data_repository import RawDataRepository
from backend.repositories.scrape_task_repository import ScrapeTaskRepository
from backend.repositories.clean_data_repository import CleanDataRepository
from backend.utils import model_list_to_dataframe
from backend.database.schemas import CleanDataIn

PROCESSOR_VERSION = "1.0"


def clean_field_name(name: str) -> str:
    return name.replace(".", "").replace(" ", "_").lower()


def clean_int(value: Optional[str | int]) -> Optional[int]:
    if isinstance(value, int):
        return value

    if value is None or value == "" or value.lower() == "n/a":
        return None

    pattern = r"([\d,]+)"
    match = re.search(pattern, value)
    if not match:
        return None

    return int(match.group(1).replace(",", "").strip())


def clean_str(value: Optional[str]) -> Optional[str]:
    if value is None or value == "" or value.lower() == "n/a":
        return None

    return value.strip()


def clean_str_list(value: Optional[str]) -> Optional[list[str]]:
    if value is None or value == "" or value.lower() == "n/a":
        return None

    return [item.strip() for item in value.split("\n") if item.strip() != ""]


def clean_float(value: Optional[str | float]) -> Optional[float]:
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)

    if value is None or value == "" or value.lower() == "n/a":
        return None

    pattern = r"([\d.]+)"

    match = re.search(pattern, value.strip())
    if not match:
        return None

    return float(match.group(1).replace(",", "."))


def parse_player_counts(value: Optional[str]) -> Optional[dict[str, int]]:
    if value is None or value == "" or value.lower() == "n/a":
        return None

    pattern = r"([\w]+[\w ]+):? (?:\(no votes\) )?(\d+)[-–](\d+)"
    matches = re.findall(pattern, value)
    if not matches:
        return None

    result: dict = {}
    for typ, min_s, max_s in matches:
        if typ.lower() == "best":
            typ = "best_player_count"
        elif typ.lower() == "players community":
            typ = "community_player_count"
        elif typ.lower() == "number of players":
            typ = "official_player_count"

        result[f"{typ.strip()}_min"] = int(min_s)
        result[f"{typ.strip()}_max"] = int(max_s)

    return result


def parse_price_and_store(value: Optional[str]) -> Optional[tuple[float, str]]:
    if value is None or value == "" or value.lower() == "n/a":
        return None

    pattern = r"(?:from )?((?:CA)?\$|£|€|C\$|Fr\.|CHF) ?([\d.]+)(?: [-–] )(.+)"
    match = re.search(pattern, value.strip())
    if not match:
        return None

    currency = match.group(1).replace(" ", "").strip()
    amount = clean_float(match.group(2))

    conversion_rates = {
        "$": 1.0,
        "CA$": 0.73,
        "£": 1.35,
        "€": 1.18,
        "Fr.": 0.17,
        "CHF": 1.29,
    }

    if currency not in conversion_rates:
        return None

    if amount is None:
        return None

    store = match.group(3).strip()
    if store is None or store == "":
        return None

    return (round(amount * conversion_rates[currency], 3), store)


def parse_dimension_to_volume(value: Optional[str]) -> Optional[float]:
    if value is None or value == "" or value.lower() == "n/a":
        return None

    pattern = r"(\d+(?:\.\d+)?) x (\d+(?:\.\d+)?) x (\d+(?:\.\d+)?) cm"
    match = re.search(pattern, value.strip())
    if not match:
        return None

    length = clean_float(match.group(1))
    width = clean_float(match.group(2))
    height = clean_float(match.group(3))

    if length is None or width is None or height is None:
        return None

    return round(length * width * height, 3)


def clean_boardgame_info():
    with get_db_session() as session:
        task = ScrapeTaskRepository.get_latest_completed_task_by_name(
            session, name="scrape_boardgames_info"
        )

        if task is None:
            print("No completed task found")
            return

        raw_data = RawDataRepository.get_by_scrape_task_id(session, task.id)

    for raw in raw_data:
        cleaned_data = {}

        int_fields = [
            "id",
            "Own",
            "Fans",
            # "year",
            "Year Released",
            "Comments",
            "Wishlist",
            "Page Views",
            "This Month",
            "Prev. Owned",
            "Overall Rank",
            "Thematic Rank",
            "All Time Plays",
            "No. of Ratings",
            "For Trade",
            "Has Parts",
            "Want Parts",
            "Want In Trade",
        ]
        for field_name in int_fields:
            cleaned_field_name = clean_field_name(field_name)
            cleaned_value = clean_int(raw.payload.get(field_name))
            cleaned_data[cleaned_field_name] = cleaned_value

        float_fields = ["Weight", "Avg. Rating", "Std. Deviation"]
        for field_name in float_fields:
            cleaned_field_name = clean_field_name(field_name)
            cleaned_value = clean_float(raw.payload.get(field_name))
            cleaned_data[cleaned_field_name] = cleaned_value

        str_fields = [
            "name",
            "url",
            "Editor",
            "Writer",
            "Designer",
            "Primary Name",
            "Solo Designer",
            "Insert Designer",
        ]
        for field_name in str_fields:
            cleaned_field_name = clean_field_name(field_name)
            cleaned_value = clean_str(raw.payload.get(field_name))
            cleaned_data[cleaned_field_name] = cleaned_value

        str_list_fields = [
            "Artists",
            "Sculptors",
            "Categories",
            "Developers",
            "Mechanics",
            "Publishers",
            "Alternate Names",
            "Graphic Designers",
            "Mechanisms",
            "Family",
        ]
        for field_name in str_list_fields:
            cleaned_field_name = clean_field_name(field_name)
            cleaned_value = clean_str_list(raw.payload.get(field_name))
            cleaned_data[cleaned_field_name] = cleaned_value

        # parse player counts
        player_counts_raw = raw.payload.get("player_counts")
        parsed_player_counts = parse_player_counts(player_counts_raw)
        if parsed_player_counts is not None:
            for key, value in parsed_player_counts.items():
                cleaned_data[key] = value

        # parse prices (and convert to USD)
        cleaned_prices = {}
        for raw_price in raw.payload.get("prices", []):
            parsed_price = parse_price_and_store(raw_price)
            if parsed_price is not None:
                cleaned_prices[parsed_price[1]] = parsed_price[0]
        cleaned_data["prices"] = cleaned_prices

        # parse dimensions
        volumes = []
        for dim in raw.payload.get("dimensions", []):
            volume = parse_dimension_to_volume(dim)
            if volume is not None:
                volumes.append(volume)

        cleaned_data["volumes_cm3"] = volumes

        # persist cleaned data and mark raw as processed
        clean_in = CleanDataIn(
            source_table=raw.source_table,
            source_id=raw.source_id,
            scrape_task_id=raw.scrape_task_id,
            payload=cleaned_data,
            processor_version=PROCESSOR_VERSION,
        )

        with get_db_session() as session:
            try:
                CleanDataRepository.create(session, clean_in, raw_id=raw.id)
                RawDataRepository.mark_processed(
                    session,
                    raw.id,

                    processor_version=PROCESSOR_VERSION,
                )

                print(f"Cleaned boardgame '{cleaned_data.get('name')}' (id: {cleaned_data.get('id')}) with {len(cleaned_data)} fields")
            except Exception as exc:
                RawDataRepository.mark_processed(
                    session, raw.id, processed=False, error=str(exc)
                )

    print("Boardgame cleaning complete")
