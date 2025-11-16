"""
ARMS v1.0 - Adaptive Regime Market Strategy
Trend Following Configuration
"""

from datetime import datetime
import MetaTrader5 as mt5

# MT5 Connection
MT5_LOGIN = None
MT5_PASSWORD = ""
MT5_SERVER = "FPMarkets-Demo"

# Trading pair and timeframe
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_H1

# Timeframe mapping for file naming
TIMEFRAME_MAP = {
    mt5.TIMEFRAME_M15: "M15",
    mt5.TIMEFRAME_M30: "M30",
    mt5.TIMEFRAME_H1: "H1",
    mt5.TIMEFRAME_H4: "H4",
    mt5.TIMEFRAME_H6: "H6",
    mt5.TIMEFRAME_D1: "D1"
}

# Data download period (includes indicator warm-up)
DATA_START_DATE = datetime(2019, 1, 1)
DATA_END_DATE = datetime(2025, 11, 16)

# Analysis period (actual trading period)
ANALYSIS_START_DATE = datetime(2025, 9, 23)
ANALYSIS_END_DATE = datetime(2025, 11, 16)

# Technical Indicators
EMA_PERIOD = 20
EMA_PERIOD_MID = 50
EMA_PERIOD_LONG = 200
ATR_PERIOD = 20
ADX_PERIOD = 14
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
VOLUME_SMA_PERIOD = 20

# ATR Calibration
ATR_ADJUSTMENT_FACTOR = 0.99

# Trading Strategy - Trend Following
EMA_CROSS_MIN_SEPARATION = 3  # Minimum pips separation to activate entry search
STOP_LOSS_PIPS = 20  # Fixed stop loss in pips

# File Management
DATA_FOLDER = "Data"
RESULTS_FOLDER = "results"
LOGS_FOLDER = "logs"


def get_timeframe_string():
    """Get timeframe string for current TIMEFRAME"""
    return TIMEFRAME_MAP.get(TIMEFRAME, "H1")


def get_raw_data_file():
    """Generate raw data filename"""
    tf_str = get_timeframe_string()
    return f"{DATA_FOLDER}/{SYMBOL}_{tf_str}_raw.csv"


def get_processed_file():
    """Generate processed data filename (with all indicators)"""
    tf_str = get_timeframe_string()
    return f"{RESULTS_FOLDER}/{SYMBOL}_{tf_str}_processed.csv"


def get_results_file(start_date, end_date):
    """Generate results filename (only detected setups)"""
    tf_str = get_timeframe_string()
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    return f"{RESULTS_FOLDER}/{SYMBOL}_{tf_str}_results_{start_str}_{end_str}.csv"


# Pip factor detection
def get_pip_factor(symbol):
    """Get pip conversion factor based on symbol"""
    two_decimal_pairs = [
        "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY", "CADJPY", "NZDJPY"
    ]
    return 100 if symbol.upper() in two_decimal_pairs else 10000


def get_symbol_info(symbol):
    """Get complete symbol information"""
    pip_factor = get_pip_factor(symbol)
    decimals = 2 if pip_factor == 100 else 4
    description = "JPY pair (2 decimals)" if pip_factor == 100 else "Major pair (4 decimals)"

    return {
        'pip_factor': pip_factor,
        'decimals': decimals,
        'description': description
    }


# Logging
LOG_LEVEL = "INFO"
LOG_FILE = f"{LOGS_FOLDER}/arms_v1.log"