import pandas as pd
from sqlalchemy import create_engine
import pymysql
import akshare as ak

engine = create_engine('mysql+pymysql://root:efATdUhSA&5Sy#gR@localhost:3306/web')
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
all_stock = stock_zh_a_spot_em_df.copy()
all_stock['时间'] = '2025-10-10'
all_stock['涨跌幅'] = round(all_stock['涨跌幅']/100, 4)
all_stock.sort_values(by='代码',ascending=True)
all_stock.to_sql(
    name='daily_price',
    con=engine,
    if_exists='append',
    index=False,
    chunksize=1000,
)
print('数据写入成功')