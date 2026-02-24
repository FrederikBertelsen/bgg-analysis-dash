from backend.database.db import get_db_session
from backend.logger import ScrapeTaskLogger
from backend.repositories import BoardGameRepository, ScrapeTaskRepository
from backend.database.schemas import BoardGameIn
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
    #     print("Login verification failed: Request error detected")
    #     return False

    # page.sleep(100000)

    return logged_in


def scrape_boardgames_links(pages: int = 10, log_to_console: bool = True):
    with ScrapeTaskLogger(
        task_name="scrape_boardgames_links", log_to_console=log_to_console
    ) as logger:
        logger.log("Started")

        items_processed = 0

        with CamoufoxWrapper().start_browser() as browser:
            page = browser.new_page(logger)

            logged_in = login(page, logger)
            if not logged_in:
                logger.fail("Login failed")
                return

            logger.log("Login successful")

            for i in range(1, pages + 1):
                page.goto(f"https://boardgamegeek.com/browse/boardgame/page/{i}")

                # if page.exists("gg-login-page"):
                #     print(f"Session expired on page {i}, re-logging in")
                #     if not login(page):
                #         print("Re-login failed, aborting")
                #         break

                #     page.goto(f"https://boardgamegeek.com/browse/boardgame/page/{i}")

                boardgame_names = page.get_texts("td.collection_objectname a.primary")
                boardgame_urls = page.get_attributes(
                    "td.collection_objectname a.primary", "href"
                )

                if boardgame_names is None or boardgame_urls is None:
                    logger.fail(f"Failed to scrape page {i}: missing data")
                    return

                if len(boardgame_names) != len(boardgame_urls):
                    logger.fail(
                        f"Failed to scrape page {i}: mismatched data length ({len(boardgame_names)}, {len(boardgame_urls)})"
                    )
                    return

                # clean data
                boardgame_names = [name.strip() for name in boardgame_names]
                boardgame_urls = [url.strip() for url in boardgame_urls]
                boardgame_ids = [int(url.split("/")[-2]) for url in boardgame_urls]

                boardgames = []
                for id, name, url in zip(
                    boardgame_ids,
                    boardgame_names,
                    boardgame_urls,
                ):
                    boardgames.append(BoardGameIn(id=id, name=name, url=url))

                with get_db_session() as session:
                    BoardGameRepository.bulk_upsert(session, boardgames)

                logger.log(
                    f"Inserted/updated {len(boardgames)} boardgames from page {i}"
                )

                items_processed += len(boardgames)

                logger.update_progress(
                    progress=i / pages,
                    current_page=i,
                    items_processed=items_processed,
                    message=f"Processed page {i} with {len(boardgames)} boardgames",
                )

                page.sleep_random(4000, 5000)
