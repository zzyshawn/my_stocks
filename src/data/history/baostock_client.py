import baostock as bs
import pandas as pd

def get_exchange_all_bao(stock_code):
    if stock_code.startswith('6'):
        return 'sh.'+stock_code
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        return 'sz.'+stock_code
    elif stock_code.startswith('8') or stock_code.startswith('9') or stock_code.startswith('4'):
        return 'bj.'+stock_code
    else:
        return '未知'

def bs_login(login):

    if login == 1:
        #### 登陆系统 ####
        lg = bs.login()
        # 显示登陆返回信息
        print('login respond error_code:'+lg.error_code)
        print('login respond  error_msg:'+lg.error_msg)
    else:
            #### 登出系统 ####
        bs.logout()
    return

def get_bao_data(ID,isdate,start,end):
    #### 获取沪深A股历史K线数据 ####
    # 详细指标参数，参见"历史行情指标参数"章节；"分钟线"参数与"日线"参数不同。"分钟线"不包含指数。
    # 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
    # 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg

    if isdate == "d":
        rs = bs.query_history_k_data_plus(get_exchange_all_bao(ID),
            "date,code,open,close,high,low,volume,amount,turn,tradestatus",
            start_date=start, end_date=end,
            frequency="d", adjustflag="2")
    else:
        rs = bs.query_history_k_data_plus(get_exchange_all_bao(ID),
            "time,code,open,close,high,low,volume,amount",
            start_date=start, end_date=end,
            frequency=isdate, adjustflag="2")
    print('query_history_k_data_plus respond error_code:'+rs.error_code)
    print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

    #### 打印结果集 ####
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)

    #### 结果集输出到csv文件 ####
    #result.to_csv("D:\\history_A_stock_k_data.csv", index=False)
    return result