"""
Report Analysis Service
Analyzes analyst reports to detect tone changes and sentiment.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

# Path to reports directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "..", "to_be_used", "report")

# Investment opinion keywords
OPINION_KEYWORDS = {
    "Buy": ["Buy", "매수", "Strong Buy", "적극 매수", "비중확대", "Overweight"],
    "Hold": ["Hold", "보유", "중립", "Neutral", "Market Perform", "시장수익률"],
    "Sell": ["Sell", "매도", "비중축소", "Underweight", "Reduce"]
}

# Positive/Negative sentiment keywords for Korean financial context
POSITIVE_KEYWORDS = [
    "호실적", "상승", "성장", "확대", "개선", "호조", "최대", "강세",
    "기대", "수혜", "매수", "목표주가 상향", "실적 서프라이즈",
    "초호황", "급등", "돌파", "사상 최고", "Top-pick", "상승여력",
    "흑자전환", "턴어라운드", "회복", "급증", "폭발적"
]

NEGATIVE_KEYWORDS = [
    "부진", "하락", "감소", "악화", "둔화", "약세", "하향", "적자",
    "매도", "목표주가 하향", "실적 쇼크", "리스크", "우려",
    "급락", "적전", "손실", "부정적", "비관적", "어려움", "난관"
]

# Company name to code mapping
COMPANY_CODE_MAP = {
    "SK하이닉스": "000660",
    "두산": "000150",
    "두산에너빌리티": "034020",
    "롯데에너지머티리얼즈": "051910",
    "삼성SDI": "006400",
    "삼성전자": "005930",
    "한중엔시에스": "363280",
    "현대건설": "000720"
}


def parse_report_filename(filename: str) -> Dict[str, str]:
    """
    Parse report filename to extract metadata.
    Format: {종목명}[{종목코드}]_{날짜}_{증권사}_{ID}.md
    """
    try:
        # Remove .md extension
        name = filename.replace(".md", "")
        parts = name.split("_")
        
        if len(parts) >= 4:
            # Extract company and code from first part
            company_part = parts[0]
            code_match = re.search(r'[（\[](\d+)[）\]]', company_part)
            code = code_match.group(1) if code_match else ""
            company = re.sub(r'[（\[]\d+[）\]]', '', company_part).strip()
            
            return {
                "company": company,
                "code": code,
                "date": parts[1] if len(parts) > 1 else "",
                "broker": parts[2] if len(parts) > 2 else "",
                "report_id": parts[3] if len(parts) > 3 else ""
            }
    except Exception as e:
        print(f"Error parsing filename {filename}: {e}")
    
    return {"company": "", "code": "", "date": "", "broker": "", "report_id": ""}


def extract_investment_opinion(content: str) -> str:
    """Extract investment opinion from report content."""
    for opinion, keywords in OPINION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content[:2000]:  # Check first 2000 chars
                return opinion
    return "Unknown"


def extract_target_price(content: str) -> Optional[int]:
    """Extract target price from report content."""
    # Various patterns for target price
    patterns = [
        r'목표주가[:\s]*([0-9,]+)\s*원',
        r'적정주가[:\s]*([0-9,]+)\s*원',
        r'Target Price[:\s]*([0-9,]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content[:3000])
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                continue
    
    return None


def calculate_sentiment_score(content: str) -> Dict[str, Any]:
    """
    Calculate sentiment score based on keyword frequency.
    Returns score from -1 (very negative) to +1 (very positive)
    """
    positive_count = 0
    negative_count = 0
    
    for keyword in POSITIVE_KEYWORDS:
        positive_count += content.count(keyword)
    
    for keyword in NEGATIVE_KEYWORDS:
        negative_count += content.count(keyword)
    
    total = positive_count + negative_count
    if total == 0:
        score = 0
    else:
        score = (positive_count - negative_count) / total
    
    return {
        "score": round(score, 3),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "sentiment": "Positive" if score > 0.1 else ("Negative" if score < -0.1 else "Neutral")
    }


def analyze_single_report(filepath: str) -> Dict[str, Any]:
    """Analyze a single report file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        metadata = parse_report_filename(filename)
        
        opinion = extract_investment_opinion(content)
        target_price = extract_target_price(content)
        sentiment = calculate_sentiment_score(content)
        
        # Extract first summary paragraph (title or key message)
        lines = content.split("\n")
        summary = ""
        for line in lines[:20]:
            if line.strip() and not line.startswith("!") and not line.startswith("|"):
                if len(line.strip()) > 10:
                    summary = line.strip()[:200]
                    break
        
        return {
            "filename": filename,
            "company": metadata["company"],
            "code": metadata["code"],
            "date": metadata["date"],
            "broker": metadata["broker"],
            "report_id": metadata["report_id"],
            "opinion": opinion,
            "target_price": target_price,
            "sentiment_score": sentiment["score"],
            "sentiment": sentiment["sentiment"],
            "positive_count": sentiment["positive_count"],
            "negative_count": sentiment["negative_count"],
            "summary": summary
        }
    except Exception as e:
        print(f"Error analyzing report {filepath}: {e}")
        return None


def get_company_reports(company_name: str) -> List[Dict[str, Any]]:
    """Get all reports for a specific company."""
    company_dir = os.path.join(REPORTS_DIR, company_name)
    
    if not os.path.exists(company_dir):
        return []
    
    reports = []
    for filename in os.listdir(company_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(company_dir, filename)
            analysis = analyze_single_report(filepath)
            if analysis:
                reports.append(analysis)
    
    # Sort by date (newest first)
    reports.sort(key=lambda x: x.get("date", ""), reverse=True)
    return reports


def analyze_tone_change(company_name: str) -> Dict[str, Any]:
    """
    Analyze tone changes across multiple reports for a company.
    Compare recent reports to detect sentiment shifts.
    """
    reports = get_company_reports(company_name)
    
    if len(reports) == 0:
        return {
            "company": company_name,
            "code": COMPANY_CODE_MAP.get(company_name, ""),
            "has_reports": False,
            "report_count": 0,
            "tone_change": "Unknown",
            "message": "분석 가능한 리포트가 없습니다."
        }
    
    # Calculate average sentiment
    avg_score = sum(r["sentiment_score"] for r in reports) / len(reports)
    
    # Detect tone change by comparing recent vs older reports
    if len(reports) >= 2:
        recent = reports[0]
        older = reports[-1]
        score_diff = recent["sentiment_score"] - older["sentiment_score"]
        
        if score_diff > 0.2:
            tone_change = "Improving"
            change_desc = "톤 개선 중"
        elif score_diff < -0.2:
            tone_change = "Declining"
            change_desc = "톤 악화 중"
        else:
            tone_change = "Stable"
            change_desc = "톤 유지"
    else:
        tone_change = "Unknown"
        change_desc = "비교 데이터 부족"
        score_diff = 0
    
    # Overall sentiment
    if avg_score > 0.1:
        overall = "Positive"
    elif avg_score < -0.1:
        overall = "Negative"
    else:
        overall = "Neutral"
    
    return {
        "company": company_name,
        "code": COMPANY_CODE_MAP.get(company_name, ""),
        "has_reports": True,
        "report_count": len(reports),
        "average_sentiment": round(avg_score, 3),
        "overall_sentiment": overall,
        "tone_change": tone_change,
        "change_description": change_desc,
        "score_diff": round(score_diff, 3) if len(reports) >= 2 else 0,
        "latest_report": reports[0] if reports else None,
        "reports": reports
    }


def get_all_companies() -> List[str]:
    """Get list of all companies with reports."""
    if not os.path.exists(REPORTS_DIR):
        return []
    
    return [d for d in os.listdir(REPORTS_DIR) 
            if os.path.isdir(os.path.join(REPORTS_DIR, d))]


def analyze_all_companies() -> List[Dict[str, Any]]:
    """Analyze tone changes for all companies with reports."""
    companies = get_all_companies()
    results = []
    
    for company in companies:
        analysis = analyze_tone_change(company)
        results.append(analysis)
    
    # Sort by tone change importance
    def sort_key(x):
        if x["tone_change"] == "Declining":
            return 0
        elif x["tone_change"] == "Improving":
            return 1
        else:
            return 2
    
    results.sort(key=sort_key)
    return results


if __name__ == "__main__":
    # Test the module
    print("Available companies:", get_all_companies())
    print("\n--- Analyzing all companies ---")
    results = analyze_all_companies()
    for r in results:
        print(f"\n{r['company']} ({r['code']}):")
        print(f"  Reports: {r['report_count']}")
        print(f"  Overall: {r.get('overall_sentiment', 'N/A')}")
        print(f"  Tone Change: {r['tone_change']}")
        if r.get('latest_report'):
            print(f"  Latest: {r['latest_report']['date']} - {r['latest_report']['broker']}")
