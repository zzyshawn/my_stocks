import sys
import os
import pandas as pd
from pathlib import Path

# Add root to path
root = r"h:\zzy-code\my_stocks"
sys.path.insert(0, root)

try:
    from src.data.history.kline_fetcher import KLineFetcher
    from src.data.history_tdx.tdx_client import tdx_login
    
    # Initialize connection
    tdx_login(1)
    
    fetcher = KLineFetcher(data_dir="tmp_data", source="tdx")
    symbol = "000001" # 6位代码
    
    print("Testing 5m data...")
    df_5 = fetcher.fetch_minute(symbol, "2026-03-18", "2026-03-18", "5")
    if not df_5.empty:
        print(f"5m Data fetched successfully. Rows: {len(df_5)}")
        print(f"First row '日期' (formatted): {df_5['日期'].iloc[0]}")
    else:
        print("5m Data is empty.")
        
    print("\nTesting 30m data...")
    df_30 = fetcher.fetch_minute(symbol, "2026-03-18", "2026-03-18", "30")
    if not df_30.empty:
        print(f"30m Data fetched successfully. Rows: {len(df_30)}")
        print(f"First row '日期' (formatted): {df_30['日期'].iloc[0]}")
    else:
        print("30m Data is empty.")

    tdx_login(0)

except Exception as e:
    print(f"Verification error: {e}")
    import traceback
    traceback.print_exc()
