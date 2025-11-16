"""
ARMS v1.0 - Trend Following Setup Detector
EMA20/EMA50 Crossover Strategy
DEBUG VERSION - Focused on 29-30 Oct issue
"""

import pandas as pd
import numpy as np
import config


class SetupDetector:
    """Trading setup detector for trend following strategy"""

    def __init__(self, symbol, min_separation_pips=3, stop_loss_pips=20):
        """
        Initialize detector with automatic pip factor detection

        Args:
            symbol: Currency pair (for automatic pip factor)
            min_separation_pips: Minimum pip separation to activate entry search
            stop_loss_pips: Fixed stop loss in pips
        """
        self.symbol = symbol.upper()
        self.min_separation_pips = min_separation_pips
        self.stop_loss_pips = stop_loss_pips
        self.setups = []

        # Auto-detect pip factor
        self.pip_factor = config.get_pip_factor(symbol)
        self.symbol_info = config.get_symbol_info(symbol)

        print(f"\n📊 AUTO CONFIGURATION FOR {self.symbol}:")
        print(f"   📍 Type: {self.symbol_info['description']}")
        print(f"   🔢 Decimals: {self.symbol_info['decimals']}")
        print(f"   🧮 Pip factor: {self.pip_factor}")
        print(f"   📏 Min separation: {self.min_separation_pips} pips")
        print(f"   🛑 Stop loss: {self.stop_loss_pips} pips")

    def detect_ema_cross(self, df, idx):
        """
        Detect EMA20/EMA50 crossover at given index

        Returns:
            'LONG' if EMA20 crosses above EMA50
            'SHORT' if EMA20 crosses below EMA50
            None if no cross
        """
        if idx == 0:
            return None

        prev_candle = df.iloc[idx - 1]
        curr_candle = df.iloc[idx]

        # Bullish cross: EMA20 was below, now above EMA50
        if prev_candle['ema20'] <= prev_candle['ema50'] and curr_candle['ema20'] > curr_candle['ema50']:
            # DEBUG: Print cross detection
            if '2025-10-29' in str(curr_candle['datetime']) or '2025-10-30' in str(curr_candle['datetime']):
                print(f"\n🔄 [CROSS DETECTED] {curr_candle['datetime']} | LONG")
                print(f"   Prev: EMA20={prev_candle['ema20']:.5f} EMA50={prev_candle['ema50']:.5f}")
                print(f"   Curr: EMA20={curr_candle['ema20']:.5f} EMA50={curr_candle['ema50']:.5f}")
            return 'LONG'

        # Bearish cross: EMA20 was above, now below EMA50
        if prev_candle['ema20'] >= prev_candle['ema50'] and curr_candle['ema20'] < curr_candle['ema50']:
            # DEBUG: Print cross detection
            if '2025-10-29' in str(curr_candle['datetime']) or '2025-10-30' in str(curr_candle['datetime']):
                print(f"\n🔄 [CROSS DETECTED] {curr_candle['datetime']} | SHORT")
                print(f"   Prev: EMA20={prev_candle['ema20']:.5f} EMA50={prev_candle['ema50']:.5f}")
                print(f"   Curr: EMA20={curr_candle['ema20']:.5f} EMA50={curr_candle['ema50']:.5f}")
            return 'SHORT'

        return None

    def check_separation(self, candle):
        """
        Check if EMAs have minimum separation in pips

        Returns:
            True if separation >= min_separation_pips
        """
        ema_diff = abs(candle['ema20'] - candle['ema50'])
        ema_diff_pips = ema_diff * self.pip_factor

        is_separated = ema_diff_pips >= self.min_separation_pips

        # DEBUG: Print separation check for 29-30 Oct
        if is_separated and ('2025-10-29' in str(candle['datetime']) or '2025-10-30' in str(candle['datetime'])):
            print(f"\n✅ [SEPARATION] {candle['datetime']} | {ema_diff_pips:.2f} pips | ACTIVATED")

        return is_separated

    def check_ema_touch(self, candle):
        """
        Check if price touches EMA20

        Returns:
            True if candle's range includes EMA20
        """
        touches = candle['low'] <= candle['ema20'] <= candle['high']

        # DEBUG: Print touch checks for 29-30 Oct
        if '2025-10-29' in str(candle['datetime']) or '2025-10-30' in str(candle['datetime']):
            status = "✅ TOUCHES" if touches else "❌ NO TOUCH"
            print(
                f"   [TOUCH CHECK] {candle['datetime']} | EMA20={candle['ema20']:.5f} | High={candle['high']:.5f} | Low={candle['low']:.5f} | {status}")

        return touches

    def simulate_trade(self, df, entry_idx, direction, entry_price):
        """
        Simulate trade outcome from entry forward

        Exit conditions:
        1. Stop loss hit (20 pips fixed)
        2. EMA20 crosses EMA50 back (trend reversal)

        Returns:
            dict with trade outcome details including exit_idx and exit_type
        """
        # Calculate stop loss price
        sl_distance = self.stop_loss_pips / self.pip_factor

        if direction == 'LONG':
            sl_price = entry_price - sl_distance
        else:  # SHORT
            sl_price = entry_price + sl_distance

        # Simulate forward from entry
        for i in range(entry_idx, len(df)):
            candle = df.iloc[i]

            # Check Stop Loss FIRST (higher priority)
            if direction == 'LONG':
                if candle['low'] <= sl_price:
                    pips = (sl_price - entry_price) * self.pip_factor
                    return {
                        'outcome': 'LOSS',
                        'exit_date': candle['datetime'],
                        'exit_price': sl_price,
                        'exit_idx': i,
                        'exit_type': 'SL',
                        'pips': round(pips, 1),
                        'candles_held': i - entry_idx,
                        'exit_reason': 'Stop Loss'
                    }
            else:  # SHORT
                if candle['high'] >= sl_price:
                    pips = (entry_price - sl_price) * self.pip_factor
                    return {
                        'outcome': 'LOSS',
                        'exit_date': candle['datetime'],
                        'exit_price': sl_price,
                        'exit_idx': i,
                        'exit_type': 'SL',
                        'pips': round(pips, 1),
                        'candles_held': i - entry_idx,
                        'exit_reason': 'Stop Loss'
                    }

            # Check EMA cross reversal (exit condition)
            if i > entry_idx:  # Don't check on entry candle
                cross_direction = self.detect_ema_cross(df, i)

                # Exit if cross in opposite direction
                if direction == 'LONG' and cross_direction == 'SHORT':
                    exit_price = candle['close']
                    pips = (exit_price - entry_price) * self.pip_factor
                    outcome = 'WIN' if pips > 0 else 'LOSS'
                    return {
                        'outcome': outcome,
                        'exit_date': candle['datetime'],
                        'exit_price': exit_price,
                        'exit_idx': i,
                        'exit_type': 'CROSS',
                        'exit_cross_direction': 'SHORT',
                        'pips': round(pips, 1),
                        'candles_held': i - entry_idx,
                        'exit_reason': 'EMA Cross Reversal'
                    }

                if direction == 'SHORT' and cross_direction == 'LONG':
                    exit_price = candle['close']
                    pips = (entry_price - exit_price) * self.pip_factor
                    outcome = 'WIN' if pips > 0 else 'LOSS'
                    return {
                        'outcome': outcome,
                        'exit_date': candle['datetime'],
                        'exit_price': exit_price,
                        'exit_idx': i,
                        'exit_type': 'CROSS',
                        'exit_cross_direction': 'LONG',
                        'pips': round(pips, 1),
                        'candles_held': i - entry_idx,
                        'exit_reason': 'EMA Cross Reversal'
                    }

        # If we reach end of data without exit
        last_candle = df.iloc[-1]
        exit_price = last_candle['close']

        if direction == 'LONG':
            pips = (exit_price - entry_price) * self.pip_factor
        else:
            pips = (entry_price - exit_price) * self.pip_factor

        outcome = 'WIN' if pips > 0 else 'LOSS'

        return {
            'outcome': outcome,
            'exit_date': last_candle['datetime'],
            'exit_price': exit_price,
            'exit_idx': len(df) - 1,
            'exit_type': 'EOD',
            'pips': round(pips, 1),
            'candles_held': len(df) - entry_idx,
            'exit_reason': 'End of Data'
        }

    def detect_all_setups(self, df, start_date, end_date):
        """
        Detect all trading setups in the given period

        CORRECTED LOGIC:
        1. Detect EMA20/EMA50 cross (updates with each new cross)
        2. Wait for separation >= 3 pips (activates entry search)
        3. First candle that touches EMA20 → ENTER
        4. Exit handling:
           - Stop Loss: RESET all states, wait for NEW cross
           - Cross Reversal: Use that cross as NEW signal immediately
        """
        print(f"\n🔍 Scanning for setups from {start_date.date()} to {end_date.date()}...")

        # Filter analysis period
        mask = (df['datetime'] >= start_date) & (df['datetime'] <= end_date)
        analysis_df = df[mask].copy().reset_index(drop=True)

        if len(analysis_df) == 0:
            print("❌ No data in analysis period")
            return []

        print(f"📊 Analyzing {len(analysis_df)} candles...")
        print("\n" + "=" * 70)
        print("DEBUG MODE: Tracking 29-30 Oct period")
        print("=" * 70)

        # State variables
        last_cross_direction = None
        separation_achieved = False
        skip_until_idx = 0

        for i in range(1, len(analysis_df)):
            candle = analysis_df.iloc[i]

            # DEBUG: Show state for 29-30 Oct
            if '2025-10-29' in str(candle['datetime']) or '2025-10-30' in str(candle['datetime']):
                if i <= skip_until_idx:
                    print(f"\n⏭️  [SKIP] {candle['datetime']} | skip_until_idx={skip_until_idx}, current_idx={i}")
                    continue
                else:
                    print(
                        f"\n📍 [PROCESSING] {candle['datetime']} | Direction={last_cross_direction} | Separated={separation_achieved}")

            # Skip if we're within an exited trade period
            if i <= skip_until_idx:
                continue

            # Check for new EMA cross
            cross = self.detect_ema_cross(analysis_df, i)

            if cross:
                # New cross detected - reset and update
                last_cross_direction = cross
                separation_achieved = False
                # Continue to next candle (never enter on cross candle itself)
                continue

            # If we have a cross direction, check for entry conditions
            if last_cross_direction:
                # Check if separation achieved
                if not separation_achieved:
                    if self.check_separation(candle):
                        separation_achieved = True

                # If separation achieved, look for entry
                if separation_achieved:
                    touches_ema = self.check_ema_touch(candle)

                    if touches_ema:
                        # ENTRY CONDITIONS MET
                        print(f"\n🎯 [ENTRY] {candle['datetime']} | {last_cross_direction} @ {candle['ema20']:.5f}")

                        trade_result = self._process_entry(analysis_df, i, last_cross_direction, candle)

                        # Handle exit based on type
                        if trade_result['exit_type'] == 'SL':
                            # Stop Loss exit - RESET everything
                            skip_until_idx = trade_result['exit_idx']
                            last_cross_direction = None
                            separation_achieved = False
                            print(
                                f"   [EXIT SL] {trade_result['exit_date']} | Reset states | skip_until={skip_until_idx}")

                        elif trade_result['exit_type'] == 'CROSS':
                            # Cross reversal exit - Use as NEW signal
                            skip_until_idx = trade_result['exit_idx']
                            last_cross_direction = trade_result['exit_cross_direction']
                            separation_achieved = False
                            print(f"   [EXIT CROSS] {trade_result['exit_date']} | New direction={last_cross_direction}")

                        else:  # EOD
                            # End of data - just stop
                            skip_until_idx = trade_result['exit_idx']

        print("\n" + "=" * 70)
        print(f"✅ Setup detection completed: {len(self.setups)} setups found")
        return self.setups

    def _process_entry(self, df, entry_idx, direction, candle):
        """
        Process trade entry and simulate outcome

        Returns:
            trade_result dict with exit info
        """
        entry_price = candle['ema20']

        # Simulate trade
        trade_result = self.simulate_trade(df, entry_idx, direction, entry_price)

        # Store setup
        setup = {
            'setup_id': len(self.setups) + 1,
            'entry_date': candle['datetime'],
            'direction': direction,
            'entry_price': round(entry_price, self.symbol_info['decimals']),
            'sl_price': round(entry_price - (self.stop_loss_pips / self.pip_factor) if direction == 'LONG'
                              else entry_price + (self.stop_loss_pips / self.pip_factor),
                              self.symbol_info['decimals']),
            'exit_date': trade_result['exit_date'],
            'exit_price': round(trade_result['exit_price'], self.symbol_info['decimals']),
            'exit_reason': trade_result['exit_reason'],
            'outcome': trade_result['outcome'],
            'pips': trade_result['pips'],
            'candles_held': trade_result['candles_held']
        }

        self.setups.append(setup)
        return trade_result

    def print_setups(self):
        """Print all detected setups"""
        if not self.setups:
            print("\n❌ No setups found")
            return

        print("\n" + "=" * 100)
        print(f"DETECTED SETUPS: {len(self.setups)} total")
        print("=" * 100)

        for setup in self.setups:
            print(f"\n📍 Setup #{setup['setup_id']} - {setup['direction']}")
            print(f"   Entry: {setup['entry_date']} @ {setup['entry_price']}")
            print(f"   Exit:  {setup['exit_date']} @ {setup['exit_price']}")
            print(f"   Result: {setup['outcome']} | {setup['pips']:+.1f} pips | {setup['candles_held']} candles")
            print(f"   Exit reason: {setup['exit_reason']}")

    def export_to_csv(self, filepath):
        """Export setups to CSV"""
        if not self.setups:
            print("❌ No setups to export")
            return

        df = pd.DataFrame(self.setups)
        df.to_csv(filepath, index=False)
        print(f"\n💾 Results exported: {filepath}")

    def get_executive_summary(self, symbol, start_date, end_date):
        """Display executive summary of results"""
        if not self.setups:
            print("\n❌ No setups to summarize")
            return

        df = pd.DataFrame(self.setups)

        total_setups = len(df)
        wins = len(df[df['outcome'] == 'WIN'])
        losses = len(df[df['outcome'] == 'LOSS'])
        win_rate = (wins / total_setups * 100) if total_setups > 0 else 0

        total_pips = df['pips'].sum()
        avg_pips = df['pips'].mean()
        avg_winner = df[df['outcome'] == 'WIN']['pips'].mean() if wins > 0 else 0
        avg_loser = df[df['outcome'] == 'LOSS']['pips'].mean() if losses > 0 else 0

        print("\n" + "=" * 70)
        print(f"EXECUTIVE SUMMARY - {symbol}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print("=" * 70)
        print(f"\n📊 PERFORMANCE:")
        print(f"   Total Setups: {total_setups}")
        print(f"   Wins: {wins} | Losses: {losses}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"\n💰 PIPS:")
        print(f"   Total: {total_pips:+.1f} pips")
        print(f"   Average per trade: {avg_pips:+.1f} pips")
        print(f"   Average winner: {avg_winner:+.1f} pips")
        print(f"   Average loser: {avg_loser:+.1f} pips")
        print(f"\n⏱️ DURATION:")
        print(f"   Average hold: {df['candles_held'].mean():.1f} candles")
        print("=" * 70)