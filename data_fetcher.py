import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class KiwoomREST:
    """
    키움증권 REST API 연동을 위한 기본 래퍼(Wrapper) 클래스입니다.
    Mac에서도 실행 가능한 순수 HTTP 요청 기반입니다.
    """
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key or os.getenv("KIWOOM_API_KEY")
        self.api_secret = api_secret or os.getenv("KIWOOM_API_SECRET")
        
        # 키움증권 REST API 기본 URL (실제 문서에 따라 변경될 수 있음)
        self.base_url = "https://openapi.kiwoom.com/v1" 
        self.access_token = None
        
        # self.authenticate() # 토큰 발급 로직 활성화 시 주석 해제

    def authenticate(self):
        """
        인증 토큰(OAuth)을 발급받는 메서드입니다.
        """
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.api_key,
            "appsecret": self.api_secret
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            print("키움증권 API 인증 성공")
        else:
            print(f"인증 실패: {response.status_code} - {response.text}")

    def get_headers(self):
        """API 요청에 필요한 공통 헤더를 반환합니다."""
        if not self.access_token:
            return {"appkey": self.api_key, "appsecret": self.api_secret}
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
            "content-type": "application/json"
        }

    def fetch_daily_ohlcv(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        종목의 일봉(OHLCV) 데이터를 가져옵니다.
        (현재 테스트를 위해 yfinance를 사용하여 실제 시장 데이터를 가져옵니다.)
        추후 키움증권 REST API 연동이 완료되면 해당 코드로 교체하세요.
        """
        import yfinance as yf
        
        # 한국 주식은 종목코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여야 yfinance에서 조회 가능
        # 예시로 코스피(.KS)를 기본으로 붙임
        yf_ticker = f"{stock_code}.KS"
        print(f"[{stock_code}] {start_date} ~ {end_date} 실제 시장 데이터 수집 중... (yfinance)")
        
        df = yf.download(yf_ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            print("데이터를 불러오지 못했습니다. 종목코드나 날짜를 확인하세요.")
            return pd.DataFrame()
            
        # 컬럼 이름 소문자로 통일
        df.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in df.columns]
        
        return df

    def get_current_price(self, stock_code: str) -> dict:
        """
        특정 종목의 현재가를 조회합니다.
        (현재 테스트를 위해 yfinance를 사용합니다.)
        """
        import yfinance as yf
        yf_ticker = f"{stock_code}.KS"
        ticker = yf.Ticker(yf_ticker)
        
        try:
            # 가장 최근의 종가 가져오기
            history = ticker.history(period="1d")
            if not history.empty:
                current_price = history['Close'].iloc[-1]
            else:
                current_price = 0
        except Exception:
            current_price = 0
            
        return {
            "stock_code": stock_code,
            "price": float(current_price),
            "change_rate": 0.0 # 임시
        }

if __name__ == "__main__":
    # 테스트 실행
    fetcher = KiwoomREST(api_key="MOCK_KEY", api_secret="MOCK_SECRET")
    df = fetcher.fetch_daily_ohlcv("005930", "2026-04-01", "2026-04-30")
    print(df.head())
