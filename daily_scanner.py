import FinanceDataReader as fdr
import datetime
import sqlite3
import os
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def get_top_stocks(max_retries=5, retry_delay=60):
    """
    당일 거래대금 상위 25개, 거래량 상위 25개 종목을 추출하여 반환합니다.
    데이터가 아직 반영되지 않아 비어 있을 경우 일정 간격으로 재시도합니다.
    """
    df = None
    for attempt in range(1, max_retries + 1):
        print(f"[{datetime.datetime.now()}] 한국거래소(KRX) 전체 종목 데이터 수집 중... (시도 {attempt}/{max_retries})")
        try:
            raw_df = fdr.StockListing('KRX')
            # 결측치나 거래정지 등 에러 방지를 위해 Amount, Volume이 있는 데이터 필터링
            filtered_df = raw_df.dropna(subset=['Amount', 'Volume'])
            
            if not filtered_df.empty:
                df = filtered_df
                break
            else:
                print(f"⚠️ 유효한 거래 데이터(Amount, Volume)가 0건입니다. (KRX 캐시 서버 업데이트 대기 중)")
        except Exception as e:
            print(f"⚠️ 데이터 수집 중 오류 발생: {e}")
            
        if attempt < max_retries:
            print(f"⏳ {retry_delay}초 후 다시 시도합니다...")
            time.sleep(retry_delay)
            
    if df is None or df.empty:
        print("❌ 최대 재시도 횟수를 초과했으나 유효한 KRX 데이터를 수집하지 못했습니다.")
        return {}, {}
    
    print("거래대금 상위 25개 추출 중...")
    top_value = df.sort_values('Amount', ascending=False).head(25)
    
    print("거래량 상위 25개 추출 중...")
    top_volume = df.sort_values('Volume', ascending=False).head(25)
    
    top_value_stocks = {}
    top_volume_stocks = {}
    
    # 거래대금 상위 25개 추가
    for _, row in top_value.iterrows():
        top_value_stocks[row['Code']] = {
            'name': row['Name'],
            'amount': row['Amount'],
            'volume': row['Volume'],
            'close': row['Close'],
            'change_ratio': row['ChagesRatio']
        }
        
    # 거래량 상위 25개 추가
    for _, row in top_volume.iterrows():
        top_volume_stocks[row['Code']] = {
            'name': row['Name'],
            'amount': row['Amount'],
            'volume': row['Volume'],
            'close': row['Close'],
            'change_ratio': row['ChagesRatio']
        }
        
    print(f"총 추출된 종목 수: 거래대금 {len(top_value_stocks)}개, 거래량 {len(top_volume_stocks)}개")
    return top_value_stocks, top_volume_stocks

def save_to_sqlite(top_value_stocks, top_volume_stocks, output_dir):
    """
    추출된 종목 딕셔너리를 SQLite 데이터베이스에 누적 저장합니다.
    """
    db_path = os.path.join(output_dir, "trading_data.db")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # DB 연결 및 테이블 생성
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_top_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT,
            scan_type TEXT,
            rank INTEGER,
            code TEXT,
            name TEXT,
            amount INTEGER,
            volume INTEGER,
            close_price INTEGER,
            change_ratio REAL
        )
    """)
    
    # 삽입 쿼리 준비
    insert_query = """
        INSERT INTO daily_top_stocks 
        (scan_date, scan_type, rank, code, name, amount, volume, close_price, change_ratio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # 거래대금 상위 종목 저장 (scan_type='AMOUNT')
    for rank, (code, info) in enumerate(top_value_stocks.items(), start=1):
        close_price = int(info['close']) if str(info['close']).lower() != 'nan' else 0
        change_ratio = float(info['change_ratio']) if str(info['change_ratio']).lower() != 'nan' else 0.0
        
        cursor.execute(insert_query, (
            date_str, 'AMOUNT', rank, code, info['name'], 
            int(info['amount']), int(info['volume']), close_price, change_ratio
        ))

    # 거래량 상위 종목 저장 (scan_type='VOLUME')
    for rank, (code, info) in enumerate(top_volume_stocks.items(), start=1):
        close_price = int(info['close']) if str(info['close']).lower() != 'nan' else 0
        change_ratio = float(info['change_ratio']) if str(info['change_ratio']).lower() != 'nan' else 0.0
        
        cursor.execute(insert_query, (
            date_str, 'VOLUME', rank, code, info['name'], 
            int(info['amount']), int(info['volume']), close_price, change_ratio
        ))
        
    conn.commit()
    conn.close()
    
    print(f"\n💾 [DB 저장 완료] 총 {len(top_value_stocks) + len(top_volume_stocks)}개 종목이 데이터베이스('{db_path}')에 저장되었습니다.")

def send_email_report(top_value_stocks, top_volume_stocks):
    """
    추출된 종목 딕셔너리를 받아서 HTML 테이블 형태로 지정된 이메일로 발송합니다.
    """
    load_dotenv()
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    
    if not sender_email or not sender_password or not receiver_email:
        print("\n💡 [이메일 발송 안내] .env 파일에 이메일 정보(SENDER/PASSWORD/RECEIVER)가 설정되지 않아 메일 발송은 건너뜁니다.")
        return
        
    # 날짜 포맷 (YYYY-MM-DD)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    # 쉼표(,)로 구분된 여러 이메일 주소를 리스트로 변환
    receiver_list = [email.strip() for email in receiver_email.split(",") if email.strip()]
    
    # 터미널 출력용 문자열
    receivers_str = ", ".join(receiver_list)
    print(f"\n📧 '{receivers_str}' 주소로 이메일을 발송하는 중입니다...")
    try:
        # HTML 테이블 생성 헬퍼 함수
        def generate_table(stocks_dict):
            table_html = """
            <table>
                <tr>
                    <th width="8%">순위</th>
                    <th width="20%">종목명</th>
                    <th width="12%">종목코드</th>
                    <th width="15%">거래대금(억원)</th>
                    <th width="15%">거래량(만주)</th>
                    <th width="15%">현재가(원)</th>
                    <th width="15%">등락률(%)</th>
                </tr>
            """
            for idx, (code, info) in enumerate(stocks_dict.items(), start=1):
                name = info['name']
                amount_uk = info['amount'] // 100_000_000
                volume_man = info['volume'] // 10_000
                close_price = int(info['close']) if not str(info['close']).lower() == 'nan' else 0
                change_ratio = float(info['change_ratio']) if not str(info['change_ratio']).lower() == 'nan' else 0.0
                
                color = "red" if change_ratio > 0 else "blue" if change_ratio < 0 else "black"
                
                table_html += f"""
                    <tr>
                        <td class="center">{idx}</td>
                        <td class="left">{name}</td>
                        <td class="center">{code}</td>
                        <td>{amount_uk:,}</td>
                        <td>{volume_man:,}</td>
                        <td>{close_price:,}</td>
                        <td style="color: {color};">{change_ratio:+.2f}%</td>
                    </tr>
                """
            table_html += "</table>"
            return table_html

        html_content = f"""
        <html>
        <head>
            <style>
                table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; }}
                th, td {{ border: 1px solid #dddddd; text-align: right; padding: 8px; }}
                th {{ background-color: #f2f2f2; text-align: center; }}
                .center {{ text-align: center; }}
                .left {{ text-align: left; }}
            </style>
        </head>
        <body>
            <h2>📊 오늘의 시장 주도주 스캔 결과 ({date_str})</h2>
            
            <h3>💰 거래대금 상위 25종목</h3>
            {generate_table(top_value_stocks)}
            
            <br/>
            <h3>📈 거래량 상위 25종목</h3>
            {generate_table(top_volume_stocks)}
        </body>
        </html>
        """
            
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receivers_str # 헤더에는 쉼표로 구분된 문자열 사용
        msg['Subject'] = f"[AI 트레이딩 봇] 오늘의 시장 주도주 스캔 결과 {date_str}"
        
        # 본문을 HTML 포맷으로 첨부
        msg.attach(MIMEText(html_content, 'html'))
        
        # 기본적으로 Gmail SMTP 서버를 사용
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        # to_addrs에 리스트를 직접 전달하여 다중 발송 처리
        server.send_message(msg, to_addrs=receiver_list)
        server.quit()
        
        print("✅ 이메일 발송이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("🤖 AI 트레이딩 봇 - [일일 스캐너] 장 마감 후 자동 분석")
    print("==================================================")
    
    top_value_stocks, top_volume_stocks = get_top_stocks()
    
    if not top_value_stocks and not top_volume_stocks:
        print("\n❌ 수집된 종목 데이터가 없어 파일 및 DB 저장, 이메일 발송을 중단합니다.")
        sys.exit(1)
    
    print("\n[임시 중지됨] 일괄 AI 분석 실행은 현재 주석 처리되어 실행되지 않습니다.")
    
    # AI 봇 실행 시에는 중복을 제거한 전체 목록 전달
    # unified_stocks = {**top_value_stocks, **top_volume_stocks}
    # run_trading_bot(unified_stocks)
    
    print("\n✅ 오늘의 상위 종목 스캔이 완료되었습니다! (AI 분석은 건너뜀)")
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = os.path.join(output_dir, f"거래대금 25-거래량 25-{today_str}.md")
    
    def write_and_print_table(f, title, stocks_dict):
        f.write(f"## {title}\n")
        f.write("| 순위 | 종목명 | 종목코드 | 거래대금(억원) | 거래량(만주) | 현재가(원) | 등락률(%) |\n")
        f.write("| :---: | :--- | :---: | ---: | ---: | ---: | ---: |\n")
        
        print(f"\n[{title}]")
        for idx, (code, info) in enumerate(stocks_dict.items(), start=1):
            name = info['name']
            amount_uk = info['amount'] // 100_000_000
            volume_man = info['volume'] // 10_000
            close_price = int(info['close']) if not str(info['close']).lower() == 'nan' else 0
            change_ratio = float(info['change_ratio']) if not str(info['change_ratio']).lower() == 'nan' else 0.0
            
            f.write(f"| {idx} | {name} | {code} | {amount_uk:,} | {volume_man:,} | {close_price:,} | {change_ratio:+.2f}% |\n")
            
            line = f" {idx:2d}. {name:<10} ({code}) | 거래대금: {amount_uk:>6,}억원 | 거래량: {volume_man:>7,}만주 | 현재가: {close_price:>7,}원 | 등락률: {change_ratio:>6.2f}%"
            print(line)
        f.write("\n")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 오늘의 시장 주도주 스캔 결과 - {today_str}\n\n")
        write_and_print_table(f, "💰 거래대금 상위 25종목", top_value_stocks)
        write_and_print_table(f, "📈 거래량 상위 25종목", top_volume_stocks)
            
    print(f"\n📁 [저장 완료] 위 목록이 '{filename}' 위치에 안전하게 저장되었습니다.")
    
    # 데이터베이스에 저장
    save_to_sqlite(top_value_stocks, top_volume_stocks, output_dir)
    
    # 이메일 발송 시도
    send_email_report(top_value_stocks, top_volume_stocks)
