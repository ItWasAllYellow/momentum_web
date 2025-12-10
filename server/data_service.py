"""
Data Service Module
Handles automatic data refresh on login and indicator calculations.
"""

from __future__ import annotations
import os
import json
import csv
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_DATA_DIR = os.path.join(DATA_DIR, "price_data")
FINANCIAL_DATA_DIR = os.path.join(DATA_DIR, "financial_data")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")
STOCKS_FILE = os.path.join(BASE_DIR, "..", "stocks.json")
NEWS_FILE = os.path.join(BASE_DIR, "..", "news.json")
TICKERS_FILE = os.path.join(BASE_DIR, "crawler", "tickers.txt")
OPM_FILE = os.path.join(BASE_DIR, "..", "to_be_used", "code", "OPM(영업이익률).xlsx")
KOSPI_KOSDAQ_FILE = os.path.join(BASE_DIR, "..", "AICapstoneDesign_analysis", "KOSPI_KOSDAQ.csv")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PRICE_DATA_DIR, exist_ok=True)
os.makedirs(FINANCIAL_DATA_DIR, exist_ok=True)

# Sector classification based on company name keywords
SECTOR_KEYWORDS = {
    "반도체": ["반도체", "하이닉스", "삼성전자", "SK하이닉스", "메모리", "칩", "실리콘", "파운드리"],
    "2차전지": ["배터리", "에너지솔루션", "SDI", "에코프로", "LG에너지", "천보", "엘앤에프", "포스코퓨처엠"],
    "바이오/제약": ["바이오", "제약", "헬스", "메디", "셀트리온", "약품", "사이언스", "젠", "텍", "휴젤", "파마"],
    "자동차/부품": ["자동차", "모비스", "현대차", "기아", "위아", "오토", "타이어", "모빌리티"],
    "금융": ["금융", "증권", "보험", "은행", "지주", "카드", "캐피탈", "투자"],
    "IT/소프트웨어": ["소프트", "게임즈", "엔터", "네이버", "카카오", "엔씨", "크래프톤", "넥슨", "컴퓨터"],
    "화학": ["화학", "케미칼", "석유", "정밀화학", "소재"],
    "철강/금속": ["철강", "스틸", "아연", "금속", "포스코"],
    "건설": ["건설", "건축", "시멘트", "HDC"],
    "조선/해양": ["조선", "해양", "해운", "HMM", "한진"],
    "전자/전기": ["전자", "전기", "LG전자", "삼성전기", "이노텍"],
    "통신": ["통신", "텔레콤", "KT", "SKT", "LG유플"],
    "유통/소비재": ["마트", "쇼핑", "리테일", "롯데", "신세계", "이마트"],
    "식품/음료": ["식품", "음료", "푸드", "농심", "오리온", "CJ제일", "삼양"],
    "에너지/유틸리티": ["에너지", "전력", "가스", "한전", "S-Oil"],
    "항공/우주": ["항공", "우주", "에어로", "한국항공"],
    "엔터테인먼트": ["엔터", "JYP", "SM", "하이브", "YG"],
    "디스플레이": ["디스플레이", "LCD", "OLED"],
    "기계/장비": ["기계", "장비", "로봇", "시스템"],
}

def get_sector_from_name(name: str) -> str:
    """Determine sector from company name using keywords."""
    name_lower = name.lower()
    for sector, keywords in SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in name_lower:
                return sector
    return "기타"


def load_stock_names() -> Dict[str, Dict[str, str]]:
    """Load stock names and sectors from KOSPI_KOSDAQ.csv."""
    stock_info = {}
    
    if os.path.exists(KOSPI_KOSDAQ_FILE):
        try:
            with open(KOSPI_KOSDAQ_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get("Code", "").strip()
                    name = row.get("Name", "").strip()
                    if code and name:
                        sector = get_sector_from_name(name)
                        stock_info[code] = {"name": name, "sector": sector}
        except Exception as e:
            print(f"Error loading stock names: {e}")
    
    return stock_info


# Global cache for stock names
_STOCK_INFO_CACHE = None

def get_stock_info() -> Dict[str, Dict[str, str]]:
    """Get cached stock info or load from file."""
    global _STOCK_INFO_CACHE
    if _STOCK_INFO_CACHE is None:
        _STOCK_INFO_CACHE = load_stock_names()
    return _STOCK_INFO_CACHE


def get_today_kst() -> str:
    """Get today's date in KST timezone as YYYY-MM-DD string."""
    try:
        return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def load_metadata() -> Dict[str, Any]:
    """Load metadata file containing last update timestamps."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(metadata: Dict[str, Any]) -> None:
    """Save metadata file."""
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def should_refresh(data_type: str) -> bool:
    """Check if the data type needs to be refreshed (not updated today)."""
    metadata = load_metadata()
    last_update = metadata.get(data_type, {}).get("last_update", "")
    today = get_today_kst()
    return last_update != today


def refresh_price_data() -> Dict[str, Any]:
    """
    Refresh stock price data by running the crawler.
    Uses append logic to only fetch new data since last update.
    """
    result = {
        "success": False,
        "message": "",
        "updated_count": 0
    }
    
    try:
        # Run the price crawler for all tickers
        crawler_script = os.path.join(BASE_DIR, "crawler", "append_stock_prices.py")
        cmd = [
            "python", crawler_script,
            "--tickers", TICKERS_FILE,
            "--outdir", PRICE_DATA_DIR,
            "--cnt", "30",
            "--sleep-sec", "0.3"
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=600  # 10 minute timeout for 350 stocks
        )
        
        if process.returncode == 0:
            # Count updated files
            csv_files = [f for f in os.listdir(PRICE_DATA_DIR) if f.endswith('.csv')]
            result["updated_count"] = len(csv_files)
            result["success"] = True
            result["message"] = f"Successfully updated {len(csv_files)} stock price files"
            
            # Update metadata
            metadata = load_metadata()
            metadata["price_data"] = {
                "last_update": get_today_kst(),
                "file_count": len(csv_files)
            }
            save_metadata(metadata)
        else:
            result["message"] = f"Crawler failed: {process.stderr[:500]}"
            
    except subprocess.TimeoutExpired:
        result["message"] = "Price data refresh timed out"
    except Exception as e:
        result["message"] = f"Error refreshing price data: {str(e)}"
    
    return result


def refresh_news_data() -> Dict[str, Any]:
    """Refresh news data by running the news crawler."""
    result = {
        "success": False,
        "message": "",
        "news_count": 0
    }
    
    try:
        # Run the news crawler
        crawler_script = os.path.join(BASE_DIR, "crawler", "news_naver.py")
        
        if not os.path.exists(crawler_script):
            result["message"] = "News crawler script not found"
            return result
            
        process = subprocess.run(
            ["python", crawler_script],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode == 0:
            result["success"] = True
            result["message"] = "Successfully updated news data"
            
            # Update metadata
            metadata = load_metadata()
            metadata["news_data"] = {
                "last_update": get_today_kst()
            }
            save_metadata(metadata)
        else:
            result["message"] = f"News crawler failed: {process.stderr[:200]}"
            
    except subprocess.TimeoutExpired:
        result["message"] = "News data refresh timed out"
    except Exception as e:
        result["message"] = f"Error refreshing news data: {str(e)}"
    
    return result


def calculate_technical_indicators(code: str) -> Dict[str, Any]:
    """
    Calculate technical indicators for a single stock.
    Returns SMA, RS, 52-week high/low, etc.
    """
    indicators = {}
    csv_path = os.path.join(PRICE_DATA_DIR, f"{code}.csv")
    
    if not os.path.exists(csv_path):
        return indicators
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if len(rows) < 2:
            return indicators
        
        # Extract close prices (rows are sorted descending, newest first)
        closes = []
        for row in rows:
            try:
                closes.append(float(row.get("close", 0)))
            except (ValueError, TypeError):
                closes.append(0)
        
        # Current price and change
        current_price = closes[0] if closes else 0
        prev_price = closes[1] if len(closes) > 1 else current_price
        change_rate = (current_price - prev_price) / prev_price if prev_price else 0
        
        indicators["current_price"] = int(current_price)
        indicators["change_rate"] = round(change_rate, 4)
        
        # SMA calculations
        if len(closes) >= 50:
            indicators["sma_50"] = round(sum(closes[:50]) / 50, 2)
        if len(closes) >= 150:
            indicators["sma_150"] = round(sum(closes[:150]) / 150, 2)
        if len(closes) >= 200:
            indicators["sma_200"] = round(sum(closes[:200]) / 200, 2)
            # SMA 200 slope (compare current vs 20 days ago)
            if len(closes) >= 220:
                sma_200_now = sum(closes[:200]) / 200
                sma_200_20d_ago = sum(closes[20:220]) / 200
                indicators["sma_200_slope"] = round((sma_200_now - sma_200_20d_ago) / sma_200_20d_ago, 4) if sma_200_20d_ago else 0
        
        # 52 week high/low (approximately 252 trading days)
        year_closes = closes[:min(252, len(closes))]
        if year_closes:
            indicators["week_52_high"] = int(max(year_closes))
            indicators["week_52_low"] = int(min(year_closes))
            # Position relative to 52-week range
            range_52w = indicators["week_52_high"] - indicators["week_52_low"]
            if range_52w > 0:
                indicators["position_52w"] = round((current_price - indicators["week_52_low"]) / range_52w, 2)
        
    except Exception as e:
        print(f"Error calculating indicators for {code}: {e}")
    
    return indicators


def load_opm_data() -> Dict[str, float]:
    """
    Load OPM (Operating Profit Margin) data from Excel file.
    Returns dict mapping stock code to latest OPM value.
    """
    opm_data = {}
    
    if not os.path.exists(OPM_FILE):
        print(f"OPM file not found: {OPM_FILE}")
        return opm_data
    
    try:
        import pandas as pd
        df = pd.read_excel(OPM_FILE)
        
        # Find the row with stock codes (row index 6 in the data)
        # and the last row with actual data (before NaN rows)
        for col_idx in range(1, len(df.columns)):
            col = df.columns[col_idx]
            # Get stock code from row 6 (index 6)
            code_raw = df.iloc[6, col_idx] if len(df) > 6 else None
            if code_raw and isinstance(code_raw, str) and code_raw.startswith('A'):
                code = code_raw[1:]  # Remove 'A' prefix
                
                # Get latest OPM value (find last non-NaN value in this column)
                for row_idx in range(len(df) - 1, 12, -1):  # Start from bottom, data starts at row 13
                    val = df.iloc[row_idx, col_idx]
                    if pd.notna(val):
                        try:
                            opm_data[code] = float(val)
                        except (ValueError, TypeError):
                            pass
                        break
                        
    except ImportError:
        print("pandas/openpyxl not installed, skipping OPM data load")
    except Exception as e:
        print(f"Error loading OPM data: {e}")
    
    return opm_data


def get_data_status() -> Dict[str, Any]:
    """Get the current status of all data types."""
    metadata = load_metadata()
    today = get_today_kst()
    
    # Count price data files
    price_files = 0
    if os.path.exists(PRICE_DATA_DIR):
        price_files = len([f for f in os.listdir(PRICE_DATA_DIR) if f.endswith('.csv')])
    
    return {
        "today": today,
        "price_data": {
            "last_update": metadata.get("price_data", {}).get("last_update", "Never"),
            "needs_refresh": should_refresh("price_data"),
            "file_count": price_files
        },
        "news_data": {
            "last_update": metadata.get("news_data", {}).get("last_update", "Never"),
            "needs_refresh": should_refresh("news_data")
        },
        "financial_data": {
            "last_update": metadata.get("financial_data", {}).get("last_update", "Never"),
            "needs_refresh": should_refresh("financial_data")
        }
    }


def refresh_all_data(force: bool = False) -> Dict[str, Any]:
    """
    Refresh all data types if needed.
    If force=True, refresh even if already updated today.
    """
    results = {
        "refreshed": [],
        "skipped": [],
        "errors": []
    }
    
    # Refresh price data
    if force or should_refresh("price_data"):
        price_result = refresh_price_data()
        if price_result["success"]:
            results["refreshed"].append(f"price_data: {price_result['message']}")
        else:
            results["errors"].append(f"price_data: {price_result['message']}")
    else:
        results["skipped"].append("price_data (already updated today)")
    
    # Refresh news data
    if force or should_refresh("news_data"):
        news_result = refresh_news_data()
        if news_result["success"]:
            results["refreshed"].append(f"news_data: {news_result['message']}")
        else:
            results["errors"].append(f"news_data: {news_result['message']}")
    else:
        results["skipped"].append("news_data (already updated today)")
    
    return results


def on_user_login(user_id: str) -> Dict[str, Any]:
    """
    Called when a user logs in.
    Triggers data refresh if data is stale (not updated today).
    Returns status information.
    """
    status = get_data_status()
    
    # Check if any data needs refresh
    needs_refresh = (
        status["price_data"]["needs_refresh"] or
        status["news_data"]["needs_refresh"]
    )
    
    result = {
        "user_id": user_id,
        "data_status": status,
        "refresh_triggered": needs_refresh,
        "refresh_results": None
    }
    
    if needs_refresh:
        # Run refresh in background or synchronously depending on preference
        # For now, just note that refresh is needed
        # The actual refresh can be triggered via /api/data/refresh endpoint
        result["message"] = "Data refresh needed. Call /api/data/refresh to update."
    else:
        result["message"] = "All data is up to date."
    
    return result


if __name__ == "__main__":
    # Test the service
    print("Data Status:", get_data_status())
    print("\nTesting OPM load...")
    opm = load_opm_data()
    print(f"Loaded OPM for {len(opm)} stocks")
    if opm:
        sample = list(opm.items())[:5]
        print("Sample:", sample)


def get_price_series(code: str, days: int = 60) -> List[float]:
    """
    Get closing price series for a stock.
    Returns list of prices, newest first.
    """
    csv_path = os.path.join(PRICE_DATA_DIR, f"{code}.csv")
    
    if not os.path.exists(csv_path):
        return []
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        closes = []
        for row in rows[:days]:
            try:
                closes.append(float(row.get("close", 0)))
            except (ValueError, TypeError):
                pass
        
        return closes
    except Exception as e:
        print(f"Error reading price series for {code}: {e}")
        return []


def calculate_correlation(prices1: List[float], prices2: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient between two price series.
    """
    if len(prices1) < 10 or len(prices2) < 10:
        return 0.0
    
    # Align lengths
    n = min(len(prices1), len(prices2))
    p1 = prices1[:n]
    p2 = prices2[:n]
    
    # Calculate means
    mean1 = sum(p1) / n
    mean2 = sum(p2) / n
    
    # Calculate correlation
    numerator = sum((p1[i] - mean1) * (p2[i] - mean2) for i in range(n))
    
    std1 = (sum((p - mean1) ** 2 for p in p1) / n) ** 0.5
    std2 = (sum((p - mean2) ** 2 for p in p2) / n) ** 0.5
    
    if std1 == 0 or std2 == 0:
        return 0.0
    
    return numerator / (n * std1 * std2)


def calculate_stock_correlations(stock_codes: List[str], days: int = 60) -> Dict[str, Dict[str, float]]:
    """
    Calculate pairwise correlations between stocks based on price data.
    Returns nested dict: {code1: {code2: correlation, ...}, ...}
    """
    # Load price series for all stocks
    price_data = {}
    for code in stock_codes:
        prices = get_price_series(code, days)
        if prices:
            price_data[code] = prices
    
    # Calculate pairwise correlations
    correlations = {}
    codes_with_data = list(price_data.keys())
    
    for i, code1 in enumerate(codes_with_data):
        correlations[code1] = {}
        for code2 in codes_with_data[i+1:]:
            corr = calculate_correlation(price_data[code1], price_data[code2])
            correlations[code1][code2] = round(corr, 3)
            # Also store reverse direction
            if code2 not in correlations:
                correlations[code2] = {}
            correlations[code2][code1] = round(corr, 3)
    
    return correlations


# Industry chain relationships (loaded from Excel files)
INDUSTRY_CHAINS = {
    # Semiconductor supply chain
    "반도체": {
        "description": "반도체 산업 체인",
        "companies": {
            "005930": {"name": "삼성전자", "role": "IDM (설계+제조)"},
            "000660": {"name": "SK하이닉스", "role": "메모리 반도체"},
            "042700": {"name": "한미반도체", "role": "장비"},
            "036830": {"name": "솔브레인홀딩스", "role": "소재"},
        },
        "relationships": [
            ("005930", "000660", 0.8, "경쟁사/동종업"),
            ("005930", "042700", 0.5, "고객-장비사"),
            ("000660", "042700", 0.5, "고객-장비사"),
        ]
    },
    # ESS/Energy storage
    "ESS": {
        "description": "ESS/에너지저장 산업 체인",
        "companies": {},
        "relationships": []
    },
    # Nuclear power
    "원전": {
        "description": "원자력 산업 체인",
        "companies": {},
        "relationships": []
    }
}


def get_enhanced_correlations(portfolio_codes: List[str]) -> Dict[str, Any]:
    """
    Get enhanced correlation data combining:
    1. Price-based statistical correlation
    2. Industry chain relationships
    
    Returns data optimized for force graph visualization.
    """
    # 1. Calculate price correlations for portfolio stocks
    all_codes = set(portfolio_codes)
    
    # Add related stocks from industry chains
    for chain_name, chain_data in INDUSTRY_CHAINS.items():
        for code in portfolio_codes:
            if code in chain_data["companies"]:
                # Add other companies in the same chain
                all_codes.update(chain_data["companies"].keys())
    
    all_codes = list(all_codes)
    
    # 2. Calculate statistical correlations
    price_correlations = calculate_stock_correlations(all_codes)
    
    # 3. Build nodes and links
    nodes = []
    links = []
    
    # Load stock names from stocks.json
    stock_names = {}
    try:
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            stocks_data = json.load(f)
            for s in stocks_data.get("stocks", []):
                stock_names[s["code"]] = s["name"]
    except:
        pass
    
    # Add industry chain company names
    for chain_data in INDUSTRY_CHAINS.values():
        for code, info in chain_data["companies"].items():
            if code not in stock_names:
                stock_names[code] = info["name"]
    
    # Create nodes
    for code in all_codes:
        name = stock_names.get(code, code)
        node = {"id": code, "name": name, "group": 1}
        
        # Determine group based on industry chain
        for chain_name, chain_data in INDUSTRY_CHAINS.items():
            if code in chain_data["companies"]:
                node["industry"] = chain_name
                node["role"] = chain_data["companies"][code].get("role", "")
                break
        
        nodes.append(node)
    
    # Create links from price correlations
    added_links = set()
    for code1, corr_dict in price_correlations.items():
        for code2, corr_value in corr_dict.items():
            if abs(corr_value) > 0.3:  # Threshold for significant correlation
                link_key = tuple(sorted([code1, code2]))
                if link_key not in added_links:
                    links.append({
                        "source": code1,
                        "target": code2,
                        "value": abs(corr_value),
                        "type": "price_correlation",
                        "correlation": corr_value
                    })
                    added_links.add(link_key)
    
    # Add industry chain links (override/supplement price correlations)
    for chain_data in INDUSTRY_CHAINS.values():
        for rel in chain_data["relationships"]:
            code1, code2, strength, rel_type = rel
            if code1 in all_codes and code2 in all_codes:
                link_key = tuple(sorted([code1, code2]))
                # Check if link already exists
                existing = next((l for l in links if tuple(sorted([l["source"], l["target"]])) == link_key), None)
                if existing:
                    # Boost the value for industry-related stocks
                    existing["value"] = max(existing["value"], strength)
                    existing["relationship"] = rel_type
                else:
                    links.append({
                        "source": code1,
                        "target": code2,
                        "value": strength,
                        "type": "industry_chain",
                        "relationship": rel_type
                    })
    
    return {
        "nodes": nodes,
        "links": links,
        "correlations": price_correlations
    }
