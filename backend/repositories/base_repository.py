from psycopg2 import OperationalError


class BaseRepository:
    # thin helper placeholder for retries / common behavior
    retry_errors = (OperationalError,)
