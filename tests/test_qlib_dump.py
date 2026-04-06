import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data import load_kline
from src.data.qlib_dump import dump_symbol_to_qlib

def test_dump():
    symbol = "000001"
    try:
        df = load_kline(symbol, "daily")
        if df is not None and len(df) > 0:
            target_dir = f"H:/股票信息/股票数据库/daban/股票数据/{symbol}/qlib"
            dump_symbol_to_qlib(symbol, df, target_dir, freq='day')
            print("Dump test execution finished.")
        else:
            print("No data available from load_kline")
    except Exception as e:
        print(f"Error testing dump: {e}")

if __name__ == '__main__':
    test_dump()
