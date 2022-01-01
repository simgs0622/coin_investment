import os
import time
import pyupbit
import datetime
import numpy as np
import pandas as pd
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from tensorflow.keras.models import load_model

# 세팅 + 모델load
coin_list = ['KRW-BTC', 'KRW-ETH']
buy_check = {'KRW-BTC': 0, 'KRW-ETH': 0}
st_check = {'KRW-BTC': 0, 'KRW-ETH': 0}
tmp_close = 0
pred_val = 0
update_check = 0
new_model = load_model('ST_v2_prediction_l32_r10_012_0.595.h5', compile=False)

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
                time.sleep(10)
                
                krw_balance = upbit.get_balance("KRW")
                tmp_table = pd.DataFrame(upbit.get_balances())
                tmp_table.balance = tmp_table.balance.astype('float')
                tmp_table.avg_buy_price = tmp_table.avg_buy_price.astype('float')
                my_balance = sum(tmp_table.balance * tmp_table.avg_buy_price) + krw_balance
                investing_limit = my_balance * 0.2

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
                
                dd = str(pyupbit.get_ohlcv('KRW-ETH', count=1).index[0]).split()[0]
                close_ = list(pyupbit.get_ohlcv('KRW-ETH', count=37, to=dd).close)
                close_tmp = list((pd.Series(close_) / close_[-1]) - 1)
                volume_ = list(pyupbit.get_ohlcv('KRW-ETH', count=37, to=dd).volume)
                volume_tmp = list((pd.Series(volume_) / volume_[-1]) - 1)
                
                update_check = 1
                
            now = datetime.datetime.now()
#             print(now, st_check, target_prices, investing_amts, tmp_close, pred_val)
            
            for ind, coin in enumerate(coin_list):
                current_price = get_current_price(coin)
                coin_s = coin[4:]
                time.sleep(0.1)
                
                if (st_check[coin] == 0) and (coin == 'KRW-ETH'):
                    if (now.minute % 5 == 0) and (now.second == 3):
                        df1 = pyupbit.get_ohlcv('KRW-BTC', interval='minute5', count=38)
                        df2 = pyupbit.get_ohlcv('KRW-ETH', interval='minute5', count=38)
                        tmp_close = df2.close[-1]
                        df1 = df1[:37]
                        df2 = df2[:37]
                        
                        df = pd.concat([df1, df2], axis=1)
                        df.columns = ['open_x', 'high_x', 'low_x', 'close_x', 'volume_x', 'value_x', 'open_y', 'high_y', 'low_y', 'close_y', 'volume_y', 'value_y']
                        df = df[['open_x', 'high_x', 'low_x', 'close_x', 'volume_x', 'open_y', 'high_y', 'low_y', 'close_y', 'volume_y']]
                        df_sub = df.copy()

                        d_x = df_sub['close_x'][max(df_sub.index)]
                        d_vx = df_sub['volume_x'][max(df_sub.index)]
                        d_y = df_sub['close_y'][max(df_sub.index)]
                        d_vy = df_sub['volume_y'][max(df_sub.index)]

                        df_sub['open_x'] = (df_sub['open_x'] / d_x) - 1
                        df_sub['high_x'] = (df_sub['high_x'] / d_x) - 1
                        df_sub['low_x'] = (df_sub['low_x'] / d_x) - 1
                        df_sub['close_x'] = (df_sub['close_x'] / d_x) - 1
                        df_sub['volume_x'] = (df_sub['volume_x'] / d_vx) - 1
                        df_sub['open_y'] = (df_sub['open_y'] / d_y) - 1
                        df_sub['high_y'] = (df_sub['high_y'] / d_y) - 1
                        df_sub['low_y'] = (df_sub['low_y'] / d_y) - 1
                        df_sub['close_y'] = (df_sub['close_y'] / d_y) - 1
                        df_sub['volume_y'] = (df_sub['volume_y'] / d_vy) - 1
                        df_sub['closeD_y'] = close_tmp
                        df_sub['volumeD_y'] = volume_tmp

                        xtest = np.array(df_sub)
                        pred = new_model.predict(xtest.reshape(1,37,12))
                        pred_val = pred[0][0]
                        
                        if pred_val > 0.99:
                            upbit.buy_market_order(coin, investing_amts[ind])
                            time.sleep(5)
                            units = get_balance(coin_s)
                            if units > 0.00000001:
                                st_check[coin] = 1
                        
                        with open("log.txt", "w") as f:
                            f.write(str(current_price) + " " + str(pred_val))

                if (buy_check[coin] == 0) and (coin == 'KRW-BTC'):
                    if (target_prices[ind] < current_price) and (get_ma5(coin) < target_prices[ind]):
                        upbit.buy_market_order(coin, investing_amts[ind]*2)
                        time.sleep(5)
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            buy_check[coin] = 1
                    time.sleep(0.1)
                
                if (buy_check[coin] == 0) and (coin == 'KRW-ETH'):
                    if (target_prices[ind] < current_price) and (get_ma5(coin) < target_prices[ind]):
                        upbit.buy_market_order(coin, investing_amts[ind])
                        time.sleep(5)
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            buy_check[coin] = 1
                    time.sleep(0.1)
                
                if st_check[coin] == 1:
                    if (0.991 * tmp_close > current_price) or (1.009 * tmp_close < current_price):
                        units = get_balance(coin_s)
                        if units > 0.00000001:
                            if buy_check[coin] == 1:
                                upbit.sell_market_order(coin, units/2)
                            else:
                                upbit.sell_market_order(coin, units)
                        st_check[coin] = 0
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
                        
        else:
            if buy_check['KRW-BTC'] == 1:
                units = get_balance('BTC')
                upbit.sell_market_order('KRW-BTC', units)
                time.sleep(0.2)

            if buy_check['KRW-ETH'] == 1:
                units = get_balance('ETH')
                if st_check['KRW-ETH'] == 1:
                    upbit.sell_market_order('KRW-ETH', units/2)
                else:
                    upbit.sell_market_order('KRW-ETH', units)
                time.sleep(0.2)

            buy_check['KRW-BTC'] = 0
            buy_check['KRW-ETH'] = 0
            update_check = 0
            time.sleep(5)
    
    except Exception as e:
        print(e)
        time.sleep(1)