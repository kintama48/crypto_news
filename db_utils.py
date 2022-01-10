import os
import sys
import json
import psycopg2

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


class Database:
    def __init__(self):
        self.db = psycopg2.connect(host=config["database"]["host"], database=config["database"]["database"],
                                   user=config["database"]["user"], port=config["database"]["port"],
                                   password=config["database"]["password"])

    def get_news_id(self):
        cur = self.db.cursor()
        cur.execute('select * from news_id;')
        return cur.fetchone()[0]

    def set_news_id(self, news_id):
        news_id = int(news_id)
        cur = self.db.cursor()
        cur.execute(f'update news_id set id={news_id};')
        self.db.commit()

