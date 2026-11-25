import time
from datetime import datetime
from data_fetcher import KiwoomREST
from indicators import add_technical_indicators
from agents import AnalystAgent, StrategistAgent, RiskManagerAgent
from execution_engine import ExecutionEngine

def run_trading_bot(target_stocks: dict):
    """
    1사이클의 자동매매 로직을 실행합니다.
    target_stocks: {"종목코드": "종목명"} 형태의 딕셔너리
    """
    print(f"\n[{datetime.now()}] === AI 트레이딩 봇 분석 사이클 시작 ===")
    
    try:
        # 1. 초기화
        fetcher = KiwoomREST()
        # fetcher.authenticate() # 실제 연동 시 주석 해제
        
        engine = ExecutionEngine(fetcher, paper_trading=True) # Paper Trading 우선
        
        analyst = AnalystAgent()
        strategist = StrategistAgent()
        risk_manager = RiskManagerAgent()
        
        for stock_code, stock_name in target_stocks.items():
            print(f"\n>>> [{stock_name}({stock_code})] 분석 중...")
            
            # Phase 1: 데이터 수집 및 지표 계산
            # 최근 30일치 데이터를 가져온다고 가정
            df = fetcher.fetch_daily_ohlcv(stock_code, start_date="2026-03-01", end_date="2026-04-30")
            df = add_technical_indicators(df)
            
            # 최근 5일치 데이터 요약 (토큰 절약을 위해)
            recent_data_str = df.tail(5).to_string()
            
            # Phase 2: 멀티 에이전트 분석
            print("  [1/3] 애널리스트 분석 중...")
            analyst_report = analyst.analyze(f"종목명 {stock_name}({stock_code})의 최근 5일 데이터 및 기술적 지표입니다.\n{recent_data_str}")
            print(f"\n--- Analyst Report ---\n{analyst_report}\n----------------------")
            
            import time
            time.sleep(3) # API 서버 과부하 방지 및 Rate Limit 회피용 대기
            
            print("  [2/3] 전략가 매매 플랜 수립 중...")
            strategist_report = strategist.analyze(
                f"애널리스트의 분석 리포트입니다:\n{analyst_report}\n\n위 분석을 바탕으로 구체적인 트레이딩 전략을 수립하세요."
            )
            print(f"\n--- Strategist Report ---\n{strategist_report}\n-------------------------")
            
            time.sleep(15) # 무료 티어 Rate Limit(분당 15회) 우회를 위한 대기
            
            print("  [3/3] 리스크 관리자 검토 (Hard Veto) 중...")
            risk_decision = risk_manager.analyze(
                f"애널리스트 리포트:\n{analyst_report}\n\n전략가 리포트:\n{strategist_report}\n\n이 거래를 승인(APPROVE)합니까, 거부(VETO)합니까?"
            )
            print(f"\n--- Risk Manager Decision ---\n{risk_decision}\n-----------------------------")
            
            # Phase 3: 실행
            if "APPROVE" in risk_decision.upper():
                engine.execute_trade(stock_code, strategist_report)
            else:
                print(f"[거부됨] 리스크 관리자가 {stock_name}({stock_code}) 거래를 VETO 했습니다.")
            
            # 리포트를 마크다운 파일로 저장
            import os
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            today_str = datetime.now().strftime("%Y%m%d")
            # 파일명을 종목명-YYYYMMDD 형태로 변경
            filename = os.path.join(output_dir, f"{stock_name}-{today_str}.md")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {stock_name}({stock_code}) AI 분석 리포트 ({today_str})\n\n")
                f.write("## 1. 시장 분석가 리포트 (Analyst)\n")
                f.write(f"{analyst_report}\n\n")
                f.write("## 2. 수석 전략가 리포트 (Strategist)\n")
                f.write(f"{strategist_report}\n\n")
                f.write("## 3. 리스크 관리자 결정 (Risk Manager)\n")
                f.write(f"{risk_decision}\n")
            
            print(f"  [Report] 분석 결과가 '{filename}' 파일로 저장되었습니다.")
                
    except Exception as e:
        print(f"시스템 오류 발생: {e}")

if __name__ == "__main__":
    print("=========================================")
    print("🤖 AI 트레이딩 봇 - 개별 종목 분석")
    print("=========================================")
    
    stock_code = input("분석할 종목코드를 입력하세요 (예: 005930): ").strip()
    stock_name = input("종목명을 입력하세요 (예: 삼성전자): ").strip()
    
    if not stock_code or not stock_name:
        print("❌ 종목코드와 종목명을 모두 입력하셔야 합니다.")
    else:
        # 입력받은 정보로 딕셔너리 생성
        target_stocks = {
            stock_code: stock_name
        }
        
        # 단일 실행
        run_trading_bot(target_stocks)
    
    # ==================================================
    # Phase 4: 24/7 Automation Loop (실제 구동 시 활성화)
    # ==================================================
    # import schedule
    # 
    # def job():
    #     run_trading_bot(target_stocks)
    #
    # # 예: 매일 오전 9시 30분에 한 번 실행
    # schedule.every().day.at("09:30").do(job)
    #
    # print("자동 매매 스케줄러를 시작합니다...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
