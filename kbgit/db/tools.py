import os
from .chroma import ChromaDBConnection


def get_db_connection():
    # TODO. Add more DB connections here
    if os.getenv('DB_TYPE') == "chroma":
        return ChromaDBConnection()