import os
import sys
import json
import asyncio
import subprocess
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import google.generativeai as genai
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Configure Gemini
GENAI_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_KEY:
    genai.configure(api_key=GENAI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
else:
    logger.warning("GEMINI_API_KEY not found. Sentiment analysis will be skipped/mocked.")
    model = None

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRAWLER_DIR = os.path.join(BASE_DIR, "crawler")
DATA_DIR = os.path.join(BASE_DIR, "data")
MOCK_STOCKS_FILE = os.path.join(BASE_DIR, "stocks.json")
MOCK_NEWS_FILE = os.path.join(BASE_DIR, "news.json")

# Ensure data dir exists
os.makedirs(DATA_DIR, exist_ok=True)

def run_crawler(script_name, args=[]):
    """Run a python script from the crawler directory."""
    script_path = os.path.join(CRAWLER_DIR, script_name)
    cmd = [sys.executable, script_path] + args
    logger.info(f"Running crawler: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=BASE_DIR) # Run from server root so relative paths work if needed
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run {script_name}: {e}")
        return False

def get_sentiment_analysis(news_items):
    """
    Analyze sentiment of news items using Gemini.
    Returns a dict mapping news_url -> {sentiment, reason}
    """
    if not model or not news_items:
        return {}

    # Prepare batch prompt
    # Limit to top 20 news to avoid quota limits
    batch = news_items[:20] 
    
    prompt = """
    Analyze the sentiment of the following news headlines/summaries for the related companies.
    Return a JSON object where keys are the 'id' (index) and values are objects with 'sentiment' (Positive, Negative, Neutral) and 'reason' (brief explanation in Korean).
    
    News Items:
    """
    
    for i, item in enumerate(batch):
        prompt += f"\n[{i}] {item['title']} (Summary: {item.get('snippet','')})"
        
    prompt += "\n\nJSON Response:"
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        result = json.loads(text)
        # Map back to original items
        analyzed = {}
        for i_str, analysis in result.items():
            idx = int(i_str)
            if idx < len(batch):
                analyzed[batch[idx]['url']] = analysis
        return analyzed

    except Exception as e:
        logger.error(f"Gemini Analysis Failed: {e}")
        return {}

def process_stocks_and_news():
    """
    Read CSVs from data/price_data and data/news_naver.
    Transform into JSON for frontend.
    """
    
    # 1. Identify Snapshot Date
    # Default to today, or search for latest folder in data/news_naver
    news_base = os.path.join(DATA_DIR, "news_naver")
    if not os.path.exists(news_base):
        logger.warning("No news data found. Run crawlers first.")
        return

    dates = sorted(os.listdir(news_base))
    if not dates:
        logger.warning("No dated folders in news_naver.")
        return
    snapshot_date = dates[-1]
    logger.info(f"Processing data for date: {snapshot_date}")

    # 2. Process Stock Prices
    price_dir = os.path.join(DATA_DIR, "price_data")
    stocks_list = []
    
    # Check for KOSPI_KOSDAQ.csv for names
    ticker_map = {}
    ticker_file = os.path.join(CRAWLER_DIR, "KOSPI_KOSDAQ.csv")
    if os.path.exists(ticker_file):
        try:
            df_meta = pd.read_csv(ticker_file, dtype=str)
             # Assume columns like 'Symbol', 'Market', 'Name', 'Sector' - adjust based on actual CSV
            # Based on inspection, it might lack headers or have specific ones.
            # Let's assume standard layout or use what we saw in news_naver.py (load_name_map)
            pass
        except Exception:
            pass

    # Use the load_name_map logic from news_naver for reliability
    sys.path.append(CRAWLER_DIR)
    from news_naver import load_name_map
    name_map = load_name_map(ticker_file) # Returns dict {code: name}

    # Iterate over price CSVs
    # We need a list of target tickers. Let's use the ones in tickers.txt if present
    target_tickers = []
    target_ticker_file = os.path.join(CRAWLER_DIR, "tickers.txt")
    if os.path.exists(target_ticker_file):
        with open(target_ticker_file, 'r') as f:
            target_tickers = [line.strip() for line in f if line.strip()]
    
    price_history_all = {}

    for ticker in target_tickers:
        csv_path = os.path.join(price_dir, f"{ticker}.csv")
        if not os.path.exists(csv_path):
            continue
            
        try:
            df = pd.read_csv(csv_path)
            # sort by date asc
            df = df.sort_values("date")
            
            latest = df.iloc[-1]
            # Headers: date,open,high,low,close,volume,change(optional)
            
            # Populate Stock Object
            current_price = int(latest['close'])
            prev_price = int(df.iloc[-2]['close']) if len(df) > 1 else current_price
            change_rate = (current_price - prev_price) / prev_price
            
            stock_obj = {
                "code": ticker,
                "name": name_map.get(ticker, ticker),
                "market": "KOSPI", # Simplification. Real logic needs market lookup.
                "sector": "Unknown", # Needs sector map
                "current_price": current_price,
                "change_rate": round(change_rate, 4),
                "market_cap": current_price * 1000000, # Mock cap if not in CSV
                "price_history": dict(zip(df['date'].tolist(), df['close'].tolist()))
            }
            stocks_list.append(stock_obj)
            price_history_all[ticker] = df['close'].tolist()[-30:] # Last 30 days for correlation
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")

    # 3. Calculate Correlation
    if price_history_all:
        # Pad lists to same length
        max_len = max(len(v) for v in price_history_all.values())
        for k, v in price_history_all.items():
            if len(v) < max_len:
                price_history_all[k] = [v[0]] * (max_len - len(v)) + v
                
        df_corr = pd.DataFrame(price_history_all)
        corr_matrix = df_corr.corr().fillna(0).to_dict()
    else:
        corr_matrix = {}

    # 4. Process News
    news_dir = os.path.join(news_base, snapshot_date)
    all_news = []
    
    news_id_counter = 1
    
    for ticker in target_tickers:
        csv_path = os.path.join(news_dir, f"{ticker}.csv")
        if not os.path.exists(csv_path):
            continue
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                import csv
                reader = csv.DictReader(f)
                rows = list(reader)
                
            # Take top 3 news per ticker
            for row in rows[:3]:
                all_news.append({
                    "id": news_id_counter,
                    "related_stocks": [ticker],
                    "title": row.get('title'),
                    "date": row.get('published_at', '')[:10], # YYYY-MM-DD
                    "url": row.get('url'),
                    "snippet": row.get('snippet'),
                    "source": row.get('publisher')
                })
                news_id_counter += 1
        except Exception as e:
            logger.error(f"Error reading news for {ticker}: {e}")

    # 5. Sentiment Analysis (Batch)
    logger.info("Running AI Sentiment Analysis...")
    sentiment_map = get_sentiment_analysis(all_news)
    
    for news in all_news:
        url = news['url']
        if url in sentiment_map:
            res = sentiment_map[url]
            news['sentiment'] = res.get('sentiment', 'Neutral')
            news['summary'] = res.get('reason', news.get('snippet'))
        else:
            news['sentiment'] = "Neutral"
            news['summary'] = news.get("snippet", "")

    # 6. Save JSONs
    output_stocks = {
        "stocks": stocks_list,
        "correlation": corr_matrix
    }
    
    with open(MOCK_STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(output_stocks, f, ensure_ascii=False, indent=2)
        
    with open(MOCK_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
        
    logger.success(f"ETL Complete. Saved {len(stocks_list)} stocks and {len(all_news)} news items.")

def main():
    logger.info("Starting Daily ETL Pipeline...")
    
    # 1. Run Crawler - Stocks
    # Need to pass correct args to append_stock_prices.
    # It reads tickers.txt by default
    
    # Ensure tickers.txt is in CWD or passed correctly
    # script expects run from 'root' usually or we pass absolute paths?
    # Let's pass absolute path to tickers.txt if needed or rely on default
    
    # Using 'server' as CWD for python execution in run_crawler?
    # Actually run_crawler uses BASE_DIR which is server/
    
    # Ticker File needs to be accessible. 
    # In 'server/crawler/tickers.txt'.
    
    ticker_file_rel = os.path.join("crawler", "tickers.txt")
    
    # 1. Run Stock Price Crawler
    # append_stock_prices.py --tickers ... 
    # But wait, original script uses relative imports from 'ls_t1305.py'.
    # If we run from server root, we need to make sure python path is correct.
    # The script `append_stock_prices.py` does `sys.path.append(CURRENT_DIR)`.
    
    if not run_crawler("append_stock_prices.py", ["--tickers", ticker_file_rel, "--outdir", "data/price_data"]):
        logger.error("Stock price crawler failed.")
    
    # 2. Run News Crawler
    # news_naver.py --ticker-file crawler/KOSPI_KOSDAQ.csv ...
    ticker_csv_rel = os.path.join("crawler", "KOSPI_KOSDAQ.csv")
    if not run_crawler("news_naver.py", ["--ticker-file", ticker_csv_rel, "--outdir", "data/news_naver/{date}", "--days", "1"]):
        logger.error("News crawler failed.")

    # 3. Process Data
    process_stocks_and_news()

if __name__ == "__main__":
    main()
