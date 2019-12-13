
import mysql.connector
import sys
import logging

logger = logging.getLogger(__name__)

class SQL:
    def __init__(self):
        try:
            logger.debug('Connecting to database')
            self.db = mysql.connector.connect(
                host="localhost",
                port="3306",
                user="root",
                passwd="1234",
                database="ozbargain"
            )
        except mysql.connector.ProgrammingError:
            logger.error("Could not connect to database", exc_info=True)
            sys.exit(0)
        self.cur = self.db.cursor()
        self.insertQuery = 'INSERT INTO livedeals (timestamp, title, price, link) VALUES ("{0}", "{1}", "{2}", "{3}") ON DUPLICATE KEY UPDATE title="{1}", price="{2}", link="{3}"'
        logger.debug('Database connected')

    def __enter__(self):
        return self

    def close(self):
        logger.debug("Closing database connection")
        self.db.commit()
        self.cur.close()
        self.db.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def insertIntoSQL(self, dict):
        try:
            query = self.insertQuery.format(
                dict['timestamp'], dict['title'], dict['price'], dict['link'])
            self.cur.execute(query)
        except mysql.connector.errors.IntegrityError:
            pass
