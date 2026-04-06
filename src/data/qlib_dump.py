import sys
import os
import yaml
import tempfile
import pandas as pd
from pathlib import Path

# 将 QLib 源码及 scripts 目录挂载至系统路径
sys.path.insert(0, r"D:\code\qlib")
sys.path.insert(0, r"D:\code\qlib\scripts")

try:
    from dump_bin import DumpDataAll
except ImportError as e:
    DumpDataAll = None
    print(f"Warning: DumpDataAll is not available. {e}")

def get_config_path() -> Path:
    """动态获取项目根目录下的 config.yaml"""
    # src/data/qlib_dump.py -> src/data -> src -> my_stocks
    root_dir = Path(__file__).resolve().parent.parent.parent
    return root_dir / "config" / "config.yaml"

def load_backtest_targets() -> list:
    """从 config.yaml 读取回测目标的 Excel 路径并获取股票列表"""
    path = get_config_path()
    if not path.exists():
        print(f"配置文件不存在: {path}")
        return []
        
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    target_cfg = config.get("backtest", {}).get("target_list", {})
    if not target_cfg:
        print("未在配置中找到回测目标清单 (backtest.target_list)")
        return []

    target_file = Path(target_cfg.get("dir", "")) / target_cfg.get("file", "")
    code_col = target_cfg.get("code_column", "股票代码")
    
    if not target_file.exists():
        print(f"回测目标 Excel 文件不存在: {target_file}")
        return []
        
    df = pd.read_excel(target_file)
    if code_col not in df.columns:
        print(f"文件中不包含列：{code_col}")
        return []
        
    symbols = df[code_col].astype(str).tolist()
    # 补充成6位股票代码
    symbols = [s.zfill(6) for s in symbols]
    return symbols

def get_qlib_dir() -> str:
    path = get_config_path()
    default_dir = str(path.parent.parent / "src" / "data" / "qlib_data")
    if not path.exists():
        return default_dir
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get("data", {}).get("qlib_dir", default_dir)

def format_df_for_qlib(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    col_map = {
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
        '成交额': 'amount',
        '换手率': 'turnover'
    }
    
    df_qlib = df.copy()
    
    # 提前移除非索引的 'date' 列，避免 reset_index 时发生名字冲突
    if 'date' in df_qlib.columns:
        df_qlib = df_qlib.drop(columns=['date'])
        
    rename_dict = {col: col_map[col] for col in df_qlib.columns if col in col_map}
    df_qlib.rename(columns=rename_dict, inplace=True)
    
    if df_qlib.index.name != 'date':
        df_qlib.index.name = 'date'
    df_qlib = df_qlib.reset_index()
    
    keep_cols = ['date'] + list(col_map.values())
    valid_cols = [c for c in keep_cols if c in df_qlib.columns]
    df_qlib = df_qlib[valid_cols]

    sz_sh_symbol = f"SH{symbol}" if str(symbol).startswith('6') else f"SZ{symbol}"
    df_qlib['symbol'] = sz_sh_symbol
    return df_qlib

def dump_all_targets_to_unified_qlib(freq='day'):
    """将所有目标股票的数据导入到统一的 QLib 数据库结构中"""
    if DumpDataAll is None:
        raise ImportError("qlib is not installed.")

    symbols = load_backtest_targets()
    if not symbols:
        print("未找到有效的回测目标。")
        return
        
    print(f"找到 {len(symbols)} 个回测目标股票，开始进行转换为统一个 QLib 数据库...")
    
    root_dir = str(get_config_path().parent.parent)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        
    from src.data import load_kline
    
    qlib_dir = Path(get_qlib_dir())
    qlib_dir.mkdir(parents=True, exist_ok=True)
    
    valid_fields = set()
    
    with tempfile.TemporaryDirectory() as temp_csv_dir:
        temp_dir_path = Path(temp_csv_dir)
        valid_symbols_count = 0
        
        for symbol in symbols:
            try:
                df = load_kline(symbol, "daily")
                if df is not None and not df.empty:
                    df_qlib = format_df_for_qlib(symbol, df)
                    sz_sh_symbol = df_qlib['symbol'].iloc[0]
                    csv_path = temp_dir_path / f"{sz_sh_symbol}.csv"
                    df_qlib.to_csv(csv_path, index=False)
                    
                    for col in df_qlib.columns:
                        if col not in ['date', 'symbol']:
                            valid_fields.add(col)
                    valid_symbols_count += 1
            except Exception as e:
                print(f"[{symbol}] 数据加载失败: {e}")
                
        if valid_symbols_count == 0:
            print("没有有效的股票数据需要转换。")
            return
            
        fields_str = ",".join(list(valid_fields))
        
        try:
            print(f"正在构建由 {valid_symbols_count} 只股票组成的 QLib 数据库, 请稍候...")
            dumper = DumpDataAll(
                data_path=str(temp_dir_path),
                qlib_dir=str(qlib_dir),
                freq=freq,
                max_workers=4,
                include_fields=fields_str,
                exclude_fields="",
                symbol_field_name="symbol",
                date_field_name="date"
            )
            dumper.dump()
            print(f"==> 全部数据整理转换完成！已存入: {qlib_dir}")
        except Exception as e:
            print(f"执行 DumpDataAll 出现异常: {e}")

if __name__ == "__main__":
    dump_all_targets_to_unified_qlib('day')
