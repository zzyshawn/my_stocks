import time
import os
import datetime
import requests
#A股票行情数据获取演示   https://github.com/mpquant/Ashare
from  Ashare import *

from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import concurrent.futures

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
            data2 = {
                'payload': '{"text": "%s"}' % time_str
                    }
            response = requests.post("http://192.168.0.100:5000/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=%22tX6wFhuo7WWzAvFS7wLE30Q07qKnzmQDPavpPkUuPY76vnfI3Lt0gDjGaW8AJnYl%22", data=data2)
            print(response.content)
            time.sleep(60)
        # 等待5分钟

def thred_worker_get_realtime(code_id,thread_id,position):
#    print(f"线程 {thread_id} 执行")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_time_filename = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
#    print(f"[{current_time}] 线程 {thread_id} 执行任务")
    
    df_5=get_price(get_exchange_all(code_id),frequency='5m',count=position+2)     #分钟线行情，只支持从当前时间往前推，可用'1m','5m','15m','30m','60m'
    if df_5.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"
    #print(f"[{current_time}]{code_id}5分钟线\n",df_5)
    path = f"H:/股票信息/股票数据库/daban/股票数据/{code_id}/realtime/"
    create_directory(path)
    df_5 = df_5.reset_index().rename(columns={'index': 'date'})
    df_5.to_excel(f"H:/股票信息/股票数据库/daban/股票数据/{code_id}/realtime/{code_id}_rt_5_{position}_{current_time_filename}.xlsx"  ,index=False) 
# 30 也实时获取 需要看高频影响
    df_30=get_price(get_exchange_all(code_id),frequency='30m',count=int(position/6)+1)     #分钟线行情，只支持从当前时间往前推，可用'1m','5m','15m','30m','60m'
    if df_30.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"
    df_30 = df_30.reset_index().rename(columns={'index': 'date'})
    df_30.to_excel(f"H:/股票信息/股票数据库/daban/股票数据/{code_id}/realtime/{code_id}_rt_30_{position}_{current_time_filename}.xlsx"  ,index=False) 

# 日也实时获取 需要看高频影响
    df_d=get_price(get_exchange_all(code_id),frequency='1d',count=2)     #分钟线行情，只支持从当前时间往前推，可用'1m','5m','15m','30m','60m'
    if df_d.empty:
        time.sleep(1)
        return f"0 {code_id} 线程 {thread_id} 失败"
    df_d = df_d.reset_index().rename(columns={'index': 'date'})
    df_d.to_excel(f"H:/股票信息/股票数据库/daban/股票数据/{code_id}/realtime/{code_id}_rt_d_{position}_{current_time_filename}.xlsx"  ,index=False) 

#    time_str = current_time +" : OK" 
#    data2 = {
#        'payload': '{"text": "%s"}' % time_str
#            }
#    response = requests.post("http://192.168.0.100:5000/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=%22tX6wFhuo7WWzAvFS7wLE30Q07qKnzmQDPavpPkUuPY76vnfI3Lt0gDjGaW8AJnYl%22", data=data2)
#    print(response.content)
#    time.sleep(1)
    return f"1 {code_id}线程 {thread_id} 完成"

def main_mutl():
    position = 0
    print('实时获取开始')
    # 读取Excel文件
    file_path = "data.xlsx"  # 替换为你的文件路径
    df = pd.read_excel(file_path,dtype={"代码": str})
    code_column = df["代码"]
#    for index, code_value in code_column.items():
#        print(f"{index} {code_value}")
#    print(f"代码列数据: {code_column.tolist()}")
    while True:
                    # 检查当前时间是否在列表中
        current_time = datetime.datetime.now().strftime("%H:%M")
#        simulate_time = "10:20"
#        sim_hour, sim_minute = map(int, simulate_time.split(':'))
#        now = datetime.datetime.now().replace(hour=sim_hour, minute=sim_minute, second=49, microsecond=0)

#        print(get_seconds_to_next_time(now,time_list_0936))
        while True:
            current_time = datetime.datetime.now().strftime("%H:%M")
            if current_time in time_list_0936:
                position = time_list_0936.index(current_time)
                print(f"\n当前时间 {current_time} 在时间列表中")
                break
            else:
                now = datetime.datetime.now()
                sleep_time = get_seconds_to_next_time(now,time_list_0936)
                min_sleep = min(sleep_time,30)
                time.sleep(min_sleep+3)#加快

#            """           
        if should_execute():
            test1 = datetime.datetime.now()
            position = time_list_0936.index(current_time)
#            position = 0
            # 使用线程池并行处理所有代码
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # 提交所有任务
                futures = [
                    executor.submit(thred_worker_get_realtime, code_value, str(index),position) 
                    for index, code_value in code_column.items()
                ]
                # 等待所有任务完成并收集结果
                results = []
                completed_count = 0
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        completed_count += 1
                        print(f"\r进度: {result}#{completed_count}/{len(futures)} 完成",end='', flush=True)
                    except Exception as e:
                        print(f"处理代码时出错: {e}")
            
            print("\nOK - 所有代码处理完成！")
            print(f"共处理 {len(results)} 个代码")
#            """
            use_time = datetime.datetime.now() - test1
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            time_str = f"{current_time}耗时： "+str(int(use_time.total_seconds())) +"秒 : "+ f"共处理 {len(results)} 个代码"
            data2 = {
                'payload': '{"text": "%s"}' % time_str
                    }
            response = requests.post("http://192.168.0.100:5000/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=%22tX6wFhuo7WWzAvFS7wLE30Q07qKnzmQDPavpPkUuPY76vnfI3Lt0gDjGaW8AJnYl%22", data=data2)
            print(response.content)
    
            time.sleep(60)

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
#    main()
    main_mutl()