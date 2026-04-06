import time
import os
import sys
import datetime

# 支持直接运行和作为模块导入
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

#A股票行情数据获取演示   https://github.com/mpquant/Ashare
from  Ashare import *

from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import concurrent.futures

# 使用项目通信模块发送飞书消息
from src.communication import send_feishu_text
# 使用项目配置模块
from src.utils.config import get_config

def should_execute():
    """检查当前时间是否应该执行任务"""
    now = datetime.datetime.now()
    current_time = now.time()
    return True
    # 检查是否在11:30-13:00之间
    if datetime.time(11, 30) < current_time < datetime.time(13, 0):
        return False
    
    # 检查是否在15:00之后
    if current_time > datetime.time(15, 5):
        return False
    
    return True
def create_directory(path):
    """
    给定一个文件夹路径，如果不存在则逐级创建文件夹
    
    参数:
        path (str): 要创建的文件夹路径
        
    返回:
        bool: 创建成功返回True，失败返回False
    """
    try:
        # 规范化路径，处理不同操作系统的路径分隔符
        normalized_path = os.path.normpath(path)
        
        # 如果路径已经存在，直接返回成功
        if os.path.exists(normalized_path):
            if os.path.isdir(normalized_path):
                #print(f"文件夹已存在: {normalized_path}")
                return True
            else:
                print(f"路径存在但不是文件夹: {normalized_path}")
                return False
        
        # 逐级创建文件夹
        os.makedirs(normalized_path, exist_ok=True)
        print(f"成功创建文件夹: {normalized_path}")
        return True
        
    except Exception as e:
        print(f"创建文件夹失败: {path}, 错误: {e}")
        return False
def get_exchange_all(stock_code):
    if stock_code.startswith('6'):
        return 'sh'+stock_code
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        return 'sz'+stock_code
    elif stock_code.startswith('8') or stock_code.startswith('9') or stock_code.startswith('4'):
        return 'bj'+stock_code
    else:
        return '未知'
    
# [未使用] 时间列表 - 从09:35开始
time_list = [
    "09:35", "09:40", "09:45", "09:50", "09:55",
    "10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40", "10:45", "10:50", "10:55",
    "11:00", "11:05", "11:10", "11:15", "11:20", "11:25", "11:30",
    "13:05", "13:10", "13:15", "13:20", "13:25", "13:30", "13:35", "13:40", "13:45", "13:50", "13:55",
    "14:00", "14:05", "14:10", "14:15", "14:20", "14:25", "14:30", "14:35", "14:40", "14:45", "14:50", "14:55",
    "15:00"
]
# 从09:36开始的时间列表
time_list_0936 = [
    "09:36", "09:41", "09:46", "09:51", "09:56",
    "10:01", "10:06", "10:11", "10:16", "10:21", "10:26", "10:31", "10:36", "10:41", "10:46", "10:51", "10:56",
    "11:01", "11:06", "11:11", "11:16", "11:21", "11:26", "11:31",
    "13:06", "13:11", "13:16", "13:21", "13:26", "13:31", "13:36", "13:41", "13:46", "13:51", "13:56",
    "14:01", "14:06", "14:11", "14:16", "14:21", "14:26", "14:31", "14:36", "14:41", "14:46", "14:51", "14:56",
    "15:01"
]


def generate_debug_time_list(count: int = 5) -> list:
    """
    生成调试用时间列表，从当前时间开始，间隔1分钟

    Args:
        count: 生成的时间点数量，默认5个

    Returns:
        时间字符串列表，格式为 "HH:MM"
    """
    now = datetime.datetime.now()
    time_list = []
    for i in range(count):
        next_time = now + datetime.timedelta(minutes=i)
        time_list.append(next_time.strftime("%H:%M"))
    return time_list

def get_seconds_to_next_time(now,time_list):
    """
    计算当前时间距离时间列表中下一个时间点相差的秒数
    
    Args:
        time_list: 时间字符串列表，格式为 "HH:MM"
    
    Returns:
        int: 距离下一个时间点的秒数，如果今天没有下一个时间点则返回None
    """
    # 获取当前时间
#    now = datetime.datetime.now()
    current_time = now.time()
    
    # 将字符串时间转换为datetime.time对象
    time_objects = []
    for time_str in time_list:
        hour, minute = map(int, time_str.split(':'))
        time_objects.append(datetime.time(hour, minute))
    
    # 找到下一个时间点
    for time_obj in time_objects:
        if time_obj > current_time:
            # 创建今天的日期时间对象
            next_datetime = datetime.datetime.combine(now.date(), time_obj)
            # 计算时间差（秒数）
            time_diff = next_datetime - now
            return int(time_diff.total_seconds())
    
    # 如果今天没有下一个时间点，返回None
    return 60

# [未使用] 单股实时数据获取测试
def main_single():
    position = 0
    while True:
        while True:
            # 检查当前时间是否在列表中
            current_time = datetime.datetime.now().strftime("%H:%M")
            if current_time in time_list_0936:
                position = time_list_0936.index(current_time)
                print(f"\n当前时间 {current_time} 在时间列表中")
                break
            else:
                time.sleep(30)#加快

        if should_execute():
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] 执行任务")
            df_5=get_price('sh600370',frequency='5m',count=position+2)     #分钟线行情，只支持从当前时间往前推，可用'1m','5m','15m','30m','60m'
            print('贵州茅台5分钟线\n',df_5)
            df_5.to_excel("H:/股票信息/股票数据库/daban/股票数据/600370/realtime/"+"600370_5_rt_"+current_time+".xlsx") 
            time_str = current_time +" : OK"
            send_feishu_text(time_str)
            time.sleep(60)
        # 等待5分钟

def thred_worker_get_realtime(code_id, thread_id, position, base_dir):
    """获取单股实时数据的工作线程"""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_time_filename = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")

    df_5 = get_price(get_exchange_all(code_id), frequency='5m', count=position+2)
    if df_5.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"

    # 拼接存储路径
    path = os.path.join(base_dir, code_id, "realtime")
    create_directory(path)

    # 列名映射：转为中文列名（与 history 模块格式一致）
    column_mapping = {
        'open': '开盘',
        'close': '收盘',
        'high': '最高',
        'low': '最低',
        'volume': '成交量'
    }
    df_5.index.name = '日期'  # 先设置索引名
    df_5 = df_5.reset_index().rename(columns=column_mapping)
    df_5['股票代码'] = code_id
    df_5['日期'] = pd.to_datetime(df_5['日期']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df_5.to_excel(os.path.join(path, f"{code_id}_rt_5_{position}_{current_time_filename}.xlsx"), index=False)

    # 30分钟线
    df_30 = get_price(get_exchange_all(code_id), frequency='30m', count=int(position/6)+1)
    if df_30.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"
    df_30.index.name = '日期'
    df_30 = df_30.reset_index().rename(columns=column_mapping)
    df_30['股票代码'] = code_id
    df_30['日期'] = pd.to_datetime(df_30['日期']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df_30.to_excel(os.path.join(path, f"{code_id}_rt_30_{position}_{current_time_filename}.xlsx"), index=False)

    # 日线
    df_d = get_price(get_exchange_all(code_id), frequency='1d', count=2)
    if df_d.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"
    df_d.index.name = '日期'
    df_d = df_d.reset_index().rename(columns=column_mapping)
    df_d['股票代码'] = code_id
    df_d['日期'] = pd.to_datetime(df_d['日期']).dt.strftime('%Y-%m-%d')
    df_d.to_excel(os.path.join(path, f"{code_id}_rt_d_{position}_{current_time_filename}.xlsx"), index=False)

    return f"1 {code_id}线程 {thread_id} 完成"

def main_mutl():
    """多股实时数据获取主函数"""
    position = 0
    print('实时获取开始')

    # 从配置文件读取配置
    config = get_config()

    # 股票列表配置
    target_dir = config.get("realtime.target_list.dir")
    target_file = config.get("realtime.target_list.file")
    code_column_name = config.get("realtime.target_list.code_column")

    if not target_dir or not target_file:
        raise ValueError("配置文件中缺少 realtime.target_list 配置项")

    # 数据存储基础目录
    base_dir = config.get("data.base_dir")
    if not base_dir:
        raise ValueError("配置文件中缺少 data.base_dir 配置项")

    file_path = os.path.join(target_dir, target_file)
    print(f"读取股票列表: {file_path}")
    print(f"数据存储目录: {base_dir}")

    df = pd.read_excel(file_path, dtype={code_column_name: str})
    code_column = df[code_column_name]
    print(f"监控股票数量: {len(code_column)}")
    print(f"股票代码列表: {code_column.tolist()}")
    
    while True:
        #current_time = datetime.datetime.now().strftime("%H:%M")
        while True:
            current_time = datetime.datetime.now().strftime("%H:%M")
            if current_time in time_list_0936:
                position = time_list_0936.index(current_time)
                print(f"\n当前时间 {current_time} 在时间列表中 (位置: {position})")
                break
            else:
                now = datetime.datetime.now()
                sleep_time = get_seconds_to_next_time(now, time_list_0936)
                min_sleep = min(sleep_time, 50)
                print(f"2.等待 {min_sleep} 秒...")
                time.sleep(min_sleep + 1)

        if should_execute():
            test1 = datetime.datetime.now()

            # 使用线程池并行处理所有代码
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(thred_worker_get_realtime, code_value, str(index), position, base_dir)
                    for index, code_value in code_column.items()
                ]
                results = []
                completed_count = 0

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        completed_count += 1
                        print(f"\r进度: {result}#{completed_count}/{len(futures)} 完成", end='', flush=True)
                    except Exception as e:
                        print(f"处理代码时出错: {e}")

            print("\nOK - 所有代码处理完成！")
            print(f"共处理 {len(results)} 个代码")

            use_time = datetime.datetime.now() - test1
            current_time_str = datetime.datetime.now().strftime("%H:%M:%S")
            time_str = f"{current_time_str}耗时：{int(use_time.total_seconds())}秒，共处理 {len(results)} 个代码"
            send_feishu_text(time_str)
            print(f"1.等待 60 秒...")
            time.sleep(60)


def debug_mutl(count: int = 5):
    """调试模式：多股实时数据获取，从当前时间开始间隔1分钟执行"""
    position = 0
    print('调试模式 - 实时获取开始')

    # 生成调试时间列表
    debug_time_list = generate_debug_time_list(count)
    print(f"调试时间列表: {debug_time_list}")

    # 从配置文件读取配置
    config = get_config()

    # 股票列表配置
    target_dir = config.get("realtime.target_list.dir")
    target_file = config.get("realtime.target_list.file")
    code_column_name = config.get("realtime.target_list.code_column")

    if not target_dir or not target_file:
        raise ValueError("配置文件中缺少 realtime.target_list 配置项")

    # 数据存储基础目录
    base_dir = config.get("data.base_dir")
    if not base_dir:
        raise ValueError("配置文件中缺少 data.base_dir 配置项")

    file_path = os.path.join(target_dir, target_file)
    print(f"读取股票列表: {file_path}")
    print(f"数据存储目录: {base_dir}")

    df = pd.read_excel(file_path, dtype={code_column_name: str})
    code_column = df[code_column_name]
    print(f"监控股票数量: {len(code_column)}")
    print(f"股票代码列表: {code_column.tolist()}")

    while True:
        current_time = datetime.datetime.now().strftime("%H:%M")

        if current_time in debug_time_list:
            position = debug_time_list.index(current_time)
            print(f"\n当前时间 {current_time} 在调试时间列表中 (位置: {position})")
            break
        else:
            now = datetime.datetime.now()
            sleep_time = get_seconds_to_next_time(now, debug_time_list)
            min_sleep = min(sleep_time, 30)
            print(f"等待 {min_sleep} 秒...")
            time.sleep(min_sleep + 1)

        # 检查是否已执行完所有时间点
        if position >= count - 1:
            print("调试完成，退出")
            break

    if should_execute():
        test1 = datetime.datetime.now()
        position = debug_time_list.index(current_time)

        # 使用线程池并行处理所有代码
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(thred_worker_get_realtime, code_value, str(index), position, base_dir)
                for index, code_value in code_column.items()
            ]
            results = []
            completed_count = 0

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    print(f"\r进度: {result}#{completed_count}/{len(futures)} 完成", end='', flush=True)
                except Exception as e:
                    print(f"处理代码时出错: {e}")

        print("\nOK - 所有代码处理完成！")
        print(f"共处理 {len(results)} 个代码")

        use_time = datetime.datetime.now() - test1
        current_time_str = datetime.datetime.now().strftime("%H:%M:%S")
        time_str = f"[调试] {current_time_str}耗时：{int(use_time.total_seconds())}秒，共处理 {len(results)} 个代码"
        send_feishu_text(time_str)

        time.sleep(60)

# [未使用] 获取单股5分钟K线数据
def get_real_5(my_code):
    position = 8
    while True:
        # 检查当前时间是否在列表中
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time in time_list_0936:
            position = time_list_0936.index(current_time)
            print(f"\n当前时间 {current_time} 在时间列表中")
            break
        else:
            time.sleep(60)#加快

    if should_execute():
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 执行任务")
        df_5=get_price(my_code ,frequency='5m',count=position+1)     #分钟线行情，只支持从当前时间往前推，可用'1m','5m','15m','30m','60m'
        print('贵州茅台5分钟线\n',df_5)
        return  df_5   


    return 

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="实时数据获取")
    parser.add_argument("--debug", action="store_true", help="调试模式，从当前时间开始间隔1分钟执行")
    parser.add_argument("--count", type=int, default=5, help="调试模式下执行次数，默认5次")

    args = parser.parse_args()

    if args.debug:
        print("运行调试模式")
        debug_mutl(args.count)
    else:
        print("运行正常模式")
        main_mutl()