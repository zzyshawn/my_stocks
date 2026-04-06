"""
股票缠论分析脚本

功能：
1. 读取股票代码清单
2. 加载对应的股票日线数据
3. 执行缠论分析
4. 生成分析报告和图表
"""

import sys
import os
import yaml
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chanlun.core.analyzer import ChanLunAnalyzer
from chanlun.core.kline import KLine
from chanlun.visualization.pyecharts_plotter import PyechartsPlotter
from chanlun.utils.data_loader import DataLoader
from excel_export.export_to_excel import analyze_and_export_single_stock


def load_config(config_path=None):
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认为同目录下的config.yaml
        
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"成功加载配置文件: {config_path}")
        return config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None


def get_stock_list_path(config):
    """
    获取股票清单文件路径
    
    Args:
        config: 配置字典
        
    Returns:
        股票清单文件完整路径
    """
    watchlist_dir = config['data']['watchlist']['dir']
    watchlist_file = config['data']['watchlist']['file']
    return os.path.join(watchlist_dir, watchlist_file)


def get_code_column(config):
    """
    获取股票代码列名
    
    Args:
        config: 配置字典
        
    Returns:
        股票代码列名
    """
    return config['data']['watchlist'].get('code_column', '代码')


def get_data_dir(config):
    """
    获取数据目录
    
    Args:
        config: 配置字典
        
    Returns:
        数据目录路径
    """
    return config['data']['base_dir']


def get_kline_file_path(config, stock_code, period):
    """
    获取K线数据文件路径
    
    Args:
        config: 配置字典
        stock_code: 股票代码
        period: 周期 (daily/min30/min5)
        
    Returns:
        K线数据文件路径
    """
    base_dir = get_data_dir(config)
    pattern = config['naming']['files']['kline']['pattern']
    extension = config['naming']['files']['kline']['extension']
    period_map = config['naming']['files']['kline']['period_map']
    
    period_code = period_map.get(period, period)
    filename = pattern.format(symbol=stock_code, period=period_code) + extension
    
    return os.path.join(base_dir, stock_code, filename)


def get_analysis_file_path(config, stock_code, period, file_type='html'):
    """
    获取分析输出文件路径
    
    Args:
        config: 配置字典
        stock_code: 股票代码
        period: 周期代码 (d/30/5)
        file_type: 文件类型 (html/excel)
        
    Returns:
        分析文件路径
    """
    base_dir = get_data_dir(config)
    naming_config = config['naming']['files']['analysis']
    
    if file_type == 'html':
        pattern = naming_config['html_pattern']
        extension = naming_config['html_extension']
    else:
        pattern = naming_config['excel_pattern']
        extension = naming_config['excel_extension']
    
    filename = pattern.format(symbol=stock_code, period=period) + extension
    
    return os.path.join(base_dir, stock_code, filename)


def read_stock_list(file_path, code_column="代码"):
    """
    读取股票代码清单
    
    Args:
        file_path: Excel文件路径
        code_column: 股票代码列名
        
    Returns:
        股票代码列表（6位数字，补零）
    """
    try:
        df = pd.read_excel(file_path)

        # 显示文件结构
        print("Excel文件结构:")
        print(f"列名: {list(df.columns)}")
        print(f"行数: {len(df)}")

        # 使用指定的列名读取代码
        if code_column in df.columns:
            raw_codes = df[code_column].dropna().astype(str).tolist()
            
            stock_codes = []
            error_codes = []
            
            for code in raw_codes:
                code = code.strip()
                if code.isdigit() and 1 <= len(code) <= 6:
                    stock_codes.append(code.zfill(6))
                else:
                    error_codes.append(code)
            
            # 打印错误的代码到log
            if error_codes:
                print(f"[警告] 以下代码格式无效，已跳过: {error_codes}")
            
            print(f"在列 '{code_column}' 中找到 {len(stock_codes)} 个有效股票代码")
            print(f"前5个: {stock_codes[:5]}")
            
            return stock_codes
        else:
            print(f"[错误] 未找到列 '{code_column}'，可用列: {list(df.columns)}")
            return []
            
    except Exception as e:
        print(f"读取股票代码清单失败: {e}")
        return []


def load_stock_data(config, stock_code, data_type="d", max_records=None):
    """
    加载股票数据

    Args:
        config: 配置字典
        stock_code: 股票代码
        data_type: 数据类型（'d'=日线, '30'=30分钟, '5'=5分钟）
        max_records: 最大记录数限制

    Returns:
        K线数据列表
    """
    try:
        if max_records is None:
            max_records = config['analysis']['max_records']

        # 数据类型映射
        period_reverse_map = {'d': 'daily', '30': 'min30', '5': 'min5'}
        period_name = period_reverse_map.get(data_type, data_type)

        # 获取文件路径
        file_path = get_kline_file_path(config, stock_code, period_name)

        # 数据类型名称
        data_type_names = {"d": "日线", "30": "30分钟", "5": "5分钟"}
        data_type_name = data_type_names.get(data_type, data_type)

        if not os.path.exists(file_path):
            print(f"股票 {stock_code} 的{data_type_name}数据文件不存在: {file_path}")
            return []

        # 读取Excel文件
        df = pd.read_excel(file_path)

        # 显示文件结构
        print(f"股票 {stock_code} {data_type_name}数据文件结构:")
        print(f"列名: {list(df.columns)}")
        print(f"行数: {len(df)}")

        # 限制数据量
        if len(df) > max_records:
            print(f"数据量超过限制，只使用最后 {max_records} 条记录")
            df = df.tail(max_records)

        # 列名映射
        column_mapping = {
            'date': ['date', '日期', '时间', 'datetime', 'trade_date'],
            'open': ['open', '开盘', '开盘价', 'open_price'],
            'high': ['high', '最高', '最高价', 'high_price'],
            'low': ['low', '最低', '最低价', 'low_price'],
            'close': ['close', '收盘', '收盘价', 'close_price'],
            'volume': ['volume', '成交量', 'vol', 'amount']
        }

        # 尝试匹配列名
        matched_columns = {}
        for target_col, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    matched_columns[target_col] = name
                    break
            else:
                if target_col in ['volume']:
                    # 成交量是可选的
                    matched_columns[target_col] = None
                else:
                    print(f"股票 {stock_code} 的数据文件缺少必要列: {target_col}")
                    return []

        print(f"匹配的列名: {matched_columns}")

        # 转换为K线对象
        klines = []
        for _, row in df.iterrows():
            # 处理日期
            date_col = matched_columns['date']
            date_value = row[date_col]

            if isinstance(date_value, str):
                # 尝试不同的日期格式（包括分钟数据格式）
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y%m%d %H:%M:%S']:
                    try:
                        timestamp = datetime.strptime(date_value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
            elif isinstance(date_value, datetime):
                timestamp = date_value
            else:
                continue

            # 构建K线对象
            kline = KLine(
                timestamp=timestamp,
                open=float(row[matched_columns['open']]),
                high=float(row[matched_columns['high']]),
                low=float(row[matched_columns['low']]),
                close=float(row[matched_columns['close']]),
                volume=float(row.get(matched_columns['volume'], 0)) if matched_columns['volume'] else 0
            )
            klines.append(kline)

        # 按时间排序
        klines.sort(key=lambda x: x.timestamp)

        print(f"成功加载股票 {stock_code} 的{data_type_name}数据，共 {len(klines)} 条记录")
        return klines

    except Exception as e:
        print(f"加载股票 {stock_code} 的{data_type_name}数据失败: {e}")
        return []


def convert_dataframe_to_klines(df: pd.DataFrame, stock_code: str = "") -> list:
    """
    将 DataFrame 转换为 KLine 对象列表

    Args:
        df: 包含K线数据的DataFrame
        stock_code: 股票代码（用于日志）

    Returns:
        KLine 对象列表
    """
    column_mapping = {
        'date': ['date', '日期', '时间', 'datetime', 'trade_date'],
        'open': ['open', '开盘', '开盘价', 'open_price'],
        'high': ['high', '最高', '最高价', 'high_price'],
        'low': ['low', '最低', '最低价', 'low_price'],
        'close': ['close', '收盘', '收盘价', 'close_price'],
        'volume': ['volume', '成交量', 'vol', 'amount']
    }

    matched_columns = {}
    for target_col, possible_names in column_mapping.items():
        for name in possible_names:
            if name in df.columns:
                matched_columns[target_col] = name
                break
        else:
            if target_col in ['volume']:
                matched_columns[target_col] = None
            else:
                print(f"数据缺少必要列: {target_col}")
                return []

    klines = []
    for _, row in df.iterrows():
        date_col = matched_columns['date']
        date_value = row[date_col]

        if isinstance(date_value, str):
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y%m%d %H:%M:%S']:
                try:
                    timestamp = datetime.strptime(date_value, fmt)
                    break
                except ValueError:
                    continue
            else:
                continue
        elif isinstance(date_value, datetime):
            timestamp = date_value
        else:
            continue

        kline = KLine(
            timestamp=timestamp,
            open=float(row[matched_columns['open']]),
            high=float(row[matched_columns['high']]),
            low=float(row[matched_columns['low']]),
            close=float(row[matched_columns['close']]),
            volume=float(row.get(matched_columns['volume'], 0)) if matched_columns['volume'] else 0
        )
        klines.append(kline)

    klines.sort(key=lambda x: x.timestamp)
    return klines


def analyze_stock(config, stock_code, klines, data_type="d", enable_html=True):
    """
    分析单只股票

    Args:
        config: 配置字典
        stock_code: 股票代码
        klines: K线数据
        data_type: 数据类型（'d'=日线, '30'=30分钟, '5'=5分钟）
        enable_html: 是否生成HTML图表

    Returns:
        分析结果
    """
    analysis_config = config.get('analysis', {}) if config else {}
    min_klines = analysis_config.get('min_klines', 10)
    if len(klines) < min_klines:
        print(f"股票 {stock_code} 的数据不足（需要至少{min_klines}条），无法进行分析")
        return None

    try:
        data_type_names = {"d": "日线", "30": "30分钟", "5": "5分钟"}
        data_type_name = data_type_names.get(data_type, data_type)

        analyzer = ChanLunAnalyzer()
        result = analyzer.analyze(klines)
        trend_strength = analyzer.get_trend_strength(result)

        print(f"\n股票 {stock_code} {data_type_name}分析结果:")
        print(f"- 识别到 {len(result['pen_series'])} 个笔")
        print(f"- 识别到 {len(result['segment_series'])} 个线段")
        print(f"- 识别到 {len(result['pivot_series'])} 个中枢")
        print(f"- 上升趋势强度: {trend_strength['up_trend']:.2%}")
        print(f"- 下降趋势强度: {trend_strength['down_trend']:.2%}")
        print(f"- 震荡强度: {trend_strength['consolidation']:.2%}")

        result['stock_code'] = stock_code
        result['stock_name'] = "股票"

        if enable_html and config:
            chart_filename = get_analysis_file_path(config, stock_code, data_type, 'html')
            plotter = PyechartsPlotter()
            plotter.plot_analysis_chart(result, output_file=chart_filename)
            print(f"- 图表已保存为: {chart_filename}")

        if config:
            excel_output_dir = os.path.dirname(get_analysis_file_path(config, stock_code, data_type, 'excel'))
            analyze_and_export_single_stock(stock_code, klines, excel_output_dir, data_type=data_type)

        return result

    except Exception as e:
        print(f"分析股票 {stock_code} 失败: {e}")
        return None


def main():
    """
    主函数
    """
    print("=== 股票缠论分析开始 ===")

    # 加载配置
    config = load_config()
    if config is None:
        print("无法加载配置文件，程序退出")
        return

    # 获取路径配置
    stock_list_path = get_stock_list_path(config)
    code_column = get_code_column(config)

    # 读取股票代码清单
    stock_codes = read_stock_list(stock_list_path, code_column)

    if not stock_codes:
        print("没有股票代码可分析")
        return

    # 获取分析配置
    data_types = config['analysis']['data_types']
    stock_limit = config['analysis']['stock_limit']

    # 限制分析数量
    if stock_limit > 0:
        stock_codes = stock_codes[:stock_limit]

    # 分析每只股票的不同时间周期
    results = {}

    for stock_code in stock_codes:
        for data_type in data_types:
            data_type_names = {"d": "日线", "30": "30分钟", "5": "5分钟"}
            data_type_name = data_type_names.get(data_type, data_type)
            print(f"\n=== 分析股票: {stock_code} ({data_type_name}数据) ===")

            klines = load_stock_data(config, stock_code, data_type=data_type)
            if klines:
                result = analyze_stock(config, stock_code, klines, data_type=data_type)
                if result:
                    results[f"{stock_code}_{data_type}"] = result

    print("\n=== 分析完成 ===")
    print(f"成功分析 {len(results)} 个数据周期")


if __name__ == "__main__":
    main()
