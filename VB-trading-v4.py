import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

access = "OtkVxrcbD942wwx15frEyOM5PAGEhDaIXLBmi0lt"
secret = "XYngSUtQTUxXBpXOopRh3Rtjc3xNbhS087LLdx71"

coin_list = ['KRW-EOS']
coin_shortlist = ['EOS']

buy_check = {}
for coin in coin_list:
    buy_check[coin] = 0

def get_target_price(ticker, k, base):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ran = df.iloc[-2]['high'] - df.iloc[-2]['low']  # 전날 변동폭
    target_price = df.iloc[-2]['close'] + (ran) * k
    return target_price

def get_start_time(ticker, base):
    """시작 시간 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    start_time = df.index[-1]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
my_balance = upbit.get_balance("KRW")
invest_limit = my_balance / len(coin_list)
now = datetime.datetime.now()
sell_time = now + datetime.timedelta(hours=24)

# 자동매매 시작
print("autotrade start")
while True:
    try:
        base = 0.1
        now = datetime.datetime.now()
#         print(now, buy_check)

        start_times = []
        for coin in coin_list:
            start_time = get_start_time(coin, base)
            start_times.append(start_time)
            time.sleep(0.1)
        start_time = min(start_times)
        end_time = start_time + datetime.timedelta(hours=24)

        if start_time < now < end_time - datetime.timedelta(minutes=2):
            target_prices = []
            for ind, coin in enumerate(coin_list):
                target_price = get_target_price(coin, 0.3, base)
                target_prices.append(target_price)
            
            for ind, coin in enumerate(coin_list):
                current_price = get_current_price(coin)
                investing_price = invest_limit * 0.99
                
                if buy_check[coin] == 0:
                    if target_prices[ind] < current_price:
                        upbit.buy_market_order(coin, investing_price)
                        buy_check[coin] = 1
                        buy_time = datetime.datetime.now()
                        sell_time = buy_time + datetime.timedelta(minutes=15)
#                         print(coin, ' 매수했음ㅋ_ㅋ')
                        time.sleep(0.2)
                
                if buy_check[coin] == 1:
                    now = datetime.datetime.now()
                    if sell_time < now:
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            upbit.sell_market_order(coin, units)
#                             print(coin, ' 매도했음ㅋ_ㅋ')
                time.sleep(0.2)

        else:
            for ind, coin in enumerate(coin_shortlist):
                units = get_balance(coin)
                if units > 0.00000001:
                    upbit.sell_market_order(coin_list[ind], units)
                time.sleep(0.2)

            buy_check = {}
            for coin in coin_list:
                buy_check[coin] = 0
            
            now = datetime.datetime.now()
            sell_time = now + datetime.timedelta(hours=24)
                
            my_balance = upbit.get_balance("KRW")
            invest_limit = my_balance / len(coin_list)
            time.sleep(5)
    
    except Exception as e:
        print(e)
        time.sleep(1)