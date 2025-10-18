import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import time
import random

def ma5_ma10_strategy(stock_code, period, start_date, end_date, adjust, initial_money, verbose, plot):
    #verbose打印过程
    df = ak.stock_zh_a_hist(
        symbol = stock_code,
        period = period,
        start_date = start_date,
        end_date = end_date,
        adjust = adjust
    )
# 数据清洗
    every_stock = df[['日期', '开盘', '收盘', '最高', '最低']].copy()
    every_stock.set_index('日期', inplace = True)
    every_stock.index = pd.to_datetime(every_stock.index)
    every_stock.columns = ['open','close','high','low']

    dt_stock = every_stock.copy()
    dt_stock['ma5'] = dt_stock['close'].rolling(window=5).mean()
    dt_stock['ma10'] = dt_stock['close'].rolling(window=10).mean()
    dt_stock.dropna(inplace=True)
#构建金叉死叉日期
    golden_cross = []
    death_cross = []
    for i in range(1, len(dt_stock.index)):
        if dt_stock['ma5'].iloc[i] >= dt_stock['ma10'].iloc[i] and dt_stock['ma5'].iloc[i - 1] < dt_stock['ma10'].iloc[i - 1]:
            golden_cross.append(dt_stock.index[i])
        elif dt_stock['ma5'].iloc[i] <= dt_stock['ma10'].iloc[i] and dt_stock['ma5'].iloc[i - 1] > dt_stock['ma10'].iloc[i - 1]:
            death_cross.append(dt_stock.index[i])
#构建金叉死叉标志
    sr1 = pd.Series(1, index = golden_cross)
    sr2 = pd.Series(0, index = death_cross)
    sr = pd.concat([sr1, sr2]).sort_index()
#构建序列前后日期序列，用于计算两次操作之间的日期
    sr_frame = pd.DataFrame(sr, columns=['flag'])
    sra = sr_frame.copy()
    sra['sequence'] = 0
    for j in range(0, len(sra)):
        sra.loc[sra.index[j], 'sequence'] = j
#初始化
    money = initial_money
    hold = 0
    cost_tax = 0
    equity_curve = pd.Series(index=dt_stock.index)

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"开始回测: {stock_code} | 初始资金: {initial_money}")
        print(f"{'=' * 60}")
#交易循环
    for date in dt_stock.index:
        p = dt_stock['open'][date]
        current_money = money + p * hold
        equity_curve[date] = current_money #计算每日资金量，画图用
        # print(equity_curve)

        if date in sr.index:
            signal = sr.loc[date]
            price = dt_stock['close'][date]

            if sra.loc[date]['sequence'] > 1:
                back = sra.loc[date]['sequence'] - 2
                forward_date = sra[sra['sequence'] == back].index
                now_date = sra[sra['sequence']==sra.loc[date]['sequence']].index
                dif = now_date - forward_date
                # print(dif)

                if signal == 1 and dif.days >= 10: # 两次操作之间的天数，屏蔽震荡行情
                    buy_units = money // (100 * price)
                    if buy_units > 0:
                        hold += buy_units * 100
                        trade_value = buy_units * 100 * price
                        commission = max(5, trade_value * 0.0002) + 0.1
                        cost_tax += commission
                        money -= trade_value
                        if verbose:
                            print(f"{date.date()} 金叉买入 | 价格: {round(p, 2)} | 持股: {hold} | 现金: {int(money)} "
                                  f"| 交易费用: {cost_tax}")

                elif signal == 0  and dif.days >= 10:  # 卖出
                    trade_value = hold * price
                    if hold > 0:
                        commission = max(5, trade_value * 0.0002)
                        stamp_tax = trade_value * 0.001
                        cost_tax += commission + stamp_tax + 0.1
                        hold = 0
                    else:
                        pass
                    money += trade_value

                    if verbose:
                        print(f"{date.date()} 死叉卖出 | 价格: {round(p, 2)} | 持股: {hold} | 现金: {int(money)}"
                              f"| 交易费用: {cost_tax}")
        else:
            continue

        #绘图
    if plot:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Noto Sans CJK SC']
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve, label='策略', color='blue')
        buy_and_hold = initial_money / dt_stock['open'].iloc[0]
        bh_value = dt_stock['open'] * buy_and_hold
        plt.plot(bh_value, label='持有', color='gray', linestyle='--')
        plt.xlabel('date')
        plt.ylabel('money')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    final_price = dt_stock['open'].iloc[-1]
    now_money = hold * final_price + money - cost_tax
    return_rate = (now_money - initial_money) / initial_money * 100
    hold_rate = (dt_stock['close'].iloc[-1] - dt_stock['open'].iloc[0]) / dt_stock['open'].iloc[0] * 100

    print(f"\n{stock_code} 回测结束")
    print(f"最终资金: {round(now_money, 2)}")
    print(f"收益率: {round(return_rate, 2)}%")
    print(f"持有: {round(hold_rate, 2)}%")

    return {
        "stock": stock_code,
        "final_money": round(now_money, 2),
        "return_rate": round(return_rate, 2),
        "initial_money": initial_money,
        "total_trades": len(sr),
        "hold": hold,
        "final_price": final_price,
        "cost_tax": round(cost_tax, 2),
        "equity_curve": equity_curve,
        "status": "success"
    }

if __name__ == "__main__":
    stock_list = ['002052']
    for stock in stock_list:
        result = ma5_ma10_strategy(
            stock_code=stock,
            period='daily',
            start_date='20240101',
            end_date='20250929',
            initial_money=100000,
            verbose=True,
            adjust='qfq',
            plot=True
        )
        time.sleep(random.uniform(3, 5))






