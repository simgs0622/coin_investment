import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

access = "OtkVxrcbD942wwx15frEyOM5PAGEhDaIXLBmi0lt"
secret = "XYngSUtQTUxXBpXOopRh3Rtjc3xNbhS087LLdx71"

coin_list = ['KRW-ETH', 'KRW-BTC']
coin_shortlist = ['ETH', 'BTC']

buy_check = {}
for coin in coin_list:
    buy_check[coin] = 0
buy_check['KRW-ETH'] = 1
update_check = 0

def get_target_price(ticker, k, base):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ran = df.iloc[-2]['high'] - df.iloc[-2]['low']  # 전날 변동폭
    target_price = df.iloc[-1]['open'] + (ran) * k
    return target_price

def get_investing_rate(ticker, tv, base):
    """변동성 통제를 위한 투자비율 산출"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    vol = ((df.iloc[-2]['high'] - df.iloc[-2]['low']) / df.iloc[-2]['open']) * 100
    if vol < tv:
        investing_rate = 1
    else:
        investing_rate = tv / vol
    return investing_rate

def get_start_time(ticker, base):
    """시작 시간 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    start_time = df.index[-1]
    return start_time

def get_hp(ticker):
    """직전일의 high 가격 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    high = df.iloc[-2]['high']
    return high

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=6)
    ma5 = df['close'].rolling(5).mean().iloc[-2]
    return ma5

def get_ma60(ticker):
    """60일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=61)
    ma60 = df['close'].rolling(60).mean().iloc[-2]
    return ma60

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
investing_limit = my_balance / (len(coin_list)-1)
high_prices = [0]

# 자동매매 시작
print("autotrade start")
while True:
    try:
        start_times = []
        for coin in coin_list:
            start_time = get_start_time(coin, 9)
            start_times.append(start_time)
            time.sleep(0.1)
        start_time = min(start_times)
        end_time = start_time + datetime.timedelta(hours=24)

        now = datetime.datetime.now()
        if start_time < now < end_time - datetime.timedelta(minutes=1):
            if update_check == 0:
                time.sleep(60)
                my_balance = upbit.get_balance("KRW")
                investing_limit = my_balance / (len(coin_list)-1)
                
                target_prices = []
                for ind, coin in enumerate(coin_list):
                    target_price = get_target_price(coin, 0.3, 9)
                    target_prices.append(target_price)
                    time.sleep(0.1)
                target_prices[0] = 99999999

                investing_amts = []
                for ind, coin in enumerate(coin_list):
                    investing_rate = get_investing_rate(coin, 5, 9)
                    investing_amt = investing_limit * investing_rate * 0.999
                    investing_amts.append(investing_amt)
                    time.sleep(0.1)
                
                for ind, coin in enumerate(coin_list):
                    if coin == 'KRW-ETH':
                        high_price = get_hp(coin)
                        high_prices.append(high_price)
                update_check = 1
                
            now = datetime.datetime.now()
#             print(now, buy_check, target_prices, investing_amts, high_prices)
            
            for ind, coin in enumerate(coin_list):
                current_price = get_current_price(coin)
                time.sleep(0.1)

                if buy_check[coin] == 0:
                    if (target_prices[ind] < current_price) and (get_ma5(coin) < target_prices[ind]):
                        upbit.buy_market_order(coin, investing_amts[ind])
                        buy_check[coin] = 1
                    time.sleep(0.1)
                
                if (buy_check[coin] == 1) and (coin == 'KRW-ETH'):
                    if (get_ma60(coin) > current_price) or (0.7 * max(high_prices) > current_price):
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            upbit.sell_market_order(coin, units)
                        high_prices = [0]
                    time.sleep(0.1)
                
                if (buy_check[coin] == 1) and (coin == 'KRW-BTC'):
                    if (0.8 * target_prices[ind]) > current_price:
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            upbit.sell_market_order(coin, units)
                    time.sleep(0.1)

        else:
            for ind, coin in enumerate(coin_list):
                if (buy_check[coin] == 1) and (coin == 'KRW-BTC'):
                    coin_s = coin_shortlist[ind]
                    units = get_balance(coin_s)
                    if units > 0.00000001:
                        upbit.sell_market_order(coin, units)
                    time.sleep(0.2)

            buy_check = {}
            for coin in coin_list:
                buy_check[coin] = 0
            buy_check['KRW-ETH'] = 1
            update_check = 0
            
            my_balance = upbit.get_balance("KRW")
            investing_limit = my_balance / (len(coin_list)-1)
            time.sleep(5)
    
    except Exception as e:
        print(e)
        time.sleep(1)