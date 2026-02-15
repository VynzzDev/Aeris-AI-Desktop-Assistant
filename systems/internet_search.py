import re
import webbrowser
from urllib.parse import quote_plus
from serpapi import GoogleSearch
from memory.config_manager import get_serpapi_key

MAX_NEWS_ITEMS = 3



def clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\(.*?\)|\[.*?\]", "", text)
    text = text.strip()
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s*—\s*", " - ", text)
    return text


def is_trash(text: str) -> bool:
    t = text.lower()

    trash_patterns = [
        r"\bstock(?:s)?\b.*\btoday\b",
        r"\bshare(?:s)?\b.*\bprice\b",
        r"\binvestor(?:s)?\b",
        r"\btrading\b",
        r"\bmarket(?:s)?\b.*\bopen(?:s|ed)?\b",
        r"\bticker\b",
        r"\bnyse\b",
        r"\bnasdaq\b",
        r"\.\w{2,4}\sis\b",
    ]

    spam_keywords = [
        "click here", "read more", "advertisement", "sponsored",
        "subscribe", "newsletter", "sign up",
        "best things to do", "events this week", "calendar",
        "official website", "visit our", "learn more",
        "year in review", "trending now", "top 10"
    ]

    for pattern in trash_patterns:
        if re.search(pattern, t):
            return True

    return any(keyword in t for keyword in spam_keywords)


def extract_clean_news(result: dict) -> str:
    title = clean(result.get("title", ""))
    snippet = clean(result.get("snippet", ""))

    if not title:
        return ""

    if snippet.startswith(title[:30]) or snippet == title:
        return title

    if len(snippet) > 120:
        snippet = snippet[:120]
        last_period = snippet.rfind(".")
        last_space = snippet.rfind(" ")

        if last_period > 80:
            snippet = snippet[:last_period + 1]
        elif last_space > 80:
            snippet = snippet[:last_space] + "..."

        return f"{title}. {snippet}"

    return f"{title}. {snippet}" if snippet else title


def format_news_output(news_items: list) -> str:
    if len(news_items) == 1:
        return news_items[0]
    elif len(news_items) == 2:
        return f"{news_items[0]}. Also, {news_items[1]}"
    else:
        result = news_items[0]
        for item in news_items[1:-1]:
            result += f". {item}"
        result += f". Additionally, {news_items[-1]}"
        return result



def serpapi_search(query: str) -> str:

    api_key = get_serpapi_key()
    if not api_key:
        return "Sir, the web search system is not configured."

    clean_query = query

    if "what happened" in query.lower():
        clean_query = re.sub(
            r"what happened (?:in|at|to)\s*",
            "",
            query,
            flags=re.IGNORECASE
        )
        clean_query += " news today"

    base_params = {
        "q": clean_query,
        "api_key": api_key,
        "hl": "en",
        "gl": "us",
        "num": 15
    }

    try:
        params = {**base_params, "engine": "google_news"}
        search = GoogleSearch(params)
        data = search.get_dict()
        results = data.get("news_results", [])

    except Exception:
        try:
            params = {**base_params, "engine": "google"}
            search = GoogleSearch(params)
            data = search.get_dict()
            results = data.get("organic_results", [])
        except Exception:
            return "Sir, I couldn't connect to the search service."

    if not results:
        return "Sir, I couldn't find any recent news about that."

    news_items = []

    for result in results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        if is_trash(title) or is_trash(snippet):
            continue

        news_text = extract_clean_news(result)

        if news_text and len(news_text.split()) >= 6:
            news_items.append(news_text)

        if len(news_items) >= MAX_NEWS_ITEMS:
            break

    if not news_items:
        return "Sir, I found some results but they weren't clear news stories."

    return format_news_output(news_items)



def web_search(parameters, player=None, session_memory=None):

    query = (parameters or {}).get("query", "").strip()

    if not query:
        return "Sir, I couldn't understand the search request."

    try:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
    except Exception:
        pass

    answer = serpapi_search(query)

    if session_memory:
        session_memory.set_last_search(query, answer)

    return answer
