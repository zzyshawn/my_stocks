import akshare as ak
import pandas as pd
from my_fun import mkdir
from my_fun import mkdir
import re
import os
import time
from my_daban_globals import set_jin_ri,get_jin_ri,set_zt_list,get_zt_list,my_zhangting_date1
from my_ta_fun import ta_canshu ,ta_fenshi
from test_my_proxy import ProxyTester
from my_get_proxy import get_and_save_fast_proxies
import requests
import urllib3
import socket
import random
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import datetime

import baostock as bs
from get_baostock import *

user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; …) Gecko/20100101 Firefox/61.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
]

def allowed_gai_family():
    return socket.AF_INET

my_home_disk_path = 'H:/股票信息/股票数据库/daban'
my_base_path = my_home_disk_path

gainiang_path = my_base_path + "//概念成分清单.xlsx"
gainiang_path_H = my_base_path + "//概念成分清单_合并.xlsx"
zhangting_path_H = my_base_path + "//涨停分析.xlsx"
gp_check_base_H = 'H:/股票信息/监控清单'

zt_path = my_base_path + "//涨停数据"
gn_path = zt_path +"//概念数据"
gp_path = my_base_path + "//股票数据"



del_gainiang = ['昨日涨停','昨日连板','昨日涨停_含一字','昨日连板_含一字','昨日触板','ST股','B股','创业板综','次新股','QFII重仓','深成500','中证500','AB股','上证380','深证100R','上证180_','上证50_','AH股','上证50_','AH股','百元股','融资融券','预亏预减','深股通','国企改革','富时罗素','预盈预增','标准普尔','沪股通','机构重仓','低价股','微盘股','长江三角','西部大开发']
gp_data= {}
gp_data_30= {}
gp_data_5= {}
my_zhangting_date = []
my_end_date = '20251231'
my_end_date2 = '2026-12-31'

proxies_g = {
        "http": "http://your_proxy:port",
        "https": "https://your_proxy:port",
    }

def file_to_dict_with_line_number(filename):
    """
    将文件每行读取到字典，行号作为键
    """
    result_dict = {}
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                result_dict[line_num] = line.strip()
        return result_dict
    except FileNotFoundError:
        print(f"错误: 文件 {filename} 不存在")
        return {}
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return {}


def get_zt_list_day(my_today):
    zt_list_day = get_zt_list()
    new_pos = zt_list_day.index(my_today)
    list_len = len(zt_list_day)
    return zt_list_day,new_pos,list_len


def setup_akshare_with_proxy(proxy_config=None):
    """
    设置AKShare使用代理
    
    Args:
        proxy_config: 代理配置字典
            {
                "http": "http://user:pass@ip:port",
                "https": "https://user:pass@ip:port"
            }
    """
    if proxy_config:
        session = requests.Session()
        session.proxies.update(proxy_config)
        ak.session = session
        print("代理设置成功")
    else:
        print("使用直连方式")

def test_proxy(proxies):
    # 设置代理
#    proxies = {
#        "http": "http://your_proxy:port",
#        "https": "https://your_proxy:port",
#    }
    
    # 测试代理连接
    try:
        test_session = requests.Session()
        print(proxies)
        test_session.proxies.update(proxies)
        response = test_session.get("http://httpbin.org/delay/1", timeout=5)
        print("代理IP:", response.json())
        response = requests.get(
                    "http://httpbin.org/delay/1", 
                    proxies=proxies, 
                    timeout=5,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
        print("代理IP:", response.json())
    except Exception as e:
        print(f"代理测试失败: {e}")
        return False
    
    # 使用代理调用AKShare
    ak_session = requests.Session()
#    ak_session.proxies.update(proxies)
    ak.session = ak_session
    
    try:
        data = ak.stock_zh_a_spot()
        print(f"成功获取数据: {len(data)} 条记录")
        return True
    except Exception as e:
        print(f"AKShare调用失败: {e}")
        return False

def get_exchange(stock_code):
    if stock_code.startswith('6'):
        return 'sh'
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        return 'sz'
    elif stock_code.startswith('8') or stock_code.startswith('9') or stock_code.startswith('4'):
        return 'bj'
    else:
        return '未知'

def get_gp_data_min(my_code,my_today,mins):
    print(f'min{mins}线')
    out_path = my_base_path + "//股票数据//" +  my_code
    gp_path = out_path+"//" + my_code+"min"+mins+".xlsx"
    mkdir(out_path)
    stock_zh_a_hist_df = ''
    last_date = ''
    gp_old_df_OUT = ''
    gp_old_df_tmp = pd.DataFrame()
    my_year = my_today[:4]
    my_month = my_today[4:6]
    my_day = my_today[6:8]
    start_date_1 = "2025-01-01 09:30:00"
#    urllib3.util.connection.allowed_gai_family = allowed_gai_family
    session = requests.Session()
#    session.proxies.update(proxies_g)
    session.headers.update({'User-Agent': random.choice(user_agent_list)})
    ak.session = session
#    ak.set_option('request_interval', 0.5)
    
    # 检查文件是否存在
    if os.path.exists(gp_path):
        gp_old_df = pd.read_excel(gp_path)#,usecols='A:L',dtype={'股票代码':str})
#        my_name = gp_list1.loc[gp_list1['代码'] == my_code, '名称']
#        gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
#        gp_old_df['日期_D'] = gp_old_df['时间'].dt.date
#        gp_old_df['日期_D'] = gp_old_df['日期_D'].strftime('%Y%m%d')
#        gp_old_df['日期_D'] = pd.to_datetime(gp_old_df['时间'], format='%Y%m%d')
        gp_old_df_tmp['时间'] = pd.to_datetime(gp_old_df['时间'])
#        gp_old_df['日期_D'] = gp_old_df_tmp['时间'].dt.date.astype(str)
#        gp_old_df['日期_D'] = gp_old_df['日期_D'].str.replace(r'-', '', regex=True)
        last_time = gp_old_df_tmp['时间'].iloc[-1]
        last_time_str = last_time.strftime('%Y-%m-%d %H:%M:%S')
        start_time_str = last_time.strftime('%Y-%m-%d')
#        print(gp_old_df['日期_D'])
#        gp_list1.loc[gp_list1['代码'] == my_code, my_today]
#        gp_old_df_OUT =  gp_old_df.loc[gp_old_df['日期_D'] == my_today]
        my_today_str = my_today[:4] +'-'+ my_today[4:6] +'-'+ my_today[6:8]+" 15:00:00"
#        new_format+" 15:00:00"
        if last_time_str != my_today_str:
#            new_format = my_today[:4] +'-'+ my_today[4:6] +'-'+ my_today[6:8]
            gp_old_df_OUT = ak.stock_zh_a_hist_min_em(symbol=my_code, start_date=last_time_str, end_date=my_today_str, period=mins, adjust="qfq")
            if gp_old_df_OUT.size == 0:
                return gp_old_df_OUT
            else:
                gp_old_df = pd.concat([gp_old_df, gp_old_df_OUT], ignore_index=True)
                stock_zh_a_hist_df = gp_old_df.drop_duplicates(subset='时间')
        else:
            return gp_old_df_OUT
#        month_data = gp_old_df[gp_old_df['日期'].dt.day == 21]
#        month_data = month_data[month_data['日期'].dt.month == 11]
    else:
        new_format = my_today[:4] +'-'+ my_today[4:6] +'-'+ my_today[6:8]
        gp_old_df_OUT = ak.stock_zh_a_hist_min_em(symbol=my_code, start_date=start_date_1, end_date=new_format+" 15:00:00", period=mins, adjust="qfq")
        stock_zh_a_hist_df = gp_old_df_OUT
    
    stock_zh_a_hist_df.to_excel(gp_path , index=False)
    time.sleep(1)    
    return gp_old_df_OUT

def get_gp_data_bao_all(my_code,my_today):
    get_gp_data_bao(my_code,my_today,'d')
    get_gp_data_bao(my_code,my_today,'30')
#    print('tttttt\n')
    get_gp_data_bao(my_code,my_today,'5')
    return

def deal_data(stock_zh_a_hist_df,date_mins):
    # 重命名列
    column_mapping = {

        'date': '日期',
        'time': '日期',
        'code': '股票代码',
        'open': '开盘',
        'close': '收盘',
        'high': '最高',
        'low': '最低',
        'volume': '成交量',
        'amount': '成交额',
        'turn': '换手率',
                        
    }
    stock_zh_a_hist_df = stock_zh_a_hist_df.rename(columns=column_mapping)
    
    existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额',	'换手率']
    #print(stock_zh_a_hist_df.columns)
    if date_mins == 'd':
        #print(type(stock_zh_a_hist_df['日期'].iloc[-1]))
        stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期']).dt.strftime('%Y-%m-%d')
        existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额',	'换手率']
    else:
        #print(type(stock_zh_a_hist_df['日期'].iloc[-1]))
        #print(stock_zh_a_hist_df['日期'].str[:14])
        stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期'].str[:14]).dt.strftime('%Y-%m-%d %H:%M:%S')
        existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额']

    stock_zh_a_hist_df['开盘'] = pd.to_numeric(stock_zh_a_hist_df['开盘'],errors='coerce').round(2)
    stock_zh_a_hist_df['收盘'] = pd.to_numeric(stock_zh_a_hist_df['收盘'],errors='coerce').round(2)
    stock_zh_a_hist_df['最高'] = pd.to_numeric(stock_zh_a_hist_df['最高'],errors='coerce').round(2)
    stock_zh_a_hist_df['最低'] = pd.to_numeric(stock_zh_a_hist_df['最低'],errors='coerce').round(2)
    stock_zh_a_hist_df['成交量'] = pd.to_numeric(stock_zh_a_hist_df['成交量'],errors='coerce').round(2)
    stock_zh_a_hist_df['成交额'] = pd.to_numeric(stock_zh_a_hist_df['成交额'],errors='coerce').round(2)
    code_tmp = stock_zh_a_hist_df['股票代码'].iloc[-1]
    stock_zh_a_hist_df['股票代码'] = code_tmp[3:9]

    stock_zh_a_hist_df['股票代码'] = stock_zh_a_hist_df['股票代码'].str.zfill(6)
    stock_zh_a_hist_df = stock_zh_a_hist_df[existing_columns]
    return stock_zh_a_hist_df

def get_gp_data_bao(my_code,my_today,date_mins):
    print(f'历史 {date_mins} mins '+my_code)
     
#    bs_login(1)
    #0 读 1 拼接 2 纯
    already_read = 0
    out_path = my_base_path + "//股票数据//" +  my_code
    out_path_bi = out_path + "/biduan"
    out_path_bi_out = out_path_bi + "/out"
#    value_path = out_path+"//" + my_code+"_value.xlsx"
    gp_path = out_path+"//" + my_code+f"_{date_mins}.xlsx"
    gp_path_bi = out_path_bi+"//" + my_code+f"_{date_mins}.csv"
    mkdir(out_path)
    mkdir(out_path_bi)
    mkdir(out_path_bi_out)

    stock_zh_a_hist_df = ''
    last_date = ''
#    if my_code in gp_data:
#        stock_zh_a_hist_df = gp_data[my_code]
#        return stock_zh_a_hist_df
    # 检查文件是否存在
    if os.path.exists(gp_path):

        gp_old_df = pd.read_excel(gp_path,dtype={'股票代码':str})
        
        gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        #gp_old_df['日期'] = gp_old_df['日期'].dt.date
        last_date = pd.to_datetime(gp_old_df.iloc[-1,0],errors='coerce').strftime('%Y-%m-%d')
        if len(gp_old_df) < 60:
            last_date = '2024-01-01'

        if len(gp_old_df.columns) == 8 or len(gp_old_df.columns) == 9:
            if my_today != last_date:
    #            print("刷"+'today=' + my_today + "  last_dat=" + last_date)
                try:
    #                stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
                    stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
                    stock_zh_a_hist_df = deal_data(stock_zh_a_hist_df,date_mins)
                    already_read = 1

                except Exception as e:
                    print(f"数据获取失败1：{e}")
                    #time.sleep(1)
                    return stock_zh_a_hist_df

    #            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
    #            gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)
                
                gp_old_df = gp_old_df.iloc[:, :12]
                gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)

                stock_zh_a_hist_df = gp_old_df.drop_duplicates(subset='日期')
            else:
                print("不用刷"+'today=' + my_today + "  last_dat=" + last_date)
                stock_zh_a_hist_df = gp_old_df
#                stock_zh_a_hist_df['日期'] = stock_zh_a_hist_df['日期']
#                stock_zh_a_hist_df['日期'] = stock_zh_a_hist_df['日期'].apply(lambda x: re.sub(r'\D', '', str(x)) if pd.notna(x) else '')
                gp_data[my_code] = stock_zh_a_hist_df
                already_read = 2
        else:
                try:
    #                stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
                    last_date = '2024-01-01'
                    stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
                    already_read = 0
                    
                except Exception as e:
                    print(f"数据获取失败1：{e}")
                    #time.sleep(1)
                    return stock_zh_a_hist_df
        
    else:
        #last_date = my_today
        last_date = '2024-01-01'
#        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
        try:
#            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
            stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
            already_read = 0
        except Exception as e:
            print(f"数据获取失败2：{e}")
#            time.sleep(1)
            return stock_zh_a_hist_df
#        gp_data[my_code] = stock_zh_a_hist_df
    #    print(type(last_date))

    # 重命名列
    if already_read == 0:
        stock_zh_a_hist_df = deal_data(stock_zh_a_hist_df,date_mins)
    """    
    stock_zh_a_hist_df = stock_zh_a_hist_df.rename(columns=column_mapping)
    
    existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额',	'换手率']
    #print(stock_zh_a_hist_df.columns)
    if date_mins == 'd':
        #print(type(stock_zh_a_hist_df['日期'].iloc[-1]))
        stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期']).dt.strftime('%Y-%m-%d')
        existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额',	'换手率']
    else:
        #print(type(stock_zh_a_hist_df['日期'].iloc[-1]))
        #print(stock_zh_a_hist_df['日期'].str[:14])
        stock_zh_a_hist_df['日期'] = pd.to_datetime(stock_zh_a_hist_df['日期'].str[:14]).dt.strftime('%Y-%m-%d %H:%M:%S')
        existing_columns = ['日期',	'股票代码',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额']

    stock_zh_a_hist_df['开盘'] = pd.to_numeric(stock_zh_a_hist_df['开盘'],errors='coerce').round(2)
    stock_zh_a_hist_df['收盘'] = pd.to_numeric(stock_zh_a_hist_df['收盘'],errors='coerce').round(2)
    stock_zh_a_hist_df['最高'] = pd.to_numeric(stock_zh_a_hist_df['最高'],errors='coerce').round(2)
    stock_zh_a_hist_df['最低'] = pd.to_numeric(stock_zh_a_hist_df['最低'],errors='coerce').round(2)
    stock_zh_a_hist_df['成交量'] = pd.to_numeric(stock_zh_a_hist_df['成交量'],errors='coerce').round(2)
    stock_zh_a_hist_df['成交额'] = pd.to_numeric(stock_zh_a_hist_df['成交额'],errors='coerce').round(2)
    code_tmp = stock_zh_a_hist_df['股票代码'].iloc[-1]
    stock_zh_a_hist_df['股票代码'] = code_tmp[3:9]

    stock_zh_a_hist_df['股票代码'] = stock_zh_a_hist_df['股票代码'].str.zfill(6)
    """
    stock_zh_a_hist_df.to_excel(gp_path , index=False)
    if date_mins == 'd':
        existing_columns_cvs = ['日期',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额','换手率']
    else:
        existing_columns_cvs = ['日期',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额']
    df_selected = stock_zh_a_hist_df[existing_columns_cvs]
    df_selected.to_csv(gp_path_bi , index=False,encoding='gbk')    
#    stock_zh_a_hist_df.to_csv(gp_path_bi , index=False,encoding='utf-8')

    gp_data[my_code] = stock_zh_a_hist_df
    
#    print(gp_data[my_code])
#    bs_login(0)
    return stock_zh_a_hist_df


def get_gp_data(my_code,my_today):
    print('日线'+my_code)
#    print(proxies_g)
#    urllib3.util.connection.allowed_gai_family = allowed_gai_family
#    session = requests.Session()
#    session.proxies.update(proxies_g)
#    session.headers.update({'User-Agent': random.choice(user_agent_list)})
    
#    ak.session = session
#    ak.set_option('request_interval', 0.5)
#    print(ak.session)
#    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date='20241231', adjust="qfq")
    out_path = my_base_path + "//股票数据//" +  my_code
    value_path = out_path+"//" + my_code+"_value.xlsx"
    gp_path = out_path+"//" + my_code+".xlsx"
    mkdir(out_path)
    stock_zh_a_hist_df = ''
    last_date = ''
    if my_code in gp_data:
        stock_zh_a_hist_df = gp_data[my_code]
        return stock_zh_a_hist_df
    # 检查文件是否存在
    elif os.path.exists(gp_path):
#        gp_old_df = pd.read_excel(gp_path,usecols='A:L',dtype={'股票代码':str})
        gp_old_df = pd.read_excel(gp_path,dtype={'股票代码':str})
#        my_name = gp_list1.loc[gp_list1['代码'] == my_code, '名称']
        gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        gp_old_df['日期'] = gp_old_df['日期'].dt.date
        last_date = gp_old_df.iloc[-1,0].strftime('%Y%m%d')
        if len(gp_old_df) < 60:
            last_date = '2024-01-01'
        if my_today != last_date:
#            print("刷"+'today=' + my_today + "  last_dat=" + last_date)
            try:
                stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
            except Exception as e:
                print(f"数据获取失败1：{e}")
                time.sleep(1)
                return stock_zh_a_hist_df

#            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
#            gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)
            gp_old_df = gp_old_df.iloc[:, :12]
            gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)

            stock_zh_a_hist_df = gp_old_df.drop_duplicates(subset='日期')
        else:
            print("不用刷"+'today=' + my_today + "  last_dat=" + last_date)
            stock_zh_a_hist_df = gp_old_df
            gp_data[my_code] = stock_zh_a_hist_df
        
    else:
        last_date = my_today
#        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
        try:
            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
        except Exception as e:
            print(f"数据获取失败2：{e}")
#            time.sleep(1)
            return stock_zh_a_hist_df
#        gp_data[my_code] = stock_zh_a_hist_df
    #    print(type(last_date))

    jys_code = get_exchange(my_code)
    print('资金'+my_code)

    if my_today == last_date:
        if os.path.exists(value_path):
            return gp_data[my_code]
        
    value_df = ak.stock_individual_fund_flow(stock=my_code, market=jys_code)

    # 检查文件是否存在
    if os.path.exists(value_path):
        value_old_df = pd.read_excel(value_path)
        value_old_df['日期'] = value_old_df['日期'].dt.date
#        value_old_df['日期'] = value_old_df['日期'].dt.strftime('%Y-%m-%d')
#        print(value_old_df['日期'])
#        print(value_df['日期'])
        out_df = pd.concat([value_old_df, value_df], ignore_index=True)

        value_df = out_df.drop_duplicates(subset='日期')
    

    value_df_tmp = value_df.drop(['收盘价', '涨跌幅'], axis=1)
    value_df_tmp.to_excel(value_path , index=False)
    stock_zh_a_hist_df = pd.merge(left=stock_zh_a_hist_df,         # 左表
                        right=value_df_tmp,        # 右表
                        left_on= '日期',  # 左表的连接字段
                        right_on= '日期',
                        how='left')             # how='left' 表示进行左连接

    stock_zh_a_hist_df.to_excel(out_path+"//" + my_code+".xlsx" , index=False)
    gp_data[my_code] = stock_zh_a_hist_df
    time.sleep(15)    
#    print(gp_data[my_code])
    return stock_zh_a_hist_df

def get_zt_base(base_path_H,out_path,date_tmp,gn):
    if os.path.exists(out_path+"//hy"+date_tmp+".xlsx"):
        print(date_tmp+"涨停已获取")
        data_leftmerge = pd.read_excel(out_path+"//hy"+date_tmp+".xlsx",dtype={'代码':str})
    else:
        stock_zt_pool_em_df = ak.stock_zt_pool_em(date=date_tmp)
        stock_zt_pool_em_df.rename(columns={"序号":"日期"},inplace = True)
        stock_zt_pool_em_df['日期'] = date_tmp

    #获取概念
        gainian_df = pd.read_excel(base_path_H,dtype={'代码':str})
    #    print(stock_zt_pool_em_df)
    #    print(gainian_df)
        data_leftmerge = pd.merge(left=stock_zt_pool_em_df,         # 左表
                                right=gainian_df[['代码','概念']],        # 右表
                                on='代码',  # 左表的连接字段
                                how='left')             # how='left' 表示进行左连接

        data_leftmerge.to_excel(out_path+"//hy"+date_tmp+".xlsx", index=False)

    return data_leftmerge



def get_zt(base_path_H,out_path,date_tmp,gn):
    print('涨停')

    if os.path.exists(out_path+"//hy"+date_tmp+".xlsx"):
        print(date_tmp+"涨停已获取")
        data_leftmerge = pd.read_excel(out_path+"//hy"+date_tmp+".xlsx",dtype={'代码':str})
    else:
        stock_zt_pool_em_df = ak.stock_zt_pool_em(date=date_tmp)
        stock_zt_pool_em_df.rename(columns={"序号":"日期"},inplace = True)
        stock_zt_pool_em_df['日期'] = date_tmp

    #获取概念
        gainian_df = pd.read_excel(base_path_H,dtype={'代码':str})
    #    print(stock_zt_pool_em_df)
    #    print(gainian_df)
        data_leftmerge = pd.merge(left=stock_zt_pool_em_df,         # 左表
                                right=gainian_df[['代码','概念']],        # 右表
                                on='代码',  # 左表的连接字段
                                how='left')             # how='left' 表示进行左连接

        data_leftmerge.to_excel(out_path+"//hy"+date_tmp+".xlsx", index=False)

#    stock_zt_pool_em_df.to_excel(out_path+"//hy"+date_tmp+".xlsx", index=False)
    total = len(data_leftmerge)
    if gn == 1:
        print('概念')
        #可能不能调太快
        gn_df = ak.stock_board_concept_name_em()
        gn_df = gn_df[~gn_df["板块名称"].isin(del_gainiang)]
        gn_df = gn_df.rename(columns={'排名': '日期'})
        gn_df['日期'] = date_tmp
        gn_df.to_excel(out_path+"//概念数据//gn"+date_tmp+".xlsx", index=False)


    i = 1
    for code in data_leftmerge['代码']:
        retry = 5
        
        while retry > 0 :
            print(f"total {i}/{total}")
            is_ok = get_gp_data(code,my_zhangting_date[-1])

            out_path = my_base_path + "//股票数据//" +  code
            canshu_path = out_path+"//" + code+"_canshu.xlsx"

            gp_df = ta_canshu(is_ok)
            gp_df.to_excel(canshu_path , index=False)
            retry = 0

        get_gp_data_min(code,my_zhangting_date[-1],"30")
        time.sleep(15)
        get_gp_data_min(code,my_zhangting_date[-1],"5")
        time.sleep(15)
        i = i + 1


    return
def get_work_date(days):

    """
    直接使用date列获取日期
    """
    # 获取沪指数据
    stock_data = ak.stock_zh_index_daily(symbol="sh000001")
    
    # 获取最后一个交易日（date列）
    last_trading_day = stock_data['date'].iloc[-1]
    
    last_trading_day_str = pd.to_datetime(last_trading_day).strftime('%Y%m%d')

    # 获取最后30个交易日（date列）
    last_30_days = stock_data.tail(days)['date']
    last_30_days_str = [pd.to_datetime(day).strftime('%Y%m%d') for day in last_30_days]
    
    return last_trading_day_str, last_30_days_str
def main():
    global my_zhangting_date

#    urllib3.util.connection.allowed_gai_family = allowed_gai_family
    #获取代理
#    proxies = get_and_save_fast_proxies('HTTP', 'fast_http_proxies.txt', 1000)
 #   https_proxies = get_and_save_fast_proxies('HTTPS', 'fast_https_proxies.txt', 1000)
    # 使用代理
#    http_dict = file_to_dict_with_line_number('fast_http_proxies.txt')
#    https_dict = file_to_dict_with_line_number('fast_https_proxies.txt')
#    print(http_dict)


#    proxies_g['http'] = http_dict[1]
#    proxies_g['https'] =https_dict[1]
#    print(type(proxies_g))
#    print(proxies_g)
#    test_proxy(proxies)
#    tester = ProxyTester()
#    proxies_to_test = [
#        'http://18.162.158.218:80',
        # 添加更多代理...
#    ]
#    results = tester.test_proxies_sequential(proxies_to_test, timeout=8)
    # 设置代理

    #session = requests.Session()
#    session.proxies.update(proxies_g)
    #sak.session = session

    my_today,my_zhangting_date = get_work_date(10)
    set_jin_ri(my_today)
    set_zt_list(my_zhangting_date)
#    date_tmp = get_jin_ri()

    my_zhangting_date2,pos,list_len= get_zt_list_day(my_today)

    my_zhangting_date = my_zhangting_date2

#

    get_zt(gainiang_path_H,zt_path,my_today,0)

    return 


def data_canshu(my_code):
    work_path = my_base_path + "/股票数据/" +  my_code
    base_path = work_path+"/" + my_code

    day_in_file = base_path + ".xlsx"
    day_out_file = base_path + "_canshu.xlsx"

    min30_in_file = base_path + "min30_tmp.xlsx"
    min30_out_file = base_path + "min30_canshu.xlsx"

    min5_in_file = base_path + "min5_tmp.xlsx"
    min5_out_file = base_path + "min5_canshu.xlsx"

    if os.path.exists(day_in_file):
        gp_old_df = pd.read_excel(day_in_file,dtype={'股票代码':str})
#            gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        gp_old_df['日期'] = gp_old_df['日期'].dt.date
#            last_date = gp_old_df.iloc[-1,0].strftime('%Y%m%d')    

        gp_df_day = ta_canshu(gp_old_df)
        gp_df_day.to_excel(day_out_file , index=False) 
    else:
        print(f"不存在：{day_in_file}")
    if os.path.exists(min30_in_file):
        gp_old_df = pd.read_excel(min30_in_file,dtype={'股票代码':str})
#            gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        gp_old_df.rename(columns={'时间': '日期'}, inplace=True)
#        gp_old_df['日期'] = gp_old_df['日期'].dt.date
#            last_date = gp_old_df.iloc[-1,0].strftime('%Y%m%d')    

        gp_df_30 = ta_canshu(gp_old_df)
        gp_df_30.to_excel(min30_out_file , index=False)   

    if os.path.exists(min5_in_file):
        gp_old_df = pd.read_excel(min5_in_file,dtype={'股票代码':str})
#            gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        gp_old_df.rename(columns={'时间': '日期'}, inplace=True)
#        gp_old_df['日期'] = gp_old_df['日期'].dt.date
#            last_date = gp_old_df.iloc[-1,0].strftime('%Y%m%d')    

        gp_df_5 = ta_canshu(gp_old_df)
        gp_df_5.to_excel(min5_out_file , index=False)  
    return gp_df_day , gp_df_30 , gp_df_5

#get_gp_data("600370","20251112")
#get_gp_data_min("600370","20251112","30")
#get_gp_data_min("600370","20251112","5")
#my_yfinance_get('002374')

def get_data_mutl(check_list , my_today):
    position = 0
    print('历史获取开始')

    code_column = check_list["代码"]
    bs_login(0)
    bs_login(1)
    while True:
 
            test1 = datetime.datetime.now()
            date_obj = datetime.datetime.strptime(my_today, '%Y%m%d')
            # 格式化为标准日期字符串
            my_today2 = date_obj.strftime('%Y-%m-%d')
            # 使用线程池并行处理所有代码
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # 提交所有任务
                #get_gp_data_bao(my_code,my_today,date_mins)
                futures = [
                    executor.submit(get_gp_data_bao_all, code_value, my_today2) 
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
                'payload': '{"text": "%s"}' %time_str
                    }
            response = requests.post("http://192.168.0.100:5000/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=%22tX6wFhuo7WWzAvFS7wLE30Q07qKnzmQDPavpPkUuPY76vnfI3Lt0gDjGaW8AJnYl%22", data=data2)
            print(response.content)
            bs_login(0)
            return

def get_base_data_his():
    global my_zhangting_date
    my_today,my_zhangting_date = get_work_date(10)
    set_jin_ri(my_today)
    set_zt_list(my_zhangting_date)

    my_zhangting_date2,pos,list_len= get_zt_list_day(my_today)

    my_zhangting_date = my_zhangting_date2

    columns_to_keep = ["日期", "代码", "名称"]  # 只保留这些列
    df = get_zt_base(gainiang_path_H,zt_path,my_today,0)
    
    # 只保留指定列
    df_filtered = df[columns_to_keep]

    if os.path.exists(gp_check_base_H +"//check_list.xlsx"):
        print("check list已获取")
        data_leftmerge = pd.read_excel(gp_check_base_H +"//check_list.xlsx",dtype={'代码':str})
        data_leftmerge = pd.concat([data_leftmerge, df_filtered], ignore_index=True)
        df_filtered = data_leftmerge.drop_duplicates(subset='代码')
        df_filtered.to_excel(gp_check_base_H +"//check_list.xlsx",index=False)
    else:
        df_filtered.to_excel(gp_check_base_H +"//check_list.xlsx",index=False)

#    get_data_mutl(df_filtered)
    return df_filtered , my_today



def make_excel_cvs(my_code,my_today,date_mins):
    
    already_read = 0
    out_path = my_base_path + "//股票数据//" +  my_code
    out_path_bi = out_path + "/biduan"
    out_path_bi_out = out_path_bi + "/out"
    gp_path = out_path+"//" + my_code+f"_{date_mins}.xlsx"
    gp_path_bi = out_path_bi+"//" + my_code+f"_{date_mins}.csv"
#    gp_path_bi_out = out_path_bi+"//" + my_code+f"_{date_mins}.xlsx"
    mkdir(out_path)
    mkdir(out_path_bi)
    mkdir(out_path_bi_out)
    stock_zh_a_hist_df = ''
    last_date = ''
#    if my_code in gp_data:
#        stock_zh_a_hist_df = gp_data[my_code]
#        return stock_zh_a_hist_df
    # 检查文件是否存在
    if os.path.exists(gp_path):

        gp_old_df = pd.read_excel(gp_path,dtype={'股票代码':str})
        
        gp_old_df['股票代码'] = gp_old_df['股票代码'].str.zfill(6)
        last_date = pd.to_datetime(gp_old_df.iloc[-1,0],errors='coerce').strftime('%Y-%m-%d')
        if len(gp_old_df) < 60:
            last_date = '2024-01-01'

        if len(gp_old_df.columns) == 8 or len(gp_old_df.columns) == 9:
            if my_today != last_date:
    #            print("刷"+'today=' + my_today + "  last_dat=" + last_date)
                try:
    #                stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
                    stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
                    stock_zh_a_hist_df = deal_data(stock_zh_a_hist_df,date_mins)
                    already_read = 1

                except Exception as e:
                    print(f"数据获取失败1：{e}")
                    #time.sleep(1)
                    return stock_zh_a_hist_df

    #            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
    #            gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)
                
                gp_old_df = gp_old_df.iloc[:, :12]
                gp_old_df = pd.concat([gp_old_df, stock_zh_a_hist_df], ignore_index=True)

                stock_zh_a_hist_df = gp_old_df.drop_duplicates(subset='日期')
            else:
                print("不用刷"+'today=' + my_today + "  last_dat=" + last_date)
                stock_zh_a_hist_df = gp_old_df
#                stock_zh_a_hist_df['日期'] = stock_zh_a_hist_df['日期']
#                stock_zh_a_hist_df['日期'] = stock_zh_a_hist_df['日期'].apply(lambda x: re.sub(r'\D', '', str(x)) if pd.notna(x) else '')
                gp_data[my_code] = stock_zh_a_hist_df
                already_read = 2
        else:
                try:
    #                stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date=last_date, end_date=my_end_date, adjust="qfq")
                    last_date = '2024-01-01'
                    stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
                    already_read = 0
                    
                except Exception as e:
                    print(f"数据获取失败1：{e}")
                    #time.sleep(1)
                    return stock_zh_a_hist_df
        
    else:
        #last_date = my_today
        last_date = '2024-01-01'
#        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
        try:
#            stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=my_code, period="daily", start_date="20240101", end_date=my_end_date, adjust="qfq")
            stock_zh_a_hist_df = get_bao_data(my_code,date_mins,last_date,my_end_date2)
            already_read = 0
        except Exception as e:
            print(f"数据获取失败2：{e}")
#            time.sleep(1)
            return stock_zh_a_hist_df
#        gp_data[my_code] = stock_zh_a_hist_df
    #    print(type(last_date))

    # 重命名列
    if already_read == 0:
        stock_zh_a_hist_df = deal_data(stock_zh_a_hist_df,date_mins)

    if date_mins == 'd':
        existing_columns_cvs = ['日期',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额']
    else:
        existing_columns_cvs = ['日期',	'开盘',	'收盘',	'最高',	'最低',	'成交量',	'成交额']
    df_selected = stock_zh_a_hist_df[existing_columns_cvs]
    df_selected.to_cvs(gp_path_bi , index=False,encoding='gbk')
    gp_data[my_code] = stock_zh_a_hist_df
    

    return stock_zh_a_hist_df    


def get_base_data_main():
    df_filtered , my_today = get_base_data_his()
    get_data_mutl(df_filtered , my_today)
    return
get_base_data_main()
#main()