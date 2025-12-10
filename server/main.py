from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from typing import List, Dict, Any
from pydantic import BaseModel
from ai_service import get_guru_analysis, get_chat_response
from data_service import (
    get_data_status, 
    refresh_all_data, 
    on_user_login,
    calculate_technical_indicators,
    load_opm_data
)
import random

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Data
STOCKS_FILE = "../stocks.json"
NEWS_FILE = "../news.json"
PRICE_DATA_DIR = "data/price_data"

def load_data():
    stocks_data = {}
    news_data = []
    
    if os.path.exists(STOCKS_FILE):
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            stocks_data = json.load(f)
    
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            news_data = json.load(f)
    
    # Update stock prices from CSV files if available
    if os.path.exists(PRICE_DATA_DIR):
        import csv
        for stock in stocks_data.get("stocks", []):
            code = stock.get("code")
            csv_path = os.path.join(PRICE_DATA_DIR, f"{code}.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    if rows:
                        # First row is the latest (sorted descending by date)
                        latest = rows[0]
                        prev = rows[1] if len(rows) > 1 else latest
                        
                        current_price = int(float(latest.get("close", 0)))
                        prev_price = int(float(prev.get("close", current_price)))
                        change_rate = (current_price - prev_price) / prev_price if prev_price else 0
                        
                        stock["current_price"] = current_price
                        stock["change_rate"] = round(change_rate, 4)
                        stock["last_updated"] = latest.get("date", "")
                except Exception as e:
                    print(f"Warning: Could not load price data for {code}: {e}")
        
    return stocks_data, news_data

stocks_data, news_data = load_data()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class PortfolioItem(BaseModel):
    code: str
    amount: int
    name: str = "" # Optional for input

class ChatRequest(BaseModel):
    message: str
    context: str = ""

# In-memory storage for prototype (resets on restart)
# purchase_price: 매수 당시 가격, purchase_date: 매수일
user_portfolios = {
    "20201651": [
        {"code": "005930", "name": "삼성전자", "amount": 100, "purchase_price": 100800, "purchase_date": "2025-12-01"},
        {"code": "000660", "name": "SK하이닉스", "amount": 50, "purchase_price": 538000, "purchase_date": "2025-12-01"},
        {"code": "035420", "name": "NAVER", "amount": 20, "purchase_price": 243000, "purchase_date": "2025-12-01"}
    ]
}

# Routes
@app.post("/api/login")
def login(request: LoginRequest):
    print(f"Login attempt: {request.username}")
    
    # Check data status on login
    login_status = on_user_login(request.username)
    data_status = login_status.get("data_status", {})
    
    if request.username == "20201651":
        if request.password == "20201651":
            print(f"Login success: {request.username}")
            return {
                "status": "success", 
                "user": request.username, 
                "token": f"mock-token-{request.username}",
                "data_status": data_status,
                "needs_refresh": login_status.get("refresh_triggered", False)
            }
        else:
            print("Login failed: Invalid credentials for test account")
            return {"status": "error", "message": "비밀번호가 일치하지 않습니다."}
            
    if request.username in user_portfolios:
         print(f"Login success: {request.username}")
         return {
            "status": "success", 
            "user": request.username, 
            "token": f"mock-token-{request.username}",
            "data_status": data_status,
            "needs_refresh": login_status.get("refresh_triggered", False)
        }
    
    print(f"Login failed: User {request.username} not found")
    return {"status": "error", "message": "사용자를 찾을 수 없습니다. 회원가입을 해주세요."}

@app.post("/api/signup")
def signup(request: LoginRequest):
    print(f"Signup attempt: {request.username}")
    if request.username in user_portfolios:
        print("Signup failed: User exists")
        return {"status": "error", "message": "이미 존재하는 사용자입니다."}
    
    user_portfolios[request.username] = []
    print(f"Signup success: {request.username}")
    return {"status": "success", "message": "회원가입이 완료되었습니다."}


# Data Management APIs
@app.get("/api/data/status")
def get_data_status_endpoint():
    """Get the current status of all data types."""
    return get_data_status()


@app.post("/api/data/refresh")
def refresh_data_endpoint(force: bool = False):
    """
    Refresh all data (prices, news, etc.) if not already updated today.
    Set force=True to refresh even if already updated.
    """
    global stocks_data, news_data
    
    results = refresh_all_data(force=force)
    
    # Reload data after refresh
    if results["refreshed"]:
        stocks_data, news_data = load_data()
    
    return {
        "status": "success" if not results["errors"] else "partial",
        "results": results
    }

@app.get("/api/easy/portfolio")
def get_easy_portfolio(user: str = "20201651"):
    portfolio = user_portfolios.get(user, [])
    
    total_value = 0
    updated_portfolio = []
    
    # Build comprehensive stock info maps
    stock_info_map = {}
    for s in stocks_data.get("stocks", []):
        stock_info_map[s["code"]] = {
            "name": s.get("name", "Unknown"),
            "current_price": s.get("current_price", 0),
            "change_rate": s.get("change_rate", 0),
            "sector": s.get("sector", "Unknown")
        }
    
    my_stock_codes = set()
    
    for item in portfolio:
        code = item["code"]
        my_stock_codes.add(code)
        
        stock_info = stock_info_map.get(code, {})
        name = item.get("name", "") or stock_info.get("name", "Unknown Stock")
        current_price = stock_info.get("current_price", 70000)
        change_rate = stock_info.get("change_rate", 0)
        sector = stock_info.get("sector", "Unknown")
        
        value = item["amount"] * current_price
        total_value += value
        
        # Calculate change rate based on purchase price (not daily change)
        purchase_price = item.get("purchase_price", current_price)  # Default to current if not set
        purchase_value = item["amount"] * purchase_price
        
        if purchase_price > 0:
            change_rate = (current_price - purchase_price) / purchase_price
        else:
            change_rate = 0
        
        profit_loss = value - purchase_value  # Absolute profit/loss
        
        updated_portfolio.append({
            "code": code,
            "name": name,
            "amount": item["amount"],
            "value": value,
            "current_price": current_price,
            "purchase_price": purchase_price,
            "change_rate": round(change_rate, 4),
            "profit_loss": profit_loss,
            "sector": sector
        })

    # Build daily report with actual news
    report_lines = []
    for news in news_data:
        related = set(news.get("related_stocks", []))
        if related & my_stock_codes:
            news_content = news.get('content') or news.get('summary') or news.get('snippet', '')
            sentiment = news.get('sentiment', '')
            sentiment_emoji = "📈" if sentiment == "Positive" else ("📉" if sentiment == "Negative" else "📊")
            report_lines.append(f"{sentiment_emoji} **{news['title']}**\n{news_content}")
            
    if not report_lines:
        if portfolio:
            report_lines.append("보유 종목과 관련된 주요 뉴스가 없습니다. 시장 전체 흐름을 주시하세요.")
        else:
            report_lines.append("포트폴리오를 등록하면 맞춤형 AI 리포트가 제공됩니다.")
            
    daily_report = "\n\n".join(report_lines)

    return {
        "portfolio": updated_portfolio,
        "total_value": total_value,
        "daily_report": daily_report
    }

@app.post("/api/easy/portfolio/add")
def add_stock_to_portfolio(user: str = Body(..., embed=True), stock: PortfolioItem = Body(...)):
    if user not in user_portfolios:
        user_portfolios[user] = []
    
    stock_input = stock.code.strip() # This could be code or name
    found_stock = None
    
    # 1. Try to find by code
    found_stock = next((s for s in stocks_data.get("stocks", []) if s["code"] == stock_input), None)
    
    # 2. If not found, try to find by name
    if not found_stock:
        found_stock = next((s for s in stocks_data.get("stocks", []) if s["name"] == stock_input), None)
        
    if not found_stock:
        return {"status": "error", "message": "지원하지 않는 종목입니다."}
        
    stock_code = found_stock["code"]
    stock_name = found_stock["name"]
    current_price = found_stock.get("current_price", 0)  # Get current price for purchase_price
    
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
            
    existing_item = next((item for item in user_portfolios[user] if item["code"] == stock_code), None)
    
    if existing_item:
        # When adding more to existing position, calculate average purchase price
        old_total = existing_item["amount"] * existing_item.get("purchase_price", current_price)
        new_total = stock.amount * current_price
        new_amount = existing_item["amount"] + stock.amount
        avg_price = (old_total + new_total) / new_amount if new_amount > 0 else current_price
        
        existing_item["amount"] = new_amount
        existing_item["purchase_price"] = int(avg_price)
    else:
        user_portfolios[user].append({
            "code": stock_code,
            "name": stock_name,
            "amount": stock.amount,
            "purchase_price": current_price,
            "purchase_date": today
        })
        
    return {"status": "success", "portfolio": user_portfolios[user]}

@app.post("/api/easy/portfolio/remove")
def remove_stock_from_portfolio(
    user: str = Body(..., embed=True), 
    code: str = Body(..., embed=True),
    amount: int = Body(0, embed=True) # 0 means remove all
):
    if user not in user_portfolios:
        return {"status": "error", "message": "User not found"}
    
    portfolio = user_portfolios[user]
    target_item = next((item for item in portfolio if item["code"] == code), None)
    
    if not target_item:
        return {"status": "error", "message": "Stock not found in portfolio"}
    
    current_amount = target_item["amount"]
    
    # If amount is specified and valid (less than current), reduce custom amount
    if amount > 0 and amount < current_amount:
        target_item["amount"] -= amount
        # Update purchase_price? No, average price remains same when selling.
    else:
        # Remove entire item
        user_portfolios[user] = [item for item in portfolio if item["code"] != code]
        
    return {"status": "success", "portfolio": user_portfolios[user]}

@app.post("/api/easy/guru-analysis")
def analyze_portfolio(guru: str = Body(..., embed=True), portfolio: List[Dict] = Body(...)):
    """Enhanced Guru Analysis with real stock data, news, and technical indicators."""
    
    from ai_service import get_guru_config
    
    # Get guru configuration
    guru_config = get_guru_config(guru)
    
    # Build comprehensive stock info map
    stock_info_map = {}
    for s in stocks_data.get("stocks", []):
        stock_info_map[s["code"]] = {
            "name": s.get("name", "Unknown"),
            "current_price": s.get("current_price", 0),
            "change_rate": s.get("change_rate", 0),
            "sector": s.get("sector", "Unknown"),
            "description": s.get("description", "")
        }
    
    # Build detailed portfolio summary with real data
    portfolio_details = []
    indicator_details = []
    my_stock_codes = set()
    total_value = 0
    total_profit = 0
    
    for p in portfolio:
        code = p['code']
        my_stock_codes.add(code)
        stock_info = stock_info_map.get(code, {})
        
        current_price = p.get('current_price') or stock_info.get("current_price", 0)
        purchase_price = p.get('purchase_price', current_price)
        change_rate = p.get('change_rate') or stock_info.get("change_rate", 0)
        profit_loss = p.get('profit_loss', 0)
        sector = p.get('sector') or stock_info.get("sector", "Unknown")
        amount = p['amount']
        value = current_price * amount
        total_value += value
        total_profit += profit_loss
        
        change_str = f"+{change_rate*100:.1f}%" if change_rate >= 0 else f"{change_rate*100:.1f}%"
        profit_str = f"+{profit_loss:,}원" if profit_loss >= 0 else f"{profit_loss:,}원"
        
        portfolio_details.append(
            f"- {p['name']} ({code}): {amount}주, "
            f"매수가 {purchase_price:,}원 → 현재가 {current_price:,}원 ({change_str}, {profit_str}), "
            f"섹터: {sector}"
        )
        
        # Calculate technical indicators for this stock
        indicators = calculate_technical_indicators(code)
        if indicators:
            ind_lines = [f"  - {p['name']} 기술적 지표:"]
            if 'sma_50' in indicators:
                ind_lines.append(f"    50일 이평선: {indicators['sma_50']:,}원")
            if 'sma_200' in indicators:
                ind_lines.append(f"    200일 이평선: {indicators['sma_200']:,}원")
            if 'sma_200_slope' in indicators:
                slope_str = "상승" if indicators['sma_200_slope'] > 0 else "하락"
                ind_lines.append(f"    200일선 기울기: {slope_str} ({indicators['sma_200_slope']*100:.2f}%)")
            if 'week_52_high' in indicators:
                ind_lines.append(f"    52주 고가/저가: {indicators['week_52_high']:,} / {indicators['week_52_low']:,}원")
                ind_lines.append(f"    52주 범위 내 위치: {indicators.get('position_52w', 0)*100:.1f}%")
            
            indicator_details.append("\n".join(ind_lines))
    
    portfolio_str = f"""
총 포트폴리오 가치: {total_value:,}원
총 평가 손익: {'+' if total_profit >= 0 else ''}{total_profit:,}원
보유 종목 상세:
""" + "\n".join(portfolio_details)
    
    indicator_str = "\n".join(indicator_details) if indicator_details else "기술적 지표 데이터 없음"
    
    # Find relevant news with sentiment
    relevant_news = []
    for news in news_data:
        related = set(news.get("related_stocks", []))
        if related & my_stock_codes:
            news_content = news.get('content') or news.get('summary') or news.get('snippet', '')
            sentiment = news.get('sentiment', 'Neutral')
            relevant_news.append(f"- [{news['date']}] [{sentiment}] {news['title']}: {news_content}")
            
    if not relevant_news:
        # Include general recent news for market context
        for n in news_data[:3]:
            news_content = n.get('content') or n.get('summary') or n.get('snippet', '')
            sentiment = n.get('sentiment', 'Neutral')
            relevant_news.append(f"- [{n['date']}] [{sentiment}] {n['title']}: {news_content}")
        
    news_context = "\n".join(relevant_news)
    
    analysis = get_guru_analysis(portfolio_str, guru, news_context, indicator_str)
    
    return {
        "guru": guru,
        "guru_info": {
            "korean_name": guru_config["korean_name"],
            "image": guru_config["image"],
            "focus_areas": guru_config["focus_areas"],
            "description": guru_config["description"]
        },
        "analysis": analysis
    }

@app.get("/api/easy/graph")
def get_correlation_graph(user: str = "20201651"):
    """
    Get correlation graph for user's portfolio stocks.
    Uses price-based correlation and industry chain relationships.
    """
    from data_service import get_enhanced_correlations
    
    # Get user's portfolio stock codes
    portfolio = user_portfolios.get(user, [])
    portfolio_codes = [item["code"] for item in portfolio]
    
    if not portfolio_codes:
        # Fallback to default stocks if no portfolio
        portfolio_codes = ["005930", "000660", "035420"]
    
    try:
        result = get_enhanced_correlations(portfolio_codes)
        return result
    except Exception as e:
        print(f"Error calculating correlations: {e}")
        # Fallback to old logic
        if "correlation" not in stocks_data:
            return {"nodes": [], "links": []}
        
        corr = stocks_data["correlation"]
        stocks = stocks_data["stocks"]
        
        nodes = [{"id": s["code"], "name": s["name"], "group": 1} for s in stocks]
        links = []
        
        stock_codes = [s["code"] for s in stocks]
        
        for i in range(len(stock_codes)):
            for j in range(i + 1, len(stock_codes)):
                code1 = stock_codes[i]
                code2 = stock_codes[j]
                val = corr.get(code1, {}).get(code2, 0)
                
                if abs(val) > 0.3: 
                    links.append({"source": code1, "target": code2, "value": abs(val)})
                    
        return {"nodes": nodes, "links": links}

# Default tone watch stocks (SK하이닉스, 두산, 두산에너빌리티, 롯데에너지머티리얼즈, 삼성SDI, 삼성전자, 한중엔시에스, 현대건설)
TONE_WATCH_STOCKS = {
    "000660": "SK하이닉스",
    "000150": "두산",
    "034020": "두산에너빌리티",
    "373220": "LG에너지솔루션",  # 롯데에너지머티리얼즈 대체 (롯데에너지머티리얼즈: 051910)
    "006400": "삼성SDI",
    "005930": "삼성전자",
    "363280": "한중엔시에스",
    "000720": "현대건설"
}

# In-memory storage for tone watch list (per user)
user_tone_watch = {
    "20201651": list(TONE_WATCH_STOCKS.keys())
}

@app.get("/api/expert/stocks")
def get_expert_stocks():
    """Get all 350 stocks with price data from CSV files."""
    from data_service import calculate_technical_indicators, get_stock_info
    
    all_stocks = []
    
    # Read tickers from file
    tickers_file = os.path.join(os.path.dirname(__file__), "crawler", "tickers.txt")
    
    # Get stock names from KOSPI_KOSDAQ.csv (via data_service)
    stock_names = get_stock_info()
    
    if os.path.exists(tickers_file):
        with open(tickers_file, "r", encoding="utf-8") as f:
            tickers = [line.strip() for line in f if line.strip()]
        
        for code in tickers:
            indicators = calculate_technical_indicators(code)
            stock_info = stock_names.get(code, {})
            
            if indicators.get("current_price"):
                all_stocks.append({
                    "code": code,
                    "name": stock_info.get("name", code),
                    "current_price": indicators.get("current_price", 0),
                    "change_rate": indicators.get("change_rate", 0),
                    "sector": stock_info.get("sector", "기타"),
                    "sma_50": indicators.get("sma_50"),
                    "sma_200": indicators.get("sma_200"),
                    "week_52_high": indicators.get("week_52_high"),
                    "week_52_low": indicators.get("week_52_low")
                })
    
    # Fall back to stocks.json if no price data
    if not all_stocks:
        return stocks_data.get("stocks", [])
    
    return all_stocks

@app.get("/api/expert/tone-watch")
def get_tone_watch_list(user: str = "20201651"):
    """Get the user's tone watch stock list."""
    watch_codes = user_tone_watch.get(user, list(TONE_WATCH_STOCKS.keys()))
    
    # Build full stock info list
    stocks = []
    for code in watch_codes:
        name = TONE_WATCH_STOCKS.get(code, "")
        # Try to get from stocks_data if not in default list
        if not name:
            for s in stocks_data.get("stocks", []):
                if s["code"] == code:
                    name = s["name"]
                    break
        stocks.append({"code": code, "name": name or code})
    
    return {"stocks": stocks}

@app.post("/api/expert/tone-watch/add")
def add_tone_watch_stock(user: str = Body(..., embed=True), code: str = Body(..., embed=True)):
    """Add a stock to user's tone watch list."""
    if user not in user_tone_watch:
        user_tone_watch[user] = list(TONE_WATCH_STOCKS.keys())
    
    if code not in user_tone_watch[user]:
        user_tone_watch[user].append(code)
    
    return {"status": "success", "watch_list": user_tone_watch[user]}

@app.post("/api/expert/tone-watch/remove")
def remove_tone_watch_stock(user: str = Body(..., embed=True), code: str = Body(..., embed=True)):
    """Remove a stock from user's tone watch list."""
    if user not in user_tone_watch:
        user_tone_watch[user] = list(TONE_WATCH_STOCKS.keys())
    
    if code in user_tone_watch[user]:
        user_tone_watch[user].remove(code)
    
    return {"status": "success", "watch_list": user_tone_watch[user]}

@app.get("/api/expert/tone-changes")
def get_tone_changes(user: str = "20201651"):
    """Generate tone changes based on report analysis for watched stocks."""
    from report_service import analyze_tone_change, COMPANY_CODE_MAP
    from data_service import get_stock_info
    
    # Reverse mapping: code -> company name
    code_to_company = {v: k for k, v in COMPANY_CODE_MAP.items()}
    stock_info = get_stock_info()
    
    changed_stocks = []
    
    # Get user's watch list
    watch_codes = set(user_tone_watch.get(user, list(TONE_WATCH_STOCKS.keys())))
    
    for code in watch_codes:
        company_name = code_to_company.get(code)
        
        if company_name:
            # Use report analysis
            analysis = analyze_tone_change(company_name)
            
            if analysis.get("has_reports"):
                changed_stocks.append({
                    "code": code,
                    "name": company_name,
                    "change": analysis.get("overall_sentiment", "Neutral"),
                    "tone_change": analysis.get("tone_change", "Unknown"),
                    "change_description": analysis.get("change_description", ""),
                    "sentiment_score": analysis.get("average_sentiment", 0),
                    "score_diff": analysis.get("score_diff", 0),
                    "report_count": analysis.get("report_count", 0),
                    "reason": f"{analysis.get('report_count', 0)}개 리포트 분석 결과",
                    "latest_report": analysis.get("latest_report"),
                    "news_count": analysis.get("report_count", 0)
                })
            else:
                # Fallback to news-based sentiment
                name = TONE_WATCH_STOCKS.get(code) or stock_info.get(code, {}).get("name", code)
                changed_stocks.append({
                    "code": code,
                    "name": name,
                    "change": "Neutral",
                    "tone_change": "Unknown",
                    "change_description": "리포트 없음",
                    "sentiment_score": 0,
                    "score_diff": 0,
                    "report_count": 0,
                    "reason": "분석 가능한 리포트 없음",
                    "news_count": 0
                })
        else:
            # No report available, use simple news-based
            name = TONE_WATCH_STOCKS.get(code) or stock_info.get(code, {}).get("name", code)
            changed_stocks.append({
                "code": code,
                "name": name,
                "change": "Neutral",
                "tone_change": "Unknown",
                "change_description": "리포트 없음",
                "sentiment_score": 0,
                "score_diff": 0,
                "report_count": 0,
                "reason": "분석 가능한 리포트 없음",
                "news_count": 0
            })
    
    # Sort by sentiment score (most negative first for attention)
    changed_stocks.sort(key=lambda x: x.get("sentiment_score", 0))
    
    return changed_stocks

@app.get("/api/expert/report-analysis/{company}")
def get_report_analysis(company: str):
    """Get detailed report analysis for a company."""
    from report_service import analyze_tone_change
    return analyze_tone_change(company)

@app.get("/api/expert/stock-news/{code}")
def get_stock_news(code: str):
    """Get news related to a specific stock."""
    from data_service import get_stock_info
    
    related_news = []
    stock_info = get_stock_info()
    
    for news in news_data:
        if code in news.get("related_stocks", []):
            related_news.append({
                "title": news.get("title", ""),
                "date": news.get("date", ""),
                "sentiment": news.get("sentiment", "Neutral"),
                "content": news.get("content") or news.get("summary") or news.get("snippet", "")
            })
    
    # Get stock name from KOSPI_KOSDAQ data
    stock_name = stock_info.get(code, {}).get("name", code)
    stock_name = TONE_WATCH_STOCKS.get(code, stock_name)
    
    return {
        "code": code,
        "name": stock_name,
        "news": related_news
    }


# In-memory storage for stock keywords (per user, per stock)
user_stock_keywords = {}

@app.get("/api/expert/stock-keywords/{code}")
def get_stock_keywords(code: str, user: str = "20201651"):
    """Get keywords for a specific stock."""
    user_keywords = user_stock_keywords.get(user, {})
    return {"code": code, "keywords": user_keywords.get(code, [])}

@app.post("/api/expert/stock-keywords/add")
def add_stock_keyword(
    user: str = Body(..., embed=True),
    code: str = Body(..., embed=True),
    keyword: str = Body(..., embed=True)
):
    """Add a keyword for a stock."""
    if user not in user_stock_keywords:
        user_stock_keywords[user] = {}
    if code not in user_stock_keywords[user]:
        user_stock_keywords[user][code] = []
    
    keyword = keyword.strip()
    if keyword and keyword not in user_stock_keywords[user][code]:
        user_stock_keywords[user][code].append(keyword)
    
    return {"status": "success", "keywords": user_stock_keywords[user][code]}

@app.post("/api/expert/stock-keywords/remove")
def remove_stock_keyword(
    user: str = Body(..., embed=True),
    code: str = Body(..., embed=True),
    keyword: str = Body(..., embed=True)
):
    """Remove a keyword for a stock."""
    if user in user_stock_keywords and code in user_stock_keywords[user]:
        if keyword in user_stock_keywords[user][code]:
            user_stock_keywords[user][code].remove(keyword)
    
    return {"status": "success", "keywords": user_stock_keywords.get(user, {}).get(code, [])}

@app.get("/api/expert/news/search")
def search_news_by_keyword(keyword: str, code: str = None):
    """Search news by keyword, optionally filtered by stock code."""
    from data_service import get_stock_info
    
    matching_news = []
    keyword_lower = keyword.lower()
    stock_info = get_stock_info()
    
    for news in news_data:
        # Check if keyword matches in title or content
        title = news.get("title", "").lower()
        content = (news.get("content") or news.get("summary") or news.get("snippet", "")).lower()
        
        if keyword_lower in title or keyword_lower in content:
            # If code is specified, also check if news is related to that stock
            if code and code not in news.get("related_stocks", []):
                continue
            
            matching_news.append({
                "title": news.get("title", ""),
                "date": news.get("date", ""),
                "sentiment": news.get("sentiment", "Neutral"),
                "content": news.get("content") or news.get("summary") or news.get("snippet", ""),
                "related_stocks": news.get("related_stocks", [])
            })
    
    return {
        "keyword": keyword,
        "code": code,
        "count": len(matching_news),
        "news": matching_news
    }

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    context: str = ""

@app.post("/api/chat")
def chat(request: ChatRequest):
    # Fetch recent news for context
    recent_news = [f"- [{n['date']}] {n['title']}" for n in news_data[:5]]
    news_context = "\n".join(recent_news)
    
    full_context = f"{request.context}\n\nRecent Market News:\n{news_context}"
    
    # Use Real AI Service
    response = get_chat_response(request.history, request.message, full_context)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
