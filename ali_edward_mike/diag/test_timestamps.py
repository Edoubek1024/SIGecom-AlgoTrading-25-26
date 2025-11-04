#!/usr/bin/env python3
"""
Inspect candle data with specific timestamp ranges
"""

from TraydnerAPI import TraydnerAPI
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
import time

API_KEY = "891830748679422e99229f7478d950fa.innE8dfKNvJ7FMeDc8afyGBwEDnRa7_UMq_8iOdIht-UOnP5rjPcd2RUPTfzefNa"
SYMBOL = "BTC"
RESOLUTION = "1m"
LIMIT = 20

def test_with_timestamps():
    print("="*100)
    print(f"TESTING HISTORY WITH TIMESTAMP PARAMETERS")
    print("="*100)
    
    try:
        client = TraydnerAPI(api_key=API_KEY)
        
        # Get current time
        now = datetime.now()
        current_timestamp = int(time.time())
        
        print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current timestamp: {current_timestamp}")
        
        # Test 1: Last 20 minutes (no timestamp parameters)
        print("\n" + "="*100)
        print("TEST 1: No timestamp parameters (default behavior)")
        print("="*100)
        
        history1 = client.get_history(symbol=SYMBOL, resolution=RESOLUTION, limit=LIMIT)
        candles1 = history1.get('history', [])
        print(f"Received {len(candles1)} candles")
        
        if candles1:
            analyze_candles(candles1, "No timestamps")
        
        # Test 2: Last 20 minutes with end_ts
        print("\n" + "="*100)
        print("TEST 2: With end_ts = now (explicit end time)")
        print("="*100)
        
        history2 = client.get_history(
            symbol=SYMBOL, 
            resolution=RESOLUTION, 
            end_ts=current_timestamp,
            limit=LIMIT
        )
        candles2 = history2.get('history', [])
        print(f"Received {len(candles2)} candles")
        
        if candles2:
            analyze_candles(candles2, "With end_ts")
        
        # Test 3: Specific time range (last 20 minutes)
        print("\n" + "="*100)
        print("TEST 3: With start_ts and end_ts (specific 20-minute range)")
        print("="*100)
        
        start_time = current_timestamp - (20 * 60)  # 20 minutes ago
        end_time = current_timestamp
        
        print(f"Start: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End:   {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        history3 = client.get_history(
            symbol=SYMBOL, 
            resolution=RESOLUTION,
            start_ts=start_time,
            end_ts=end_time,
            limit=LIMIT
        )
        candles3 = history3.get('history', [])
        print(f"Received {len(candles3)} candles")
        
        if candles3:
            analyze_candles(candles3, "With start_ts and end_ts")
        
        # Test 4: Recent 5 minutes only
        print("\n" + "="*100)
        print("TEST 4: Last 5 minutes only (smaller range)")
        print("="*100)
        
        start_time_5min = current_timestamp - (5 * 60)
        
        print(f"Start: {datetime.fromtimestamp(start_time_5min).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End:   {datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        
        history4 = client.get_history(
            symbol=SYMBOL, 
            resolution=RESOLUTION,
            start_ts=start_time_5min,
            end_ts=current_timestamp,
            limit=5
        )
        candles4 = history4.get('history', [])
        print(f"Received {len(candles4)} candles")
        
        if candles4:
            analyze_candles(candles4, "Last 5 minutes")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

def analyze_candles(candles, test_name):
    """Analyze a set of candles"""
    
    print(f"\nAnalysis for: {test_name}")
    print("-" * 100)
    
    closes = []
    timestamps = []
    
    for i, candle in enumerate(candles, 1):
        timestamp = candle.get('t', 'N/A')
        close = candle.get('close', 0)
        
        closes.append(close)
        
        # Convert timestamp
        if isinstance(timestamp, (int, float)):
            if timestamp > 10**10:  # milliseconds
                dt = datetime.fromtimestamp(timestamp / 1000)
                timestamps.append(timestamp / 1000)
            else:  # seconds
                dt = datetime.fromtimestamp(timestamp)
                timestamps.append(timestamp)
            datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            datetime_str = 'N/A'
            timestamps.append(None)
        
        print(f"  #{i:<3} {datetime_str:<25} Close: ${close:>12,.2f}")
    
    # Statistics
    if closes:
        mean = sum(closes) / len(closes)
        min_close = min(closes)
        max_close = max(closes)
        
        print(f"\n  Mean:  ${mean:,.2f}")
        print(f"  Min:   ${min_close:,.2f}")
        print(f"  Max:   ${max_close:,.2f}")
        print(f"  Range: ${max_close - min_close:,.2f}")
    
    # Time analysis
    if timestamps and all(t is not None for t in timestamps):
        time_span = timestamps[-1] - timestamps[0]
        print(f"\n  Time span: {time_span/60:.1f} minutes")
        
        # Check gaps
        gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            print(f"  Avg gap: {avg_gap:.1f} seconds")
            
            # Find unusual gaps
            unusual = [(i+1, gap) for i, gap in enumerate(gaps) if abs(gap - 60) > 10]
            if unusual:
                print(f"  ⚠️  Unusual gaps: {unusual}")
    
    print()

if __name__ == "__main__":
    test_with_timestamps()
