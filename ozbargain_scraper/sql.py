from config import config
import mysql.connector
import sys
import logging

logger = logging.getLogger(__name__)


class SQL:
    def __init__(self):
        try:
            logger.debug("Connecting to database")
            self.db = mysql.connector.connect(
                host=config.settings["sql_host"],
                port=config.settings["sql_port"],
                user=config.settings["sql_user"],
                passwd=config.settings["sql_pass"],
                database=config.settings["sql_database"],
            )
        except mysql.connector.ProgrammingError:
            logger.error("Could not connect to database", exc_info=True)
            sys.exit(0)
        self.cur = self.db.cursor(buffered=True)
        self.insertQuery = 'INSERT INTO livedeals (timestamp, title, price, link) VALUES ("{0}", "{1}", "{2}", "{3}") ON DUPLICATE KEY UPDATE title="{1}", price="{2}", link="{3}"'
        logger.debug("Database connected")

    def __enter__(self):
        return self

    def close(self):
        logger.debug("Closing database connection")
        self.db.commit()
        self.cur.close()
        self.db.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def insertIntoSQL(self, list):
        logger.info("Inserting into SQL")
        for item in list:
            try:
                query = self.insertQuery.format(
                    item["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    item["title"],
                    item["price"],
                    item["link"],
                )
                self.cur.execute(query)
            except mysql.connector.errors.IntegrityError:
                pass
        self.db.commit()
        logger.debug("Data inserted into SQL")

    def getDealId(self, deal):
        query = 'SELECT id FROM livedeals as ld WHERE ld.timestamp="{0}"'.format(deal[1]["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))
