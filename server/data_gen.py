import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_stocks_data():
    stocks = [
        {"code": "005930", "name": "삼성전자", "market": "KOSPI", "sector": "반도체"},
        {"code": "000660", "name": "SK하이닉스", "market": "KOSPI", "sector": "반도체"},
        {"code": "035420", "name": "NAVER", "market": "KOSPI", "sector": "IT"},
        {"code": "035720", "name": "카카오", "market": "KOSPI", "sector": "IT"},
        {"code": "005380", "name": "현대차", "market": "KOSPI", "sector": "자동차"},
        {"code": "000270", "name": "기아", "market": "KOSPI", "sector": "자동차"},
        {"code": "051910", "name": "LG화학", "market": "KOSPI", "sector": "화학"},
        {"code": "006400", "name": "삼성SDI", "market": "KOSPI", "sector": "배터리"},
        {"code": "373220", "name": "LG에너지솔루션", "market": "KOSPI", "sector": "배터리"},
        {"code": "207940", "name": "삼성바이오로직스", "market": "KOSPI", "sector": "바이오"},
    ]

    # Generate price history for correlation
    dates = pd.date_range(end=datetime.today(), periods=100).strftime("%Y-%m-%d").tolist()
    price_data = {}
    
    for stock in stocks:
        base_price = random.randint(50000, 500000)
        prices = [base_price]
        for _ in range(99):
            change = random.uniform(-0.03, 0.03)
            prices.append(int(prices[-1] * (1 + change)))
        
        stock["current_price"] = prices[-1]
        stock["market_cap"] = prices[-1] * random.randint(1000000, 10000000)
        stock["price_history"] = dict(zip(dates, prices))
        
        # Analyst Report Mock
        sentiments = ["Positive", "Neutral", "Negative"]
        stock["analyst_reports"] = [
            {
                "date": (datetime.today() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "sentiment": random.choice(sentiments),
                "summary": f"{stock['name']}에 대한 {random.choice(sentiments)}적인 전망입니다.",
                "tone_score": random.uniform(0, 10) # 0: Negative, 10: Positive
            }
        ]
        
        price_data[stock["code"]] = prices

    # Calculate Correlation Matrix
    df = pd.DataFrame(price_data)
    corr_matrix = df.corr().to_dict()
    
    return stocks, corr_matrix

def generate_news_data(stocks):
    news_templates = [
        "{name}, 3분기 실적 발표... 예상치 상회",
        "{name}, 신규 수주 계약 체결 소식에 강세",
        "{name}, 글로벌 경기 침체 우려에 약세",
        "{name}, 외국인 매수세 유입... 주가 상승",
        "{name}, 신제품 출시 기대감 고조"
    ]
    
    news_list = []
    for i in range(20):
        stock = random.choice(stocks)
        news_list.append({
            "id": i + 1,
            "related_stocks": [stock["code"]],
            "title": news_templates[random.randint(0, 4)].format(name=stock["name"]),
            "date": (datetime.today() - timedelta(days=random.randint(0, 7))).strftime("%Y-%m-%d"),
            "keywords": [stock["sector"], "실적", "전망"],
            "summary": "뉴스 요약 내용입니다..."
        })
    return news_list

if __name__ == "__main__":
    stocks, corr = generate_stocks_data()
    news = generate_news_data(stocks)
    
    with open("stocks.json", "w", encoding="utf-8") as f:
        json.dump({"stocks": stocks, "correlation": corr}, f, ensure_ascii=False, indent=2)
        
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    
    print("Mock data generated successfully.")
