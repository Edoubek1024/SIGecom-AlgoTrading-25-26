#!/usr/bin/env python3
"""
Inspect the actual candle data to see why the mean is so low
"""

from TraydnerAPI import TraydnerAPI
from requests.exceptions import HTTPError

API_KEY = "891830748679422e99229f7478d950fa.innE8dfKNvJ7FMeDc8afyGBwEDnRa7_UMq_8iOdIht-UOnP5rjPcd2RUPTfzefNa"
SYMBOL = "BTC"
RESOLUTION = "1m"
LIMIT = 20

def main():
    print("="*80)
    print(f"INSPECTING LAST {LIMIT} CANDLES FOR {SYMBOL} @ {RESOLUTION}")
    print("="*80)
    
    try:
        client = TraydnerAPI(api_key=API_KEY)
        
        # Get current price first
        current = client.get_price(SYMBOL)
        current_price = current.get('price')
        print(f"\nCurrent Price: ${current_price:,.2f}")
        
        # Get historical data
        history = client.get_history(symbol=SYMBOL, resolution=RESOLUTION, limit=LIMIT)
        candles = history.get('history', [])
        
        if not candles:
            print("No candles returned!")
            return
        
        print(f"\nReceived {len(candles)} candles")
        print("\n" + "-"*100)
        print(f"{'#':<4} {'Timestamp':<20} {'Datetime':<25} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12} {'Volume':<12}")
        print("-"*100)
        
        closes = []
        timestamps_unix = []
        
        for i, candle in enumerate(candles, 1):
            timestamp = candle.get('t', 'N/A')
            open_price = candle.get('open', 0)
            high = candle.get('high', 0)
            low = candle.get('low', 0)
            close = candle.get('close', 0)
            volume = candle.get('volume', 0)
            
            closes.append(close)
            
            # Convert timestamp to readable datetime
            if isinstance(timestamp, (int, float)):
                from datetime import datetime
                # Handle both seconds and milliseconds timestamps
                if timestamp > 10**10:  # Likely milliseconds
                    dt = datetime.fromtimestamp(timestamp / 1000)
                else:  # Likely seconds
                    dt = datetime.fromtimestamp(timestamp)
                datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                timestamps_unix.append(timestamp)
            else:
                datetime_str = 'N/A'
                timestamps_unix.append(None)
            
            print(f"{i:<4} {str(timestamp):<20} {datetime_str:<25} ${open_price:<11,.2f} ${high:<11,.2f} ${low:<11,.2f} ${close:<11,.2f} {volume:<12,.2f}")
        
        # Analyze timestamps
        print("\n" + "="*80)
        print("TIMESTAMP ANALYSIS")
        print("="*80)
        
        from datetime import datetime
        if timestamps_unix and all(t is not None for t in timestamps_unix):
            # Check if timestamps are in order
            is_ordered = all(timestamps_unix[i] <= timestamps_unix[i+1] for i in range(len(timestamps_unix)-1))
            print(f"\nTimestamps in chronological order: {'✓ Yes' if is_ordered else '✗ No'}")
            
            # Calculate time gaps
            time_gaps = []
            for i in range(1, len(timestamps_unix)):
                gap = timestamps_unix[i] - timestamps_unix[i-1]
                # Convert to seconds if in milliseconds
                if timestamps_unix[0] > 10**10:
                    gap = gap / 1000
                time_gaps.append(gap)
            
            if time_gaps:
                avg_gap = sum(time_gaps) / len(time_gaps)
                min_gap = min(time_gaps)
                max_gap = max(time_gaps)
                
                print(f"\nTime gaps between candles:")
                print(f"  Average: {avg_gap:.1f} seconds ({avg_gap/60:.1f} minutes)")
                print(f"  Min:     {min_gap:.1f} seconds ({min_gap/60:.1f} minutes)")
                print(f"  Max:     {max_gap:.1f} seconds ({max_gap/60:.1f} minutes)")
                print(f"  Expected for {RESOLUTION}: {60 if RESOLUTION == '1m' else 'varies'} seconds")
                
                # Detect irregular gaps
                irregular = [i+1 for i, gap in enumerate(time_gaps) if abs(gap - 60) > 10]
                if irregular:
                    print(f"\n⚠️  Irregular time gaps detected between candles: {irregular}")
            
            # Show timestamp range
            if timestamps_unix[0] > 10**10:
                first_dt = datetime.fromtimestamp(timestamps_unix[0] / 1000)
                last_dt = datetime.fromtimestamp(timestamps_unix[-1] / 1000)
            else:
                first_dt = datetime.fromtimestamp(timestamps_unix[0])
                last_dt = datetime.fromtimestamp(timestamps_unix[-1])
            
            time_span = (last_dt - first_dt).total_seconds()
            print(f"\nTime span: {time_span/60:.1f} minutes ({time_span/3600:.2f} hours)")
            print(f"First candle: {first_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last candle:  {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate statistics
        print("\n" + "="*80)
        print("PRICE STATISTICS")
        print("="*80)
        
        mean = sum(closes) / len(closes)
        min_close = min(closes)
        max_close = max(closes)
        
        print(f"\nMean (Average) Close:  ${mean:,.2f}")
        print(f"Min Close:             ${min_close:,.2f}")
        print(f"Max Close:             ${max_close:,.2f}")
        print(f"Current Price:         ${current_price:,.2f}")
        print(f"Range:                 ${max_close - min_close:,.2f}")
        
        # Check for anomalies
        print("\n" + "="*80)
        print("ANOMALY DETECTION")
        print("="*80)
        
        # Find prices significantly different from current
        threshold = current_price * 0.10  # 10% difference
        anomalies = []
        
        for i, close in enumerate(closes, 1):
            diff_pct = abs(close - current_price) / current_price * 100
            if diff_pct > 10:
                anomalies.append((i, close, diff_pct))
        
        if anomalies:
            print(f"\n⚠️  Found {len(anomalies)} candles with >10% difference from current price:")
            for idx, price, diff in anomalies:
                print(f"   Candle #{idx}: ${price:,.2f} ({diff:.1f}% different)")
        else:
            print("\n✓ No significant anomalies detected")
        
        # Recommendation
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)
        
        if anomalies:
            print("\n⚠️  Data quality issue detected!")
            print("   The historical data contains prices very different from current price.")
            print("   This is why your mean/SMA is so low.")
            print("\n   Possible solutions:")
            print("   1. Use a shorter period (try mean_period=5 instead of 20)")
            print("   2. Use a longer resolution (try '5m' or '15m' instead of '1m')")
            print("   3. Contact API provider about data quality")
        else:
            print("\n✓ Data looks reasonable")
            print("   The low mean might be due to recent price movements.")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
