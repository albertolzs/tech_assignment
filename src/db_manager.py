import os
import sqlite3
from typing import List, Dict, Iterable, Optional
from datetime import date
import pandas as pd
import datetime as dt

from settings import MARKETS, DEFAULT_START_DATE


class DBManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def init(self) -> None:
        if (not os.path.exists(self.db_path)) or (os.path.getsize(self.db_path) == 0):
            with sqlite3.connect(self.db_path) as con:
                dtypes = {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "uid": "TEXT UNIQUE",
                    "title": "TEXT",
                    "link": "TEXT",
                    "date": "TEXT",
                    "time": "TEXT",
                    "region": "TEXT",
                    "zone": "TEXT",
                    "source": "TEXT",
                    **{key: "INTEGER" for key in MARKETS},
                    "reasons": "TEXT",
                    "score": "INTEGER",
                    "summary": "TEXT",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                }
                db = pd.DataFrame([], columns=list(dtypes.keys()))
                db.to_sql("news", con, index=False, dtype=dtypes)
                cur = con.cursor()
                cur.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news(date)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_news_region ON news(region)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)")
                con.commit()


    def _make_uid(self, item: Dict) -> str:
        title = item.get("title", "")[:120]
        date_str = item.get("date", "")
        source = item.get("source", "")
        region = item.get("region", "")
        return f"{region}|{source}|{date_str}|{title}"


    def update(self, items: Iterable[Dict]) -> int:
        if not items:
            return 0
        with sqlite3.connect(self.db_path) as con:
            db = pd.read_sql_query(f"SELECT * FROM news LIMIT 1", con)
            new_db = pd.DataFrame(items).drop(columns=["markets"])
            new_db["uid"] = new_db.apply(self._make_uid, axis=1)
            new_db["reasons"] = new_db["reasons"].astype(str)
            for market in MARKETS:
                new_db[market] = [market in item.get("markets") for item in items]
            new_db = new_db[db.drop(columns=["id", "created_at"]).columns]
            common_rows = new_db.merge(db, on=['uid'], how='inner')
            new_db = new_db.drop(labels=common_rows.index)
            count = new_db.to_sql("news", con, index=False, if_exists="append")
            return count


    def get(
            self,
            region: Optional[List[str]] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            markets_filter: Optional[List[str]] = None,
        ) -> List[Dict]:
        with sqlite3.connect(self.db_path) as con:
            db = pd.read_sql_query(f"SELECT * FROM news", con)
            db.loc[db["date"].notnull(), "date"] = db.loc[db["date"].notnull(), "date"].apply(
                lambda x: dt.datetime.strptime(x, "%Y-%m-%d").date())
            db["date"] = db["date"].fillna(DEFAULT_START_DATE)
            db = db.query(f"region == @region") \
                .query("date >= @start_date") \
                .query("date <= @end_date")
            if markets_filter:
                db = db[db[markets_filter].gt(0).any(axis=1)]
            out = db.to_dict(orient="records")
            return out
