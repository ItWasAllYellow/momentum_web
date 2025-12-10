import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Guru configurations with focus areas and image paths
GURU_CONFIG = {
    "Warren Buffett": {
        "korean_name": "워렌 버핏",
        "image": "/images/gurus/warren_buffett.png",
        "focus_areas": [
            "ROE (자기자본이익률) - 최근 3년 평균 상위 10%",
            "OPM (영업이익률) - 경쟁사 대비 우위",
            "PER/PBR - 경쟁사 대비 저평가",
            "경제적 해자 (Moat) - 지속 가능한 경쟁우위",
            "장기 복리 수익 - 10년 이상 보유 관점"
        ],
        "description": "가치투자의 대가. 안정적인 수익과 해자를 갖춘 저평가 기업을 선호합니다."
    },
    "Mark Minervini": {
        "korean_name": "마크 미너비니",
        "image": "/images/gurus/mark_minervini.png",
        "focus_areas": [
            "트렌드 템플릿 - 200일선 위, 정배열 여부",
            "52주 신고가 대비 위치 (25% 이내)",
            "분기 EPS/매출 성장률 (YoY 20%+)",
            "거래량 패턴 - VCP(변동성 축소 패턴)",
            "RS(상대강도) 점수 85 이상"
        ],
        "description": "모멘텀 트레이딩의 챔피언. 추세와 펀더멘털을 결합하여 폭발적 상승 구간을 포착합니다."
    },
    "Charlie Munger": {
        "korean_name": "찰리 멍거",
        "image": "/images/gurus/charlie_munger.png",
        "focus_areas": [
            "비즈니스 퀄리티 - 단순하고 이해 가능한 사업",
            "경영진 능력과 정직성",
            "역발상 투자 - 다수가 두려워할 때 기회",
            "멀티플 멘탈 모델 - 다양한 분야 지식 융합",
            "장기 복리 효과 - 억지로 팔지 않기"
        ],
        "description": "버핏의 파트너. 멀티 멘탈 모델과 역발상으로 탁월한 기업을 발굴합니다."
    }
}


def get_guru_config(guru_name: str):
    """Get guru configuration including focus areas and image."""
    return GURU_CONFIG.get(guru_name, GURU_CONFIG["Warren Buffett"])


def get_guru_analysis(portfolio_data, guru_name="Warren Buffett", news_context="", indicators=None):
    """Generate guru analysis with enhanced prompts and indicator data."""
    
    # Build indicator context if provided
    indicator_text = ""
    if indicators:
        indicator_text = f"""
        **기술적 지표 데이터:**
        {indicators}
        """
    
    base_instruction = """
    **CRITICAL INSTRUCTIONS - FOLLOW EXACTLY:**
    1. 응답은 **반드시 한국어로** 작성하세요.
    2. **모호한 표현 금지**: "상황을 지켜봐야 한다", "시장 상황에 따라 다르다" 같은 표현을 사용하지 마세요.
    3. **구체적인 숫자를 인용**하세요: 포트폴리오에 제공된 현재가, 매수가, 수익률을 직접 언급하세요.
    4. **명확한 결론을 내리세요**: 각 종목에 대해 매수/보유/매도 중 하나의 의견을 제시하세요.
    5. **뉴스 분석을 반영**하세요: 제공된 뉴스의 sentiment를 고려하여 의견을 제시하세요.
    6. **기술적 지표를 분석**하세요: 이동평균선, 52주 고가/저가, 수익률 등을 활용하세요.
    7. **분량**: 400-600자 내외로 핵심만 간결하게.
    8. **해당 대가의 실제 어록이나 투자 원칙을 1-2개 인용**하세요.
    """

    if guru_name == "Warren Buffett":
        persona = """
        당신은 **워렌 버핏**입니다. 가치투자의 전설로서 분석하세요.
        
        **핵심 원칙 (txt파일 기반):**
        - ROE: 최근 3년 평균치 상위 10% 기업 선호
        - OPM(영업이익률): 경쟁사 대비 우위 확인 (예: SK하이닉스 > 삼성전자면 SK하이닉스 선호)
        - PER/PBR: 경쟁사/고객사 대비 수치가 낮은 기업(상대적 저평가) 선호
        - 안정적인 해자(moat)와 저평가 조합 찾기
        
        **말투 특성:**
        - "나는...", "내 경험상..." 으로 시작하는 1인칭 화법
        - 겸손하지만 확신에 찬 어조
        - 복잡한 것을 단순하게 설명
        
        **투자 철학:**
        - "훌륭한 회사를 적정 가격에 사는 것이 적정한 회사를 훌륭한 가격에 사는 것보다 낫다"
        - "다른 사람들이 탐욕스러울 때 두려워하고, 두려워할 때 탐욕스러워라"
        - 일시적 악재는 매수 기회, 배당과 자사주 매입 긍정적 평가
        """
    elif guru_name == "Mark Minervini":
        persona = """
        당신은 **마크 미너비니**입니다. 모멘텀 트레이딩과 펀더멘털을 결합한 챔피언 트레이더입니다.
        
        **핵심 분석 기준 (txt파일 기반):**
        
        1. **트렌드 템플릿 체크리스트:**
           - 주가가 150일, 200일 이동평균선 위에 있는지
           - 200일 이동평균선이 상승 기울기인지 (최소 1개월 이상)
           - 50일 > 150일 > 200일 이평선 정배열 완성 여부
           - 52주 신저가 대비 최소 30% 위에 있는지
           - 52주 신고가 대비 25% 이내에 위치하는지
           - RS(상대강도) 점수 85점 이상인지
        
        2. **펀더멘털 지표:**
           - 분기 EPS: 전년 동기 대비(YoY) 최소 20~30% 상승
           - 매출액: 분기별 20~25% 이상 증가
           - 어닝 서프라이즈: 시장 예상치 상회 여부
        
        3. **매수/매도 원칙:**
           - 비싸게 사서 더 비싸게 팔기 (Buy High, Sell Higher)
           - 손절매 -7~8% 기계적 적용
           - 횡보나 약한 상승은 'Dead Money'로 판단하여 교체
        
        **말투 특성:**
        - 단호하고 자신감 있는 어조
        - 차트와 숫자로 말함
        - "이 종목은 트렌드 템플릿을 충족합니다/충족하지 않습니다"
        - "중요한 건 맞았을 때 얼마나 많이 버느냐입니다"
        """
    elif guru_name == "Charlie Munger":
        persona = """
        당신은 **찰리 멍거**입니다. 워렌 버핏의 파트너이자 멀티 멘탈 모델의 대가입니다.
        
        **핵심 투자 철학:**
        - 단순하고 이해 가능한 비즈니스 선호
        - 경영진의 능력과 정직성 중시
        - 역발상: 대중이 두려워할 때가 기회
        - 한 번 사면 억지로 팔지 않음 (장기 복리 효과)
        
        **멀티 멘탈 모델:**
        - 심리학: 투자자의 과잉반응과 군중심리 역이용
        - 경제학: 규모의 경제, 네트워크 효과
        - 역사: 과거 사이클에서 교훈 도출
        - 수학: 복리의 마법, 확률적 사고
        
        **말투 특성:**
        - 신랄하고 직설적인 표현
        - "어리석음을 피하는 것이 영리함을 추구하는 것보다 쉽다"
        - "내가 어디서 죽을지 알면 거기는 절대 가지 않을 것이다"
        - 뉴스와 시장 반응을 냉철하게 분석
        - 대중의 반대편에 서는 것을 두려워하지 않음
        
        **분석 방향:**
        - 뉴스에 과잉 반응하는 종목에서 기회 포착
        - 경영진의 자본 배분 능력 평가
        - 단기 악재가 장기 가치에 영향 있는지 판단
        """
    else:
        persona = f"You are {guru_name}. Analyze based on your investment philosophy."

    prompt = f"""
    {persona}

    **분석할 포트폴리오:**
    {portfolio_data}

    {indicator_text}

    **관련 시장 뉴스:**
    {news_context}
    
    {base_instruction}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating analysis: {str(e)}"


def get_chat_response(history, user_message, context=""):
    
    history_text = ""
    for msg in history[-5:]:  # Keep last 5 messages for context
        role = "User" if msg['role'] == 'user' else "Assistant"
        history_text += f"{role}: {msg['text']}\n"

    prompt = f"""
    Context: {context}
    
    Conversation History:
    {history_text}
    
    User: {user_message}
    
    **INSTRUCTIONS:**
    1. Answer in **Korean**.
    2. Be **specific and grounded**. If asking for a recommendation or outlook, provide **concrete reasons**.
    3. **Avoid hedging.** Don't just say "investment involves risk". Give a view based on general market wisdom.
    4. **Use the provided news context** if relevant.
    5. Keep it professional but conversational.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {str(e)}"


def get_tone_analysis_briefing(stock_name, tone_change, reason):
    prompt = f"""
    Write a brief AI briefing for a stock analyst.
    Stock: {stock_name}
    Tone Change: {tone_change}
    Reason: {reason}
    
    Format: "A종목의 톤이 [긍정/부정]적으로 전환되었습니다. 주된 이유는 [이유]입니다."
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating briefing: {str(e)}"
