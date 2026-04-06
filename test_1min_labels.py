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
    TDX_WORK_DIR = Path(r"D:\8TDX\PYPlugins\user\txd_first")
    os.chdir(str(TDX_WORK_DIR))
    tq.initialize(__file__)
    
    symbol = "000001.SZ"
    # Try different labels for 1-min
    for p in ["1", "1min", "m1", "60s"]:
        print(f"Testing labels: {p}")
        try:
            data = tq.get_market_data([symbol], period=p, start_time="20260318", end_time="20260319")
            if data and 'Close' in data and not data['Close'].empty:
                print(f"  [FOUND] Label '{p}' works!")
                break
        except:
            pass
            
    tq.close()
except Exception as e:
    print(f"Error: {e}")
