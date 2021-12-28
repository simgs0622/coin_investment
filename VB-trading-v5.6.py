import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

# 세팅
coin_list = ['KRW-BTC', 'KRW-ETH', 'KRW-ZIL']
buy_check = {'KRW-BTC': 0, 'KRW-ETH': 0, 'KRW-ZIL': 0}

# 로그인
access = "OtkVxrcbD942wwx15frEyOM5PAGEhDaIXLBmi0lt"
secret = "XYngSUtQTUxXBpXOopRh3Rtjc3xNbhS087LLdx71"
upbit = pyupbit.Upbit(access, secret)

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, count=2)
    ran = df.iloc[-2]['high'] - df.iloc[-2]['low']  # 전날 변동폭
    target_price = df.iloc[-1]['open'] + (ran) * k
    return target_price

def get_investing_rate(ticker, tv):
    """변동성 통제를 위한 투자비율 산출"""
    df = pyupbit.get_ohlcv(ticker, count=2)
    vol = ((df.iloc[-2]['high'] - df.iloc[-2]['low']) / df.iloc[-2]['open']) * 100
    if vol < tv:
        investing_rate = 1
    else:
        investing_rate = tv / vol
    return investing_rate

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, count=1)
    start_time = df.index[-1]
    return start_time

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=6)
    ma5 = df['close'].rolling(5).mean().iloc[-2]
    return ma5

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
    return pyupbit.get_current_price(ticker)

# 자동매매 시작
update_check = 0
print("autotrade start")
while True:
    try:
        if update_check == 0:
            start_times = []
            for coin in coin_list:
                start_time = get_start_time(coin)
                start_times.append(start_time)
                time.sleep(0.1)
            start_time = min(start_times)
            end_time = start_time + datetime.timedelta(hours=24)

        now = datetime.datetime.now()
        if start_time < now < end_time - datetime.timedelta(minutes=1):
            if update_check == 0:
                time.sleep(30)
                
                krw_balance = upbit.get_balance("KRW")
                tmp_table = pd.DataFrame(upbit.get_balances())
                tmp_table.balance = tmp_table.balance.astype('float')
                tmp_table.avg_buy_price = tmp_table.avg_buy_price.astype('float')
                my_balance = sum(tmp_table.balance * tmp_table.avg_buy_price) + krw_balance
                investing_limit = my_balance * 0.35

                target_prices = []
                for coin in coin_list:
                    target_price = get_target_price(coin, 0.3)
                    target_prices.append(target_price)
                    time.sleep(0.1)

                investing_amts = []
                for coin in coin_list:
                    investing_rate = get_investing_rate(coin, 5)
                    investing_amt = int(investing_limit * investing_rate)
                    investing_amts.append(investing_amt)
                    time.sleep(0.1)
                
                update_check = 1
                
#             now = datetime.datetime.now()
#             print(now, buy_check, target_prices, investing_amts)
            
            for ind, coin in enumerate(coin_list):
                current_price = get_current_price(coin)
                coin_s = coin[4:]
                time.sleep(0.2)

                if (buy_check[coin] == 0) and ((coin == 'KRW-BTC') or (coin == 'KRW-ETH')):
                    if (target_prices[ind] < current_price) and (get_ma5(coin) < target_prices[ind]):
                        upbit.buy_market_order(coin, investing_amts[ind])
                        time.sleep(5)
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            buy_check[coin] = 1
                    time.sleep(0.1)
                
                if buy_check[coin] == 1:
                    if coin == 'KRW-BTC':
                        if 0.92 * target_prices[ind] > current_price:
                            units = get_balance(coin_s)
                            if units > 0.00000001:
                                upbit.sell_market_order(coin, units)
                        time.sleep(0.1)

                    if coin == 'KRW-ETH':
                        if 0.9 * target_prices[ind] > current_price:
                            units = get_balance(coin_s)
                            if units > 0.00000001:
                                upbit.sell_market_order(coin, units)
                        time.sleep(0.1)
                    
                    if coin == 'KRW-ZIL':
                        if (0.9 * 116 > current_price) or (1.1 * 116 < current_price):
                            units = get_balance(coin_s)
                            if units > 0.00000001:
                                upbit.sell_market_order(coin, units)
                            buy_check[coin] = 0
                        time.sleep(0.1)

        else:
            if buy_check['KRW-BTC'] == 1:
                units = get_balance('BTC')
                upbit.sell_market_order('KRW-BTC', units)
                time.sleep(0.2)

            if buy_check['KRW-ETH'] == 1:
                units = get_balance('ETH')
                upbit.sell_market_order('KRW-ETH', units)
                time.sleep(0.2)

            buy_check['KRW-BTC'] = 0
            buy_check['KRW-ETH'] = 0
            update_check = 0
            time.sleep(5)
    
    except Exception as e:
        print(e)
        time.sleep(1)