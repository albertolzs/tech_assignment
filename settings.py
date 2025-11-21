import datetime as dt

REGIONS = {
    "United States": {
        "zone": "North America",
        "sources": [
            {
                "name": "Federal Reserve Board",
                "url": "https://www.federalreserve.gov/feeds/press_all.xml",
                "type": "rss",
            },
            {
                "name": "Securities and Exchange Commission",
                "url": "https://www.sec.gov/news/pressreleases.rss",
                "type": "rss",
            },
            {
                "name": "Nature",
                "url": "https://www.nature.com/nature.rss",
                "type": "rss",
            },
            {
                "name": "FX Street",
                "url": "https://about.fxstreet.com/press-releases/",
                "type": "rss",
            },
        ],
    },
    "European Union": {
        "zone": "Europe",
        "sources": [
            {
                "name": "European Central Bank",
                "url": "https://www.ecb.europa.eu/rss/pub.html",
                "type": "rss",
            },
            {
                "name": "Eurostat",
                "url": "https://ec.europa.eu/eurostat/en/search?p_p_id=estatsearchportlet_WAR_estatsearchportlet&p_p_lifecycle=2&p_p_state=maximized&p_p_mode=view&p_p_resource_id=atom&_estatsearchportlet_WAR_estatsearchportlet_collection=CAT_PREREL",
                "type": "rss",
            },
            {
                "name": "European Parliament",
                "url": "https://www.europarl.europa.eu/rss/doc/press-releases/en.xml",
                "type": "rss",
            },
            {
                "name": "European Securities and Markets Authority",
                "url": "https://www.esma.europa.eu/rss.xml",
                "type": "rss",
            },
        ],
    },
    "United Kingdom": {
        "zone": "UK",
        "sources": [
            {
                "name": "Bank of England",
                "url": "https://www.bankofengland.co.uk/rss/news",
                "type": "rss",
            },
            {
                "name": "HM Treasury",
                "url": "https://www.gov.uk/government/organisations/hm-treasury.atom",
                "type": "rss",
            },
            {
                "name": "Financial Conduct Authority",
                "url": "https://www.fca.org.uk/news/rss.xml",
                "type": "rss",
            },
        ],
    },
    "China": {
        "zone": "Asia",
        "sources": [
            {
                "name": "China News Service",
                "url": "http://www.ecns.cn/rss/rss.xml",
                "type": "rss",
            },
            {
                "name": "China Digital Times",
                "url": "https://chinadigitaltimes.net/feed/",
                "type": "rss",
            },
            {
                "name": "BBC News China",
                "url": "https://feeds.bbci.co.uk/news/world/asia/china/rss.xml",
                "type": "rss",
            },
        ],
    },
    "Japan": {
        "zone": "Asia",
        "sources": [
            {
                "name": "Bank of Japan",
                "url": "https://www.boj.or.jp/en/rss/whatsnew.xml",
                "type": "rss",
            },
            {
                "name": "Financial Services Agency Japan",
                "url": "https://www.fsa.go.jp/fsaEnNewsList_rss2.xml",
                "type": "rss",
            },
        ],
    },
}

MARKETS = [
    "Energy",
    "Technology",
    "Climate Change",
    "Healthcare",
    "Real Estate",
]

AVAILABLE_MODELS = [
    "llama3.1:8b",
    "llama3.2:1b",
    "gpt-oss:latest",
    "gemma3:270m",
]

DEFAULT_START_DATE = dt.date(2025, 11, 10)

DB_PATH = "news_info.db"

HTTP_TIMEOUT = 10