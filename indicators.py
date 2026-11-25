import pandas as pd
import ta

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    OHLCV 데이터프레임에 기술적 지표(보조지표)를 추가합니다.
    """
    if df.empty or len(df) < 30:
        return df

    # 1. Moving Averages (이동평균선)
    df['MA5'] = ta.trend.sma_indicator(df['close'], window=5)
    df['MA20'] = ta.trend.sma_indicator(df['close'], window=20)
    df['MA60'] = ta.trend.sma_indicator(df['close'], window=60)
    
    # 2. RSI (Relative Strength Index)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    
    # 3. MACD (Moving Average Convergence Divergence)
    macd = ta.trend.MACD(df['close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()
    
    # 4. Bollinger Bands (볼린저 밴드)
    bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    df['BB_Mid'] = bollinger.bollinger_mavg()

    # 결측치(NaN) 처리 - 지표 계산 시 초기 데이터 부족으로 생기는 NaN 제거 또는 유지
    # df.fillna(method='bfill', inplace=True)
    
    return df

if __name__ == "__main__":
    # 간단한 테스트
    mock_data = {
        'close': [50000 + i*100 for i in range(100)]
    }
    df_mock = pd.DataFrame(mock_data)
    df_mock = add_technical_indicators(df_mock)
    print(df_mock.tail())
