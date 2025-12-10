# 📈 Project Momentum

> AI 기반 주식 분석 및 포트폴리오 관리 플랫폼

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)
![React](https://img.shields.io/badge/React-19-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-teal.svg)

</div>

---

## 📋 목차

- [Pain Points & 해결책](#-pain-points--해결책)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [빠른 시작 가이드](#-빠른-시작-가이드)
- [프로젝트 구조](#-프로젝트-구조)
- [예시 화면](#-예시-화면)
- [API 키 발급 가이드](#-api-키-발급-가이드)
- [문제 해결](#-문제-해결)

---

## 🎯 Pain Points & 해결책

### 기존 투자자들의 어려움

| Pain Point | Momentum의 해결책 |
|------------|------------------|
| 📰 **뉴스 과부하**: 수많은 뉴스 중 의미 있는 정보 선별이 어려움 | AI 기반 감성 분석으로 뉴스의 긍정/부정 영향도를 자동 분석 |
| 📊 **리포트 해석 난이도**: 증권사 리포트의 전문 용어와 숫자 해석이 어려움 | Tone Change Analysis로 애널리스트의 숨겨진 심리 변화 감지 |
| 🎓 **전문가 조언 부재**: 개인 투자자가 전문가 수준의 분석을 받기 어려움 | 워렌 버핏, 피터 린치 등 금융 대가의 AI 페르소나가 포트폴리오 진단 |
| 🔗 **종목 간 연관성 파악 어려움**: 보유 종목들이 어떻게 연동되는지 모름 | 상관관계 그래프로 포트폴리오 다각화 수준 시각화 |
| ⏰ **정보 수집 시간 부족**: 직장인 투자자가 시장을 따라가기 어려움 | 한 곳에서 종합적인 분석 결과 제공 |

---

## ✨ 주요 기능

### 🟢 Easy Mode (일반 투자자용)

- **내 포트폴리오 대시보드**: 보유 종목의 수익률, 현재가 확인 및 관리
- **AI 금융 대가 분석 (Guru Analysis)**: 워렌 버핏, 피터 린치 등 유명 투자자의 관점에서 포트폴리오 진단
- **종목 상관관계 그래프**: 보유 종목 간 가격 움직임 상관관계 시각화

### 🔵 Expert Mode (전문가용)

- **전체 종목 시세**: 350여 개 KOSPI/KOSDAQ 종목 실시간 정보 조회
- **뉴스 키워드 검색**: 종목별 맞춤 키워드로 뉴스 필터링
- **Analyst Tone Change**: 애널리스트 리포트의 어조 변화 감지 (긍정↔부정)
- **감성 분석 그래프**: 뉴스 기사별 긍정/부정 점수 시각화

### 💬 공통 기능

- **AI ChatBot**: 시장, 금융 용어, 종목 정보에 대한 자유로운 질의응답
- **직관적인 다크 테마 UI**: 깔끔하고 모던한 인터페이스

---

## 🛠 기술 스택

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 19.2 | UI 프레임워크 |
| Vite | 7.2 | 빌드 도구 |
| React Router | 7.9 | 라우팅 |
| Recharts | 3.4 | 차트/시각화 |
| Axios | 1.13 | HTTP 클라이언트 |

### Backend
| 기술 | 용도 |
|------|------|
| FastAPI | REST API 서버 |
| Uvicorn | ASGI 서버 |
| Google Generative AI | Gemini LLM 연동 |
| Pandas / NumPy | 데이터 분석 |
| Scikit-learn | 상관관계 분석 |

---

## 🚀 빠른 시작 가이드

### 📌 사전 요구사항

- **Node.js** v16 이상
- **Python** 3.8 이상
- **Git**

### 📥 Step 1: 프로젝트 클론

```bash
git clone https://github.com/ItWasAllYellow/momentum_web.git
cd momentum_web
```

### 🔑 Step 2: 환경 변수 설정 (중요!)

**루트 디렉토리**에 `.env` 파일 생성:
```bash
# 프로젝트 루트에서 실행
cp .env.example .env
```

**server 디렉토리**에도 `.env` 파일 생성:
```bash
cp server/.env.example server/.env
```

그리고 두 `.env` 파일에 실제 API 키를 입력하세요:

```env
LS_APP_KEY=your_ls_app_key_here
LS_SECRET_KEY=your_ls_secret_key_here
LS_BASE_URL=https://openapi.ls-sec.co.kr:8080
GEMINI_API_KEY=your_gemini_api_key_here
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```

> ⚠️ **주의**: `.env` 파일은 Git에 포함되지 않습니다. 팀원에게 별도로 전달받으세요.

### 📦 Step 3: Backend 설정

```bash
# 프로젝트 루트에서 실행

# Python 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r server/requirements.txt
```

### 📦 Step 4: Frontend 설정

```bash
cd client
npm install
```

### ▶️ Step 5: 서버 실행

**터미널 1 - Backend 서버:**
```bash
cd server
python main.py
```
> 성공 시: `Uvicorn running on http://0.0.0.0:8000`

**터미널 2 - Frontend 서버:**
```bash
cd client
npm run dev
```
> 성공 시: `Local: http://localhost:5173/`

### 🌐 Step 6: 접속

브라우저에서 `http://localhost:5173` 접속

**테스트 계정:**
| ID | PW |
|----|----|
| `20201651` | `20201651` |

> 💡 회원가입도 가능하지만, 서버 재시작 시 데이터가 초기화됩니다.

---

## 📁 프로젝트 구조

```
momentum_web/
├── 📂 client/                  # Frontend (React)
│   ├── 📂 src/
│   │   ├── 📂 components/      # 재사용 컴포넌트
│   │   ├── 📂 pages/           # 페이지 컴포넌트
│   │   │   ├── Landing.jsx     # 로그인/회원가입
│   │   │   ├── ModeSelection.jsx # 모드 선택
│   │   │   ├── EasyMode.jsx    # Easy Mode
│   │   │   └── ExpertMode.jsx  # Expert Mode
│   │   ├── App.jsx             # 메인 앱
│   │   └── index.css           # 글로벌 스타일
│   └── package.json
│
├── 📂 server/                  # Backend (FastAPI)
│   ├── 📂 data/                # 주가 데이터 (CSV)
│   ├── 📂 crawler/             # 뉴스 크롤러
│   ├── main.py                 # FastAPI 엔트리
│   ├── ai_service.py           # Gemini AI 서비스
│   ├── data_service.py         # 데이터 처리
│   ├── report_service.py       # 리포트 분석
│   ├── etl.py                  # 감성 분석 ETL
│   ├── requirements.txt        # Python 의존성
│   └── .env.example            # 환경변수 템플릿
│
├── 📂 to_be_used/              # 분석용 데이터
│   └── 📂 report/              # 증권사 리포트
│
├── .env.example                # 환경변수 템플릿
├── .gitignore                  # Git 제외 파일
└── README.md                   # 이 파일
```

---

## 📸 예시 화면

### 🔐 로그인 화면
모던하고 깔끔한 다크 테마 로그인 인터페이스

### 🏠 모드 선택
Easy Mode / Expert Mode 선택 화면

### 📊 Easy Mode - 포트폴리오 대시보드
- 보유 종목 수익률 현황
- AI Guru 분석 (워렌 버핏, 피터 린치 등)
- 종목 간 상관관계 그래프

### 🔬 Expert Mode - 전문가 분석
- 전체 종목 시세 테이블
- 뉴스 키워드 검색
- Tone Change 분석 그래프
- 감성 분석 바 차트

---

## 🔐 API 키 발급 가이드

### 1. Google Gemini API Key

1. [Google AI Studio](https://aistudio.google.com/) 접속
2. 로그인 후 "Get API Key" 클릭
3. "Create API Key" 선택
4. 생성된 키를 `.env`의 `GEMINI_API_KEY`에 입력

### 2. LS증권 API Key (주가 데이터)

1. [LS증권 Open API](https://openapi.ls-sec.co.kr/) 접속
2. 회원가입 후 앱 등록
3. APP KEY, SECRET KEY 발급
4. `.env`에 입력

### 3. Naver API Key (뉴스 검색)

1. [Naver Developers](https://developers.naver.com/) 접속
2. 애플리케이션 등록 (검색 API 선택)
3. Client ID, Secret 발급
4. `.env`에 입력

---

## ❓ 문제 해결

### 🔴 "GEMINI_API_KEY not found" 에러

```bash
# .env 파일이 올바른 위치에 있는지 확인
ls -la .env           # 루트
ls -la server/.env    # server 폴더
```

### 🔴 "Module not found" 에러 (Python)

```bash
# 가상환경 활성화 확인 후 재설치
pip install -r server/requirements.txt
```

### 🔴 "npm install" 실패

```bash
# Node.js 버전 확인
node -v  # v16 이상이어야 함

# 캐시 삭제 후 재시도
npm cache clean --force
npm install
```

### 🔴 포트 충돌

```bash
# 다른 포트로 실행
# Backend:
uvicorn main:app --port 8001

# Frontend (vite.config.js 수정):
server: { port: 3000 }
```

---

## 👥 팀 정보

**AI Capstone Design Project**

---

## 📄 라이선스

MIT License

---

<div align="center">

**Made with ❤️ for better investment decisions**

</div>
