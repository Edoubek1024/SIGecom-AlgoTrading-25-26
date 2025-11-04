#!/usr/bin/env python3
"""
DIAGNOSTIC TEST SCRIPT
This script tests available resolutions and data for your Traydner API
"""

from TraydnerAPI import TraydnerAPI
from requests.exceptions import HTTPError
import traceback

# Configuration
API_KEY = "891830748679422e99229f7478d950fa.innE8dfKNvJ7FMeDc8afyGBwEDnRa7_UMq_8iOdIht-UOnP5rjPcd2RUPTfzefNa"
SYMBOL = "BTC"
RESOLUTIONS_TO_TEST = ["1m", "5m", "15m", "30m", "1h", "4h", "D"]

def main():
    print("="*60)
    print("TESTING AVAILABLE RESOLUTIONS FOR BTC")
    print("="*60)

    try:
        client = TraydnerAPI(api_key=API_KEY)
        
        # Test 1: API Connection
        print("\n1. Testing API Connection...")
        balance = client.get_balance()
        print(f"   ✓ API Connected. Balance: {balance.get('balance')}")
        
        # Test 2: Current Price
        print("\n2. Testing Current Price...")
        price = client.get_price(SYMBOL)
        print(f"   ✓ Current {SYMBOL} Price: {price.get('price')}")
        
        # Test 3: Market Status
        print("\n3. Testing Market Status...")
        status = client.get_market_status(symbol=SYMBOL)
        print(f"   ✓ Market Open: {status.get('isOpen')}")
        
        # Test 4: Historical Data for Each Resolution
        print("\n4. Testing Historical Data Resolutions...")
        print("-" * 60)
        
        available_resolutions = []
        
        for resolution in RESOLUTIONS_TO_TEST:
            try:
                print(f"\n   Testing {resolution}...")
                history = client.get_history(symbol=SYMBOL, resolution=resolution, limit=5)
                
                if history.get('history') and len(history.get('history', [])) > 0:
                    candle_count = len(history.get('history', []))
                    first_candle = history.get('history')[0]
                    
                    print(f"   ✓ {resolution}: AVAILABLE")
                    print(f"      - Received {candle_count} candles")
                    print(f"      - Sample close: {first_candle.get('close')}")
                    print(f"      - Sample volume: {first_candle.get('volume')}")
                    
                    available_resolutions.append(resolution)
                else:
                    print(f"   ✗ {resolution}: No data returned")
                    
            except HTTPError as e:
                if e.response.status_code == 404:
                    print(f"   ✗ {resolution}: NOT AVAILABLE (404 - No data)")
                else:
                    print(f"   ✗ {resolution}: HTTP Error {e.response.status_code}")
            except Exception as e:
                print(f"   ✗ {resolution}: ERROR - {e}")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        if available_resolutions:
            print(f"\n✓ Available resolutions: {', '.join(available_resolutions)}")
            print(f"\nRecommended configurations for your strategies:")
            print("-" * 60)
            
            # MeanReversionTrader suggestions
            print("\nMeanReversionTrader:")
            for res in available_resolutions[:3]:  # Top 3
                print(f"   - resolution: \"{res}\"")
            
            # MomentumTrader suggestions
            print("\nMomentumTrader:")
            for res in available_resolutions[:3]:  # Top 3
                print(f"   - resolution: \"{res}\"")
                if res == "1m":
                    print(f"     (14 candles = 14 minutes lookback)")
                elif res == "5m":
                    print(f"     (14 candles = 70 minutes lookback)")
                elif res == "15m":
                    print(f"     (14 candles = 3.5 hours lookback)")
                elif res == "30m":
                    print(f"     (14 candles = 7 hours lookback)")
                elif res == "1h":
                    print(f"     (14 candles = 14 hours lookback)")
        else:
            print("\n✗ WARNING: No historical data available!")
            print("   Your API might only support real-time data.")
            print("   Try testing with different symbols or check API documentation.")
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        traceback.print_exc()

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
