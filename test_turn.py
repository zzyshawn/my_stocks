import sys
sys.path.insert(0, r"h:\zzy-code\my_stocks")

from src.data.history_tdx.tdx_client import tdx_login, get_tdx_data

tdx_login(1)
df = get_tdx_data("000001", "d", "2026-03-18", "2026-03-19")
print("=== Daily data with turnover ===")
print(df.columns.tolist())
print(df)
print(f"\nTurnover values: {df['turn'].tolist() if 'turn' in df.columns else 'NOT FOUND'}")
tdx_login(0)
