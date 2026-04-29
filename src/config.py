"""新聞看板資料來源設定。"""

RSS_SOURCES = {
    "world": [
        ("Reuters World", "https://news.google.com/rss/search?q=when:24h+site:reuters.com+world&hl=en-US&gl=US&ceid=US:en", 3),
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", 3),
        ("CNN World", "http://rss.cnn.com/rss/edition_world.rss", 2),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", 2),
        ("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 3),
    ],
    "finance": [
        ("Reuters Business", "https://news.google.com/rss/search?q=when:24h+site:reuters.com+business&hl=en-US&gl=US&ceid=US:en", 3),
        ("BBC Business", "http://feeds.bbci.co.uk/news/business/rss.xml", 3),
        ("CNN Business", "http://rss.cnn.com/rss/money_latest.rss", 2),
        ("Bloomberg", "https://news.google.com/rss/search?q=when:24h+site:bloomberg.com&hl=en-US&gl=US&ceid=US:en", 3),
        ("Financial Times", "https://news.google.com/rss/search?q=when:24h+site:ft.com&hl=en-US&gl=US&ceid=US:en", 3),
        ("WSJ", "https://news.google.com/rss/search?q=when:24h+site:wsj.com+(markets+OR+economy+OR+business)&hl=en-US&gl=US&ceid=US:en", 3),
        ("CNBC", "https://news.google.com/rss/search?q=when:24h+site:cnbc.com&hl=en-US&gl=US&ceid=US:en", 2),
        ("鉅亨網", "https://news.google.com/rss/search?q=when:24h+site:cnyes.com&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 2),
        ("經濟日報", "https://news.google.com/rss/search?q=when:24h+site:money.udn.com&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 2),
        ("工商時報", "https://news.google.com/rss/search?q=when:24h+site:ctee.com.tw&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 2),
        ("商業周刊", "https://news.google.com/rss/search?q=when:24h+site:businessweekly.com.tw+(財經+OR+股+OR+投資+OR+金融+OR+經濟+OR+企業)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 2),
    ],
    "crypto": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", 3),
        ("Cointelegraph", "https://cointelegraph.com/rss", 2),
        ("Decrypt", "https://decrypt.co/feed", 2),
        ("BlockTempo 動區", "https://www.blocktempo.com/feed/", 2),
        ("ABMedia 鏈新聞", "https://www.abmedia.io/feed", 2),
    ],
    "tech": [
        ("TechCrunch", "https://techcrunch.com/feed/", 3),
        ("VentureBeat", "https://venturebeat.com/feed/", 2),
        ("The Verge", "https://www.theverge.com/rss/index.xml", 2),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", 2),
        ("iThome", "https://news.google.com/rss/search?q=when:24h+site:ithome.com.tw&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 3),
        ("數位時代", "https://news.google.com/rss/search?q=when:24h+site:bnext.com.tw&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 3),
    ],
    "entertainment": [
        ("Hollywood Reporter", "https://www.hollywoodreporter.com/feed/", 3),
        ("Variety", "https://variety.com/feed/", 3),
        ("Deadline", "https://deadline.com/feed/", 2),
        ("ETtoday 娛樂", "https://news.google.com/rss/search?q=when:24h+site:star.ettoday.net&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 3),
        ("鏡週刊 娛樂", "https://news.google.com/rss/search?q=when:48h+site:mirrormedia.mg+(娛樂+OR+影劇+OR+明星)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", 3),
    ],
}

CATEGORY_META = {
    "world":         {"label": "世界",   "icon": "🌍", "order": 1, "top_n": 5},
    "finance":       {"label": "財經",   "icon": "💰", "order": 2, "top_n": 5},
    "crypto":        {"label": "加密",   "icon": "🪙", "order": 3, "top_n": 5},
    "tech":          {"label": "科技",   "icon": "💻", "order": 4, "top_n": 5},
    "entertainment": {"label": "影視",   "icon": "🎬", "order": 5, "top_n": 5},
    "reports":       {"label": "機構報告","icon": "📚", "order": 6, "top_n": 5},
}

STOCK_TICKERS = [
    ("^TWII",  "台股加權"),
    ("^GSPC",  "S&P 500"),
    ("^IXIC",  "Nasdaq"),
    ("^DJI",   "Dow Jones"),
    ("^N225",  "日經 225"),
    ("USDTWD=X", "USD/TWD"),
    ("DX-Y.NYB", "美元指數"),
]

CRYPTO_COINS = ["bitcoin", "ethereum"]

# 機構報告來源（沒有 when 限制 → 抓最近能搜到的，通常是過去 30 天）
REPORT_SOURCES = [
    ("McKinsey",        "https://news.google.com/rss/search?q=site:mckinsey.com+(report+OR+insights+OR+outlook)&hl=en-US&gl=US&ceid=US:en"),
    ("Goldman Sachs",   "https://news.google.com/rss/search?q=site:goldmansachs.com+(insights+OR+outlook+OR+research)&hl=en-US&gl=US&ceid=US:en"),
    ("IMF",             "https://news.google.com/rss/search?q=site:imf.org+(report+OR+outlook+OR+publication)&hl=en-US&gl=US&ceid=US:en"),
    ("WEF",             "https://news.google.com/rss/search?q=site:weforum.org+(report+OR+whitepaper)&hl=en-US&gl=US&ceid=US:en"),
    ("CFR",             "https://news.google.com/rss/search?q=site:cfr.org+(report+OR+analysis)&hl=en-US&gl=US&ceid=US:en"),
    ("World Bank",      "https://news.google.com/rss/search?q=site:worldbank.org+(report+OR+outlook)&hl=en-US&gl=US&ceid=US:en"),
    ("BCG",             "https://news.google.com/rss/search?q=site:bcg.com+(insight+OR+report)&hl=en-US&gl=US&ceid=US:en"),
    ("Bain",            "https://news.google.com/rss/search?q=site:bain.com+(report+OR+insight)&hl=en-US&gl=US&ceid=US:en"),
    ("PwC",             "https://news.google.com/rss/search?q=site:pwc.com+(report+OR+outlook)&hl=en-US&gl=US&ceid=US:en"),
    ("Deloitte",        "https://news.google.com/rss/search?q=site:deloitte.com+(report+OR+insights)&hl=en-US&gl=US&ceid=US:en"),
    ("TAICCA",          "https://news.google.com/rss/search?q=site:taicca.tw&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
    ("資策會 MIC",       "https://news.google.com/rss/search?q=site:mic.iii.org.tw+OR+(資策會+(報告+OR+研究+OR+分析+OR+趨勢))&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
    ("工研院 IEK",       "https://news.google.com/rss/search?q=(工研院+OR+IEK+OR+ITRI)+(產業趨勢+OR+技術趨勢+OR+研究報告+OR+市場分析+OR+產業洞察)&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"),
]

REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (NewsDashboard/0.1)"

# 各分類關鍵字黑名單（標題含這些字會被過濾掉）
BLACKLIST_KEYWORDS = {
    "finance": [
        # 生活、健康、心理
        "生活", "旅遊", "美食", "健康", "星座", "育兒", "減肥", "養生", "瘦身",
        "料理", "心情", "療癒", "寵物", "戀愛", "命理", "八字", "塔羅", "減脂",
        "保養", "穿搭", "親子", "家庭", "睡眠", "婚姻", "心理測驗", "情感",
        "婚禮", "髮型", "美容", "食譜", "減重", "瑜珈", "瑜伽", "戀人",
        "占卜", "風水", "球星", "球員", "球隊", "藝人", "明星", "演員",
        "失眠", "便秘", "腸道", "腦袋", "腦力", "大腦", "情緒", "焦慮", "憂鬱",
        # 生活習慣、撇步、教你類
        "撇步", "妙招", "秘訣", "祕訣", "訣竅", "教你", "教戰", "攻略",
        "必學", "小妙招", "小秘密", "你不知道", "你知道嗎", "1 招",
        "1招", "2招", "3招", "5招", "幾招", "技巧", "懶人包",
        "如何讓", "這樣做", "這樣吃", "這樣穿", "這樣選", "怎麼吃", "怎麼選",
        "幸福感", "幸福", "做這件事", "做這 5 件", "做這5件",
        "壞習慣", "好習慣", "養成習慣", "習慣養成",
        "早餐吃", "午餐吃", "晚餐吃", "宵夜",
        "失敗者", "成功人士", "聰明人",
        # 體育、政治雜訊
        "MLB", "NBA", "中職", "棒球", "籃球",
        # 英文 lifestyle
        "lifestyle", "wellness", "horoscope", "celebrity", "diet",
        "habit", "habits", "weight loss", "happiness",
    ],
    "world": [
        "球員", "球隊", "明星緋聞", "horoscope", "celebrity",
    ],
    "tech": [
        "球員", "藝人", "明星", "命理", "horoscope",
    ],
}

# 每來源於同一類別中最多顯示幾篇（避免單一來源洗版）
MAX_PER_SOURCE_PER_CATEGORY = 3
