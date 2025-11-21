import datetime as dt
import logging
import sqlite3
import time
from typing import List, Dict, Optional
import json
import ollama
import feedparser
import pandas as pd
from bs4 import BeautifulSoup

from settings import REGIONS, MARKETS, DB_PATH, DEFAULT_START_DATE
from src import ANALYSIS_CONTEXT_PROMPT


class NewsFetcher():

    def __init__(self, time_out: int, utc) -> None:
        self.logger = logging.getLogger(__name__)
        self.time_out = time_out
        self.utc = utc


    def parse_date(self, entry) -> Optional[dt.datetime]:
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            if getattr(entry, key, None):
                t = getattr(entry, key)
                try:
                    return dt.datetime.fromtimestamp(time.mktime(t), tz=self.utc)
                except Exception:
                    continue
        for key in ("published", "updated", "created"):
            val = entry.get(key)
            if not val:
                continue
            try:
                return dt.datetime(*entry.get(f"{key}_parsed"))
            except Exception:
                continue
        return None


    def clean_html(self, html: str) -> str:
        try:
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(" ", strip=True)
        except Exception:
            return html


    def fetch_rss(self, url: str) -> List[Dict]:
        parsed = feedparser.parse(url)
        items = []
        for e in parsed.entries:
            items.append({
                "title": e.get("title"),
                "summary_raw": self.clean_html(e.get("summary", "")),
                "link": e.get("link"),
                "date_dt": self.parse_date(e),
            })
        return items


    def build_prompt(self, title: str, summary: str, markets: str) -> str:
        prompt = ANALYSIS_CONTEXT_PROMPT + f"News: TITLE='{title}'. SUMMARY='{summary}'. MARKETS='{markets}'."
        return prompt


    def heuristic_relevance(self, title: str, summary: str) -> Dict:
        text = f"{title} {summary}".lower()
        keywords = [
            "regulat", "policy", "central bank", "interest rate" "inflation", "bank", "capital", "invest"
        ]
        relevant = any(k in text for k in keywords)
        brief = title if len(title) < 180 else title[:177] + "..."
        markets = [market for market in MARKETS if market in text]
        return {
            "relevant": bool(relevant),
            "markets": markets,
            "score": 0,
            "summary": brief if relevant else "",
            "reasons": []
        }


    def extract_with_llm(self, model: str, title: str, summary: str, markets: str) -> Dict:
        prompt = self.build_prompt(title=title, summary=summary, markets=markets)
        resp = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            options={"temperature":0.0},
        )
        content = resp.get("message", {}).get("content", "")
        try:
            data = json.loads(content)
        except:
            data = json.loads(content[3:-3])
        return {
            "relevant": bool(data.get("relevant")),
            "markets": data.get("markets", []),
            "score": data.get("score", 0),
            "summary": data.get("summary", ""),
            "reasons": data.get("reasons", []),
        }


    def fetch_news(
            self,
            region: str,
            end_date: dt.date,
            start_date: dt.date = None,
            use_llm: bool = False,
            model: str = "llama3.2:1b",
        ) -> List[Dict]:
        conf = REGIONS.get(region)
        if not conf:
            return []
        with sqlite3.connect(DB_PATH) as con:
            db = pd.read_sql_query(f"SELECT * FROM news", con)
            if len(db) == 0:
                start_date = DEFAULT_START_DATE
            if start_date is None:
                start_date = db.sort_values(by="date")["date"]
                if start_date.empty:
                    start_date = DEFAULT_START_DATE
                else:
                    start_date = dt.datetime.strptime(start_date.iloc[0], "%Y-%m-%d").date()

            items = []

            for src in conf.get("sources", []):
                url = src.get("url")
                if not url:
                    continue
                try:
                    if src.get("type") == "rss":
                        fetched = self.fetch_rss(url)
                    else:
                        fetched = []
                except Exception as e:
                    self.logger.warning(f"Error fetching {url}: {e}")
                    continue

                fetched = fetched[:10]
                for it in fetched:
                    date_dt = it.get("date_dt")
                    if date_dt is not None:
                        d = date_dt.date()
                        if d < start_date or d > end_date:
                            continue

                    title = it.get("title", "")
                    summary_raw = it.get("summary_raw", "")

                    nlp_method = "heuristic"
                    if use_llm:
                        try:
                            assess = self.extract_with_llm(model=model, title=title, summary=summary_raw, markets=MARKETS)
                            nlp_method = model
                        except Exception as e:
                            self.logger.exception(f"LLM call failed: {e}")
                            assess = self.heuristic_relevance(title, summary_raw)
                    else:
                        assess = self.heuristic_relevance(title, summary_raw)

                    if not assess.get("relevant"):
                        continue

                    items.append({
                        "title": title,
                        "markets": assess.get("markets"),
                        "score": assess.get("score"),
                        "summary": assess.get("summary") or summary_raw[:300],
                        "reasons": assess.get("reasons"),
                        "link": it.get("link"),
                        "date": date_dt.strftime("%Y-%m-%d") if date_dt else None,
                        "time": date_dt.strftime("%H-%M-%S") if date_dt else None,
                        "region": region,
                        "zone": conf.get("zone"),
                        "source": src.get("name"),
                        "extractor": nlp_method,
                    })

            items.sort(key=lambda x: x.get("date") or "0000-00-00", reverse=True)
            return items
