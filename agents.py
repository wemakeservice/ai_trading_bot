import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class GeminiAgent:
    """
    Gemini API를 이용한 기본 에이전트 클래스입니다.
    시스템 프롬프트를 다르게 주어 여러 역할을 수행할 수 있도록 합니다.
    """
    def __init__(self, role: str, system_prompt: str, model_name="gemini-2.5-flash"):
        self.role = role
        self.system_prompt = system_prompt
        self.model_name = model_name
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "여기에" in api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았거나 임시 텍스트가 남아있습니다. .env 파일을 저장했는지 확인하세요.")
        
        # .env 파일에 공백이 들어갔을 경우를 대비해 양옆 공백 제거
        api_key = api_key.strip()
        
        self.client = genai.Client(api_key=api_key)

    def analyze(self, user_prompt: str) -> str:
        """에이전트에게 분석 요청을 보내고 응답을 반환합니다."""
        print(f"[{self.role}] 분석 시작...")
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                ),
            )
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

# ==========================================
# 1. Analyst Agent (시장 분석가)
# ==========================================
ANALYST_PROMPT = """
당신은 월스트리트 최고 수준의 '시장 분석가(Market Analyst)'입니다.
주어진 주식의 일봉 데이터(OHLCV) 및 기술적 지표(이동평균선, RSI, MACD, 볼린저밴드 등)를 바탕으로 현재 시장 상황을 객관적으로 분석하세요.
상승장인지, 하락장인지, 횡보장인지 파악하고 주요 지지선과 저항선을 찾아내야 합니다.

결과는 다음 형식으로 작성하세요:
- 현재 트렌드 요약:
- 주요 지표 분석 (RSI, MACD 등):
- 지지선/저항선 예측:
- 종합 의견 (Bullish/Bearish/Neutral):
"""

class AnalystAgent(GeminiAgent):
    def __init__(self):
        super().__init__(role="Analyst", system_prompt=ANALYST_PROMPT)


# ==========================================
# 2. Strategist Agent (전략가)
# ==========================================
STRATEGIST_PROMPT = """
당신은 헤지펀드의 '수석 트레이딩 전략가(Trading Strategist)'입니다.
'시장 분석가'가 작성한 리포트와 현재가를 바탕으로 구체적인 트레이딩 전략을 수립하세요.

결과는 다음 형식으로 작성하세요:
- 추천 포지션 (BUY, SELL, HOLD):
- 진입가 (Entry Price):
- 목표가 (Take Profit):
- 손절가 (Stop Loss):
- 포지션 비중 (예: 전체 자본의 10%):
- 전략 논리: (왜 이런 전략을 세웠는지 1~2줄로 설명)
"""

class StrategistAgent(GeminiAgent):
    def __init__(self):
        super().__init__(role="Strategist", system_prompt=STRATEGIST_PROMPT)


# ==========================================
# 3. Risk Manager Agent (리스크 관리자 - Hard Veto)
# ==========================================
RISK_MANAGER_PROMPT = """
당신은 헤지펀드의 엄격한 '리스크 관리 책임자(Chief Risk Officer)'입니다.
'시장 분석가'의 리포트와 '전략가'의 트레이딩 계획을 꼼꼼히 검토하십시오.
당신의 유일한 목표는 자본을 보호하는 것입니다. 손익비(Risk/Reward Ratio)가 나쁘거나 하락장인데 억지로 매수를 추천했다면 무조건 거래를 거부(Veto)해야 합니다.

결과는 반드시 다음 형식으로 작성하세요:
[최종결정] : APPROVE 또는 VETO (단어 하나만 명확히 기재할 것)
[거부 사유 또는 승인 사유] : (1~3줄로 작성)
"""

class RiskManagerAgent(GeminiAgent):
    def __init__(self):
        super().__init__(role="Risk Manager", system_prompt=RISK_MANAGER_PROMPT)


if __name__ == "__main__":
    # 테스트 (API 키가 없으면 에러가 발생하므로 구조만 확인)
    pass
