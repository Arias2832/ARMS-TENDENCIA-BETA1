"""
ARMS v1.0 - Adaptive Regime Market Strategy
Main Pipeline: Download → Indicators → Detection
"""

import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime
from core.mt5_connector import MT5Connector
from core.indicators import IndicatorCalculator
from core.setup_detector import SetupDetector
import config


def download_data():
    """Download historical data from MT5"""
    print("=" * 70)
    print("STEP 1: HISTORICAL DATA DOWNLOAD")
    print("=" * 70)

    connector = MT5Connector()

    try:
        if not connector.initialize(
                login=config.MT5_LOGIN,
                password=config.MT5_PASSWORD,
                server=config.MT5_SERVER
        ):
            print("\n❌ Could not connect to MT5")
            return None

        df = connector.download_historical_data(
            symbol=config.SYMBOL,
            timeframe=config.TIMEFRAME,
            start_date=config.DATA_START_DATE,
            end_date=config.DATA_END_DATE
        )

        if df is None:
            return None

        raw_file = config.get_raw_data_file()
        connector.save_to_csv(df, raw_file)
        return df

    finally:
        connector.shutdown()


def calculate_indicators(df):
    """Calculate all technical indicators"""
    print("\n" + "=" * 70)
    print("STEP 2: INDICATOR CALCULATION")
    print("=" * 70)

    calculator = IndicatorCalculator(
        ema_period=config.EMA_PERIOD,
        ema_mid=config.EMA_PERIOD_MID,
        ema_long=config.EMA_PERIOD_LONG,
        atr_period=config.ATR_PERIOD,
        adx_period=config.ADX_PERIOD,
        rsi_period=config.RSI_PERIOD,
        macd_fast=config.MACD_FAST,
        macd_slow=config.MACD_SLOW,
        macd_signal=config.MACD_SIGNAL,
        volume_sma=config.VOLUME_SMA_PERIOD,
        atr_adjustment=config.ATR_ADJUSTMENT_FACTOR
    )

    df_with_indicators = calculator.calculate_all_indicators(df)
    calculator.get_indicator_summary(df_with_indicators)

    return df_with_indicators


def detect_setups(df, start_date, end_date):
    """Detect trading setups"""
    print("\n" + "=" * 70)
    print("STEP 3: SETUP DETECTION")
    print("=" * 70)

    # Save processed DataFrame with ALL indicators (complete dataset)
    processed_file = config.get_processed_file()
    df.to_csv(processed_file, index=False)
    print(f"💾 Processed data saved: {processed_file} ({len(df)} candles)")

    # Detect setups
    detector = SetupDetector(
        symbol=config.SYMBOL,
        min_separation_pips=config.EMA_CROSS_MIN_SEPARATION,
        stop_loss_pips=config.STOP_LOSS_PIPS
    )

    setups = detector.detect_all_setups(
        df,
        start_date=start_date,
        end_date=end_date
    )

    detector.print_setups()

    if setups:
        results_file = config.get_results_file(start_date, end_date)
        detector.export_to_csv(results_file)

    detector.get_executive_summary(config.SYMBOL, start_date, end_date)

    return setups


def main():
    """Complete pipeline: Download → Indicators → Detection"""
    os.makedirs(config.DATA_FOLDER, exist_ok=True)
    os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
    os.makedirs(config.LOGS_FOLDER, exist_ok=True)

    raw_file = config.get_raw_data_file()

    # STEP 1: Get data
    if os.path.exists(raw_file):
        print(f"\n📂 Existing raw data: {raw_file}")
        response = input("\nRe-download data? (y/n): ").lower()

        if response == 'y':
            df = download_data()
            if df is None:
                return
        else:
            print("\n📊 Loading existing data...")
            df = pd.read_csv(raw_file)
            df['datetime'] = pd.to_datetime(df['datetime'])
            print(f"✅ {len(df)} candles loaded")
    else:
        df = download_data()
        if df is None:
            return

    # STEP 2: Calculate indicators (in memory)
    df_processed = calculate_indicators(df)

    # STEP 3: Detect setups and save results
    setups = detect_setups(df_processed, config.ANALYSIS_START_DATE, config.ANALYSIS_END_DATE)

    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETED")
    print("=" * 70)
    print("\n📁 Generated files:")
    print(f"   1. {config.get_raw_data_file()} - Raw data from MT5")
    print(f"   2. {config.get_processed_file()} - All candles with indicators")
    print(
        f"   3. {config.get_results_file(config.ANALYSIS_START_DATE, config.ANALYSIS_END_DATE)} - Detected setups only")
    print("=" * 70)


if __name__ == "__main__":
    main()