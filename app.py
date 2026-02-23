from backend.db import get_db_session, init_db
from backend.repositories import BoardGameRepository
from scraping.scrape_boardgames_links import scrape_boardgames_links


def main():
    init_db()

    scrape_boardgames_links(10)

    with get_db_session() as session:
        boardgames = BoardGameRepository.get_all(session)
        print(f"Found {len(boardgames)} board games in the database:")
        for bg in boardgames[:10]:
            print(bg.name)


if __name__ == "__main__":
    main()
