from typing import cast

from backend.database.db import get_db_session
from backend.logger import ScrapeTaskLogger
from backend.repositories import BoardGameRepository, ScrapeTaskRepository
from backend.database.schemas import BoardGameIn, RawDataIn
from backend.repositories.raw_repository import RawRepository
from scraping.camoufox_wrapper import CamoufoxWrapper
from scraping.page_wrapper import PageWrapper


def login(page: PageWrapper, logger: ScrapeTaskLogger) -> bool:
    page.goto("https://www.boardgamegeek.com/login")

    # if page.exists('div[role="alert"]', has_text="You are already logged in"):
    #     print("Already logged in (alert detected)")
    #     return True

    if not page.exists("gg-login-page"):
        logger.fail("Login page not found")
        return False

    # agree to cookies if banner is present
    if page.click("button", has_text="I'm OK with that"):
        # cookie agree might trigger a page reload, so wait for network to be idle again
        page.wait_for_idle(timeout=10000)

    page.sleep_random(2000, 5000)

    logged_in = page.login(
        username_selector="input#inputUsername",
        password_selector="input#inputPassword",
        submit_selector="button.btn-primary",
        username="olehax",
        password="F**f43M58NfwV7%4F!#8J",
    )

    if not page.exists("gg-avatar-letter > span", has_text="O"):
        logger.fail("Login verification failed: Avatar not found")
        return False

    page.sleep(3000)

    # if page.exists("div", has_text="There was a problem with your request."):
    #     logger.fail("Login verification failed: Request error detected")
    #     return False

    # page.sleep(100000)

    return logged_in


def scrape_boardgames_info(log_to_console: bool = True):
    with ScrapeTaskLogger(
        task_name="scrape_boardgames_info", log_to_console=log_to_console
    ) as logger:
        logger.log("Started")

        boardgames = []
        with get_db_session() as session:
            boardgames = BoardGameRepository.get_all(session)

        if len(boardgames) == 0:
            logger.fail("No boardgames found in database, aborting scrape")
            return

        boardgames = boardgames[:20]

        items_processed = 0

        with CamoufoxWrapper().start_browser() as browser:
            page = browser.new_page(logger)

            logged_in = login(page, logger)
            if not logged_in:
                logger.fail("Login failed")
                return

            logger.log("Login successful")

            for i, boardgame in enumerate(boardgames):
                raw_game_data = {
                    "id": boardgame.id,
                    "name": boardgame.name,
                    "url": boardgame.url,
                }

                boardgame_url = f"https://boardgamegeek.com{boardgame.url}"

                page.goto(f"{boardgame_url}/credits")
                page.sleep_random(500, 1000)

                raw_game_data["player_counts"] = page.get_text(
                    'li[itemprop="numberOfPlayers"]'
                )

                raw_game_data["year"] = page.get_text("span.game-year")

                detail_elms = page.locator("credits-module ul > li.outline-item")

                for detail_elm in detail_elms.element_handles():
                    classification_name = detail_elm.query_selector(
                        "div.outline-item-title"
                    )
                    value = detail_elm.query_selector("div.outline-item-description")

                    if not classification_name:
                        continue
                    if not value:
                        continue

                    classification_name = classification_name.inner_text()
                    value = value.inner_text()

                    raw_game_data[classification_name] = value
                    pass

                page.goto(f"{boardgame_url}/versions?showcount=50")
                page.sleep_random(500, 1000)

                dimensions = page.get_texts(
                    "span[ng-if=\"ldata.displaytype==='dimensions'\"]"
                )
                raw_game_data["dimensions"] = list(
                    set(dimensions if dimensions is not None else [])
                )

                page.goto(f"{boardgame_url}/marketplace/stores")
                page.sleep_random(500, 1000)

                raw_game_data["prices"] = page.get_texts(
                    "ul.shopping-listings > li.item-listing a[href] span.item-listing__btn-text"
                )

                page.goto(f"{boardgame_url}/stats")
                page.sleep_random(500, 1000)

                stat_elms = page.locator("div.panel-body > ul > li.outline-item")
                for stat_elm in stat_elms.element_handles():
                    stat_name = stat_elm.query_selector("div.outline-item-title")
                    stat_value = stat_elm.query_selector("div.outline-item-description")

                    if not stat_name:
                        continue
                    if not stat_value:
                        continue

                    stat_name = stat_name.inner_text()
                    stat_value = stat_value.inner_text()

                    raw_game_data[stat_name] = stat_value

                # clean data by removing tabs and collapsing spaces
                for key, value in raw_game_data.items():
                    # remove tabs and collapse any consecutive whitespace to a single space
                    if isinstance(value, str):
                        value = " ".join(value.replace("\t", " ").split())
                        raw_game_data[key] = value
                    elif isinstance(value, list):
                        value = [" ".join(v.replace("\t", " ").split()) for v in value]
                        raw_game_data[key] = value

                with get_db_session() as session:
                    RawRepository.create(
                        session,
                        raw_in=RawDataIn(
                            source_table="boardgame_info",
                            source_id=cast(int, boardgame.id),
                            scrape_task_id=logger.task_id,
                            payload=raw_game_data,
                        ),
                    )

                logger.log(
                    f"Inserted/updated raw boardgame data for '{boardgame.name}'"
                )

                items_processed += 1

                logger.update_progress(
                    progress=i / len(boardgames),
                    items_processed=items_processed,
                    message=f"Processed: {boardgame.name}",
                )
