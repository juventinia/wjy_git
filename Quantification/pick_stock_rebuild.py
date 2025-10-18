import akshare as ak
import pandas as pd
import time
from datetime import datetime
import random
import json

def create_stock_target(symbol, date):
    stock_collection = ak.index_detail_cni(symbol=symbol, date=date)
    stock_collection_filter = stock_collection[(stock_collection['总市值'] >= 100) & (stock_collection['总市值'] <= 300)]
    code_list = [s for s in list(stock_collection_filter['样本代码']) if s[:3] != '688']
    print(f'满足条件的数量为{len(code_list)}')
    return code_list

def create_stock_handle(symbol, date, start_date, end_date):
    latest_golden_cross = []
    latest_death_cross = []
    code_sample = []
    code_list = create_stock_target(symbol, date)
    for code in code_list:
        print(f"正在获取{code}")
        stock = ak.stock_zh_a_hist(symbol=code, period='daily', start_date=start_date, end_date=end_date,
                                   adjust='qfq')
        handle_stock = stock[['日期', '开盘', '收盘', '最高', '最低']].copy()
        handle_stock.set_index('日期', inplace=True)
        handle_stock.index = pd.to_datetime(handle_stock.index)
        handle_stock.columns = ['open', 'close', 'high', 'low']
        data = handle_stock.copy()
        data['ma5'] = data['close'].rolling(window=5).mean()
        data['ma10'] = data['close'].rolling(window=10).mean()
        data.dropna(inplace=True)
        if data['close'].iloc[-1] >= 50:
            print(f"代码{code}最新价为{data['close'].iloc[-1]}，价格太高不满足条件")
        else:
            golden_cross = []
            death_cross = []
            for j in range(1, len(data)):
                if data['ma5'].iloc[j] >= data['ma10'].iloc[j] and data['ma5'].iloc[j - 1] <= data['ma10'].iloc[j - 1]:
                    golden_cross.append(data.index[j])
                elif data['ma5'].iloc[j] <= data['ma10'].iloc[j] and data['ma5'].iloc[j - 1] >= data['ma10'].iloc[
                    j - 1]:
                    death_cross.append(data.index[j])

            if len(golden_cross) > 0 and len(death_cross) > 0:
                code_sample.append(code)
                latest_golden_cross.append(golden_cross[-1].strftime('%Y-%m-%d'))
                print(f"代码{code}，最新的buy时间为：{latest_golden_cross[-1]}")
                latest_death_cross.append(death_cross[-1].strftime('%Y-%m-%d'))
                print(f"代码{code}，最新的sold时间为：{latest_death_cross[-1]}")
                time.sleep(random.uniform(4, 7))
    return code_sample, latest_golden_cross, latest_death_cross

if __name__ == '__main__':
    result_dict=[]
    code_sample, latest_golden_cross, latest_death_cross = create_stock_handle('399303', '202508', '20250601',
                                                                               '20251013')
    for c, g, d in zip(code_sample, latest_golden_cross, latest_death_cross):
        item = {
            "code": c,
            "last_day": {
                "latest_golden_cross": g,
                "latest_death_cross": d
            }
        }
        result_dict.append(item)
    sort_result = sorted(result_dict, key=lambda x: datetime.strptime(x['last_day']['latest_golden_cross'], '%Y-%m-%d'),
                         reverse=True)
    result = json.dumps(sort_result)
    print(result)