# AI Trading Bot (한국 증시 주도주 자동 스캐너 & AI 분석 봇)

이 프로젝트는 한국 증시(KRX)의 당일 시장 주도주를 자동으로 스캔하고, 다중 AI 에이전트(애널리스트, 전략가, 리스크 관리자)를 활용하여 투자 전략을 도출하는 자동화 스크립트 모음입니다.

## 🚀 주요 기능

- **일일 시장 스캐너 (`daily_scanner.py`)**
  - 장 마감 후 당일 거래대금 및 거래량 상위 주도주(Top 25) 자동 추출
  - 추출된 종목들의 현재가, 등락률, 업종(Industry) 정보 결합
  - 결과를 마크다운(`.md`) 파일로 자동 저장
  - 설정된 수신자(단일/다중)에게 스타일이 적용된 HTML 형식의 요약 이메일 자동 발송
  
- **다중 AI 기반 심층 분석 (`main.py` / `agents.py`)**
  - **애널리스트:** 최근 가격 변동 및 기술적 지표를 기반으로 한 기본 분석
  - **전략가:** 애널리스트의 분석을 바탕으로 구체적인 매수/매도/관망 트레이딩 전략 수립
  - **리스크 관리자:** 최종 전략에 대한 포트폴리오 비중, 손절가, 변동성 등의 위험 요소 검증

## 🛠️ 설치 및 설정 방법

### 1. 가상 환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
```

### 2. 패키지 설치
아래의 라이브러리들이 필요합니다.
```bash
pip install finance-datareader pykrx google-genai python-dotenv
```

### 3. 환경 변수 (`.env`) 설정
프로젝트 최상단 루트에 `.env` 파일을 생성하고 아래 내용을 입력해 주세요. (GitHub에 절대 노출되지 않도록 주의하세요!)

```env
# Google Gemini API 인증 정보
GEMINI_API_KEY=your_gemini_api_key_here

# 자동 이메일 발송 설정 (Gmail 권장)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # 일반 비밀번호가 아닌 '앱 비밀번호(App Password)' 사용
EMAIL_RECEIVER=receiver1@email.com, receiver2@email.com
```

## 🖥️ 사용 방법

### 시장 주도주 스캔 및 이메일 리포팅
당일 장 마감 후 시장 주도주를 스캔하고 리포트를 생성/발송합니다.
```bash
python daily_scanner.py
```
> 결과물은 `output/` 폴더에 `거래대금 25-거래량 25-YYYYMMDD.md` 형태로 저장됩니다.

## ⚠️ 주의 사항

- 본 프로그램에서 제공되는 AI의 종목 분석과 매매 전략은 정보 제공을 목적으로 하며, 실제 투자 결과에 대한 책임은 전적으로 투자자 본인에게 있습니다.
- `.env` 파일이 실수로 GitHub에 업로드되지 않도록 주의해 주세요. (이미 `.gitignore`에 포함되어 있습니다.)
