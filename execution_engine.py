import json
from data_fetcher import KiwoomREST

class ExecutionEngine:
    """
    Risk Manager의 승인(APPROVE)이 떨어진 트레이딩 전략을 
    실제 증권사 API를 통해 실행하거나 모의투자(Paper Trading)로 기록하는 모듈.
    """
    def __init__(self, kiwoom_api: KiwoomREST, paper_trading: bool = True):
        self.api = kiwoom_api
        self.paper_trading = paper_trading
        
    def execute_trade(self, stock_code: str, strategy_report: str):
        """
        Risk Manager가 승인한 전략(strategy_report)을 파싱하여 
        매수/매도 주문을 실행합니다.
        """
        # 아주 단순화된 텍스트 파싱 예시 (실제로는 LLM에 JSON 출력을 강제하는 것이 좋습니다)
        position = "HOLD"
        if "BUY" in strategy_report:
            position = "BUY"
        elif "SELL" in strategy_report:
            position = "SELL"
            
        current_price_info = self.api.get_current_price(stock_code)
        price = current_price_info.get("price")
        
        if position == "HOLD":
            print(f"[Execution] {stock_code} 보류(HOLD). 주문을 넣지 않습니다.")
            return

        if self.paper_trading:
            # 모의투자 로그
            print(f"\n[Paper Trading] 📈 가상 주문 실행!")
            print(f"- 종목코드: {stock_code}")
            print(f"- 포지션: {position}")
            print(f"- 체결가(현재가 기준): {price}원")
            print("- 상태: 성공 (가상)")
        else:
            # 실제 주문 로직 (키움 REST API 매수/매도 엔드포인트 호출)
            # url = f"{self.api.base_url}/domestic-stock/v1/trading/order-cash"
            print(f"[Live Trading] ⚠️ 실제 주문 전송: {stock_code} {position}")
            pass

if __name__ == "__main__":
    fetcher = KiwoomREST(api_key="MOCK", api_secret="MOCK")
    engine = ExecutionEngine(fetcher, paper_trading=True)
    engine.execute_trade("005930", "추천 포지션: BUY\n진입가: 50500\n")
