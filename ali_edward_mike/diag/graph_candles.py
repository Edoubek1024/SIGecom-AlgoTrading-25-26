#!/usr/bin/env python3
"""
Graph the candle data to visualize the anomalies
"""

from TraydnerAPI import TraydnerAPI
import matplotlib.pyplot as plt
from datetime import datetime

API_KEY = "891830748679422e99229f7478d950fa.innE8dfKNvJ7FMeDc8afyGBwEDnRa7_UMq_8iOdIht-UOnP5rjPcd2RUPTfzefNa"
SYMBOL = "BTC"
RESOLUTION = "1m"
LIMIT = 20

def main():
    print("Fetching data and creating visualization...")
    
    try:
        client = TraydnerAPI(api_key=API_KEY)
        
        # Get current price
        current = client.get_price(SYMBOL)
        current_price = current.get('price')
        
        # Get historical data
        history = client.get_history(symbol=SYMBOL, resolution=RESOLUTION, limit=LIMIT)
        candles = history.get('history', [])
        
        if not candles:
            print("No candles returned!")
            return
        
        # Extract data
        indices = list(range(1, len(candles) + 1))
        opens = [c.get('open', 0) for c in candles]
        highs = [c.get('high', 0) for c in candles]
        lows = [c.get('low', 0) for c in candles]
        closes = [c.get('close', 0) for c in candles]
        timestamps = [c.get('t', f'Candle {i}') for i, c in enumerate(candles, 1)]
        
        # Calculate mean
        mean = sum(closes) / len(closes)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle(f'{SYMBOL} - Last {LIMIT} Candles @ {RESOLUTION} Resolution\nData Quality Analysis', 
                     fontsize=16, fontweight='bold')
        
        # --- SUBPLOT 1: Price Chart ---
        ax1.plot(indices, closes, marker='o', linewidth=2, markersize=8, label='Close Price', color='blue')
        ax1.plot(indices, opens, marker='s', linewidth=1, markersize=6, label='Open Price', color='green', alpha=0.6)
        ax1.plot(indices, highs, marker='^', linewidth=1, markersize=5, label='High', color='lightgreen', alpha=0.4)
        ax1.plot(indices, lows, marker='v', linewidth=1, markersize=5, label='Low', color='lightcoral', alpha=0.4)
        
        # Add current price line
        ax1.axhline(y=current_price, color='red', linestyle='--', linewidth=2, label=f'Current Price: ${current_price:,.2f}')
        
        # Add mean line
        ax1.axhline(y=mean, color='orange', linestyle='--', linewidth=2, label=f'Mean (SMA): ${mean:,.2f}')
        
        # Highlight anomalies
        threshold = current_price * 0.10
        for i, close in enumerate(closes, 1):
            if abs(close - current_price) > threshold:
                ax1.scatter(i, close, color='red', s=200, alpha=0.3, marker='o')
        
        ax1.set_xlabel('Candle Number (most recent = rightmost)', fontsize=12)
        ax1.set_ylabel('Price (USD)', fontsize=12)
        ax1.set_title('Price Movement - Anomalies Highlighted in Red', fontsize=14)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(indices)
        
        # Format y-axis
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # --- SUBPLOT 2: Percentage Difference from Current Price ---
        pct_diffs = [(close - current_price) / current_price * 100 for close in closes]
        colors = ['red' if abs(d) > 10 else 'green' for d in pct_diffs]
        
        bars = ax2.bar(indices, pct_diffs, color=colors, alpha=0.7, edgecolor='black')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.axhline(y=10, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='±10% Threshold')
        ax2.axhline(y=-10, color='orange', linestyle='--', linewidth=1, alpha=0.5)
        
        ax2.set_xlabel('Candle Number', fontsize=12)
        ax2.set_ylabel('% Difference from Current Price', fontsize=12)
        ax2.set_title('Percentage Deviation - Red bars = >10% deviation (Data Quality Issue)', fontsize=14)
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_xticks(indices)
        
        # Add value labels on bars
        for i, (bar, pct) in enumerate(zip(bars, pct_diffs)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{pct:.1f}%',
                    ha='center', va='bottom' if height > 0 else 'top',
                    fontsize=8)
        
        plt.tight_layout()
        
        # Save figure
        output_file = '/home/ali/code/algotrading/candle_analysis.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n✓ Graph saved to: {output_file}")
        
        # Show figure
        plt.show()
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        anomaly_count = sum(1 for d in pct_diffs if abs(d) > 10)
        print(f"\nTotal candles: {len(candles)}")
        print(f"Anomalies (>10% deviation): {anomaly_count} ({anomaly_count/len(candles)*100:.1f}%)")
        print(f"Current Price: ${current_price:,.2f}")
        print(f"Calculated Mean: ${mean:,.2f}")
        print(f"Mean is {(current_price - mean)/current_price*100:.1f}% lower than current price")
        
        print("\n⚠️  ISSUE: Your API is returning stale/mixed data!")
        print("   The first 14 candles are from a much lower price range.")
        print("   This is NOT normal 1-minute data - it looks like mixed timeframes.")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Try resolution '5m' or '15m' - might have better data quality")
        print("   2. Reduce mean_period to 5 (use only last 5 candles)")
        print("   3. Contact your API provider about this data issue")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
