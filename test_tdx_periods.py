import sys
import os
import pandas as pd
from pathlib import Path

# Add root to path
root = r"h:\zzy-code\my_stocks"
sys.path.insert(0, root)

# TDX 插件路径
_tdx_user_path = r"D:\8TDX\PYPlugins\user"
if _tdx_user_path not in sys.path:
    sys.path.insert(0, _tdx_user_path)

try:
    from tqcenter import tq
    print("tqcenter found.")
    
    # Initialize
    TDX_WORK_DIR = Path(r"D:\8TDX\PYPlugins\user\txd_first")
    os.chdir(str(TDX_WORK_DIR))
    tq.initialize(__file__)
    print("TDX initialized.")
    
    symbol = "000001.SZ"
    periods = ["1m", "5m", "15m", "30m", "60m", "1d"]
    
    for p in periods:
        print(f"\nTesting period: {p}")
        try:
            data = tq.get_market_data(
                stock_list=[symbol],
                start_time="20260318",
                end_time="20260319",
                period=p,
                dividend_type='none',
                fill_data=False
            )
            if data and 'Close' in data and not data['Close'].empty:
                print(f"  [OK] Successfully read {p} data. Rows: {len(data['Close'])}")
                print(f"  Index (first 2): {data['Close'].index[:2]}")
                print(f"  Columns: {data['Close'].columns}")
            else:
                print(f"  [FAIL] No data for {p}")
        except Exception as e:
            print(f"  [ERROR] Failed to read {p}: {e}")
            
    tq.close()
    print("\nTDX closed.")

except Exception as e:
    print(f"Setup failed: {e}")
    import traceback
    traceback.print_exc()
