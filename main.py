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


def download_data(timeframe=None, timeframe_name=None):
    """Download historical data from MT5"""
    if timeframe is None:
        timeframe = config.TIMEFRAME
    if timeframe_name is None:
        timeframe_name = config.get_timeframe_string(timeframe)

    print("=" * 70)
    print(f"DOWNLOADING {timeframe_name} DATA")
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
            timeframe=timeframe,
            start_date=config.DATA_START_DATE,
            end_date=config.DATA_END_DATE
        )

        if df is None:
            return None

        raw_file = config.get_raw_data_file(timeframe)
        connector.save_to_csv(df, raw_file)
        return df

    finally:
        connector.shutdown()


def calculate_indicators(df, timeframe_name="H1"):
    """Calculate all technical indicators"""
    print("\n" + "=" * 70)
    print(f"CALCULATING {timeframe_name} INDICATORS")
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


def detect_setups(df, df_htf, start_date, end_date):
    """Detect trading setups"""
    print("\n" + "=" * 70)
    print("SETUP DETECTION")
    print("=" * 70)

    # Save processed DataFrame with ALL indicators (complete dataset)
    processed_file = config.get_processed_file()
    df.to_csv(processed_file, index=False)
    print(f"💾 Processed data saved: {processed_file} ({len(df)} candles)")

    # Detect setups
    detector = SetupDetector(
        symbol=config.SYMBOL,
        min_separation_pips=config.EMA_CROSS_MIN_SEPARATION,
        stop_loss_pips=config.STOP_LOSS_PIPS,
        use_di_h4_filter=config.USE_DI_H4_FILTER,
        di_h4_min_diff=config.DI_H4_MIN_DIFF,
        use_be_atr=config.USE_BE_ATR,
        be_atr_multiplier=config.BE_ATR_MULTIPLIER,
        use_tp_atr=config.USE_TP_ATR,
        tp_atr_multiplier=config.TP_ATR_MULTIPLIER
    )

    setups = detector.detect_all_setups(
        df,
        df_htf=df_htf,
        start_date=start_date,
        end_date=end_date
    )

    detector.print_setups()

    if setups:
        results_file = config.get_results_file(start_date, end_date)
        detector.export_to_csv(results_file)

    detector.get_executive_summary(config.SYMBOL, start_date, end_date)

    return setups


def load_or_download_data(timeframe, timeframe_name):
    """Load existing data or download new"""
    raw_file = config.get_raw_data_file(timeframe)

    if os.path.exists(raw_file):
        print(f"\n📂 Loading existing {timeframe_name} data: {raw_file}")
        df = pd.read_csv(raw_file)
        df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"✅ {len(df)} candles loaded")
        return df
    else:
        return download_data(timeframe, timeframe_name)


def main():
    """Complete pipeline: Download → Indicators → Detection"""
    os.makedirs(config.DATA_FOLDER, exist_ok=True)
    os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
    os.makedirs(config.LOGS_FOLDER, exist_ok=True)

    # Print filter configuration
    print("\n" + "=" * 70)
    print("ARMS v1.0 - FILTER CONFIGURATION")
    print("=" * 70)
    print(f"🔧 DI H4 Filter: {'ON' if config.USE_DI_H4_FILTER else 'OFF'} (min diff: {config.DI_H4_MIN_DIFF})")
    print(f"🔧 BE ATR Filter: {'ON' if config.USE_BE_ATR else 'OFF'} (multiplier: {config.BE_ATR_MULTIPLIER})")
    print(f"🔧 TP ATR Filter: {'ON' if config.USE_TP_ATR else 'OFF'} (multiplier: {config.TP_ATR_MULTIPLIER})")
    print("=" * 70)

    raw_file_h1 = config.get_raw_data_file(config.TIMEFRAME)
    raw_file_h4 = config.get_raw_data_file(config.TIMEFRAME_HTF)

    # Check if we need to re-download
    if os.path.exists(raw_file_h1):
        print(f"\n📂 Existing H1 data: {raw_file_h1}")
        if config.USE_DI_H4_FILTER and os.path.exists(raw_file_h4):
            print(f"📂 Existing H4 data: {raw_file_h4}")

        response = input("\nRe-download data? (y/n): ").lower()

        if response == 'y':
            # Download H1
            df_h1 = download_data(config.TIMEFRAME, "H1")
            if df_h1 is None:
                return

            # Download H4 if filter is enabled
            if config.USE_DI_H4_FILTER:
                df_h4 = download_data(config.TIMEFRAME_HTF, "H4")
                if df_h4 is None:
                    return
            else:
                df_h4 = None
        else:
            # Load existing H1
            df_h1 = load_or_download_data(config.TIMEFRAME, "H1")
            if df_h1 is None:
                return

            # Load existing H4 if filter is enabled
            if config.USE_DI_H4_FILTER:
                df_h4 = load_or_download_data(config.TIMEFRAME_HTF, "H4")
                if df_h4 is None:
                    return
            else:
                df_h4 = None
    else:
        # Download H1
        df_h1 = download_data(config.TIMEFRAME, "H1")
        if df_h1 is None:
            return

        # Download H4 if filter is enabled
        if config.USE_DI_H4_FILTER:
            df_h4 = download_data(config.TIMEFRAME_HTF, "H4")
            if df_h4 is None:
                return
        else:
            df_h4 = None

    # Calculate indicators for H1
    df_h1_processed = calculate_indicators(df_h1, "H1")

    # Calculate indicators for H4 if needed
    if config.USE_DI_H4_FILTER and df_h4 is not None:
        df_h4_processed = calculate_indicators(df_h4, "H4")
        # Save H4 processed data
        processed_file_h4 = config.get_processed_file(config.TIMEFRAME_HTF)
        df_h4_processed.to_csv(processed_file_h4, index=False)
        print(f"💾 H4 processed data saved: {processed_file_h4}")
    else:
        df_h4_processed = None

    # Detect setups
    setups = detect_setups(
        df_h1_processed,
        df_h4_processed,
        config.ANALYSIS_START_DATE,
        config.ANALYSIS_END_DATE
    )

    print("\n" + "=" * 70)
    print("✅ PIPELINE COMPLETED")
    print("=" * 70)
    print("\n📁 Generated files:")
    print(f"   1. {config.get_raw_data_file()} - Raw H1 data from MT5")
    if config.USE_DI_H4_FILTER:
        print(f"   2. {config.get_raw_data_file(config.TIMEFRAME_HTF)} - Raw H4 data from MT5")
    print(f"   3. {config.get_processed_file()} - H1 candles with indicators")
    if config.USE_DI_H4_FILTER:
        print(f"   4. {config.get_processed_file(config.TIMEFRAME_HTF)} - H4 candles with indicators")
    print(f"   5. {config.get_results_file(config.ANALYSIS_START_DATE, config.ANALYSIS_END_DATE)} - Detected setups")
    print("=" * 70)


if __name__ == "__main__":
    main()