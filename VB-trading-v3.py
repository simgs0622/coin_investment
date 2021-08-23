import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

access = "OtkVxrcbD942wwx15frEyOM5PAGEhDaIXLBmi0lt"
secret = "XYngSUtQTUxXBpXOopRh3Rtjc3xNbhS087LLdx71"
# coin_list = ['KRW-BTC', 'KRW-LTC', 'KRW-ETC', 'KRW-ETH', 'KRW-EOS']
# coin_shortlist = ['BTC', 'LTC', 'ETC', 'ETH', 'EOS']
krw_tickers = pyupbit.get_tickers("KRW")

candidate_list = []
vola_list = []
noise_list = []
for coin in krw_tickers:
    df = pyupbit.get_daily_ohlcv_from_base(coin, 20)
    df['vola'] = (df['high'] - df['low']) / df['open'] * 100
    df['noise'] = 1 - (abs(df['close'] - df['open']) / (df['high'] - df['low']))
    
    if df.shape[0] >= 9:
        candidate_list.append(coin)
        vola_list.append(np.mean(df['vola']))
        noise_list.append(np.mean(df['noise']))
df_result = pd.DataFrame({'coin': candidate_list, 'vola': vola_list, 'noise': noise_list})

df_result_sub = df_result[df_result['noise'] < 0.5]
if df_result_sub.shape[0] < 5:
    coin_list = ['KRW-BTC', 'KRW-LTC', 'KRW-ETC', 'KRW-ETH', 'KRW-EOS']
    coin_shortlist = ['BTC', 'LTC', 'ETC', 'ETH', 'EOS']
    noise_list = [0.55, 0.55, 0.55, 0.55, 0.55]
else:
    df_result_sub = df_result_sub.sort_values(by=['vola'], ascending=False)
    df_result_sub = df_result_sub.reset_index(drop='index')
    df_result_sub = df_result_sub[:5]
    coin_list = list(df_result_sub['coin'])
    coin_shortlist = [x.split('-')[1] for x in coin_list]
    noise_list = list(df_result_sub['noise'])

buy_check = {}
buy_check2 = {}
sonjeol_check = {}
for coin in coin_list:
    buy_check[coin] = 0
    buy_check2[coin] = 0
    sonjeol_check[coin] = 0

def get_target_price(ticker, k, base):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ran = df.iloc[-2]['high'] - df.iloc[-2]['low']  # 전날 변동폭
    ran *= (2/3)  # 12시간 변동폭 추정치
    target_price = df.iloc[-2]['close'] + (ran) * k
    return target_price

def get_investing_rate(ticker, tv, base):
    """변동성 통제를 위한 투자비율 산출"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    vol = ((df.iloc[-2]['high'] - df.iloc[-2]['low']) / df.iloc[-2]['open']) * 100
    vol *= (2/3)
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

def get_start_price(ticker, base):
    """시작 가격 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    start_price = df['open'][-1]
    return start_price

def get_prev_price(ticker):
    """12시간 전 가격 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=25)
    prev_price = df['open'][12]
    return prev_price

def get_ma3(ticker, base):
    """3일 이동 평균선 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ma3 = df['close'].rolling(3).mean().iloc[-1]
    return ma3

def get_ma5(ticker, base):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_ma7(ticker, base):
    """7일 이동 평균선 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ma7 = df['close'].rolling(7).mean().iloc[-1]
    return ma7

def get_ma10(ticker, base):
    """10일 이동 평균선 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    return ma10

def get_ma9(ticker, base):
    """9일 이동 평균선 조회"""
    df = pyupbit.get_daily_ohlcv_from_base(ticker, base=base)
    ma9 = df['close'].rolling(9).mean().iloc[-1]
    return ma9

def get_volume(ticker):
    """직전12시간 거래량 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=25)
    vol = sum(df['volume'][12:24])
    return vol

def get_prev_volume(ticker):
    """직전24~12시간 거래량 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute60", count=25)
    vol = sum(df['volume'][0:12])
    return vol

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
invest_limit = my_balance / len(coin_list) / 2  # 코인 5개 2개 전략
coin = coin_list[0]
investing_price = 0
update_yn = 0

target_prices = []
for ind, coin in enumerate(coin_list):
    target_price = get_target_price(coin, noise_list[ind], 20)
    target_prices.append(target_price)

# 자동매매 시작
print("autotrade start")
while True:
    try:
        base = 20
        now = datetime.datetime.now()
#         print(buy_check, buy_check2, sonjeol_check, now)
#         print(coin, ' 투자금액: ', investing_price)
        start_times = []
        for coin in coin_list:
            start_time = get_start_time(coin, base)
            start_times.append(start_time)
            time.sleep(0.1)
        start_time = min(start_times)
            
        if (start_time.dayofweek) == 4 or (start_time.dayofweek) == 5:
            base = 22  # 금 토는 밤 10시에 투자
        start_times = []
        for coin in coin_list:
            start_time = get_start_time(coin, base)
            start_times.append(start_time)
            time.sleep(0.1)
        start_time = min(start_times)
        
        check_time = start_time + datetime.timedelta(minutes=10)
        end_time = start_time + datetime.timedelta(hours=12)
        
        if start_time < now < check_time:
            if update_yn == 0:
                krw_tickers = pyupbit.get_tickers("KRW")
                candidate_list = []
                vola_list = []
                noise_list = []
                for coin in krw_tickers:
                    df = pyupbit.get_daily_ohlcv_from_base(coin, 20)
                    df['vola'] = (df['high'] - df['low']) / df['open'] * 100
                    df['noise'] = 1 - (abs(df['close'] - df['open']) / (df['high'] - df['low']))

                    if df.shape[0] >= 9:
                        candidate_list.append(coin)
                        vola_list.append(np.mean(df['vola']))
                        noise_list.append(np.mean(df['noise']))
                df_result = pd.DataFrame({'coin': candidate_list, 'vola': vola_list, 'noise': noise_list})

                df_result_sub = df_result[df_result['noise'] < 0.5]
                if df_result_sub.shape[0] < 5:
                    coin_list = ['KRW-BTC', 'KRW-LTC', 'KRW-ETC', 'KRW-ETH', 'KRW-EOS']
                    coin_shortlist = ['BTC', 'LTC', 'ETC', 'ETH', 'EOS']
                    noise_list = [0.55, 0.55, 0.55, 0.55, 0.55]
                else:
                    df_result_sub = df_result_sub.sort_values(by=['vola'], ascending=False)
                    df_result_sub = df_result_sub.reset_index(drop='index')
                    df_result_sub = df_result_sub[:5]
                    coin_list = list(df_result_sub['coin'])
                    coin_shortlist = [x.split('-')[1] for x in coin_list]
                    noise_list = list(df_result_sub['noise'])

                buy_check = {}
                buy_check2 = {}
                sonjeol_check = {}
                for coin in coin_list:
                    buy_check[coin] = 0
                    buy_check2[coin] = 0
                    sonjeol_check[coin] = 0
                
                update_yn = 1
            
#             print('전략2 투자금액 판단중', start_time, now)
            investing_prices2 = []
            for ind, coin in enumerate(coin_list):
                investing_rate = get_investing_rate(coin, 1, base)
                if (get_prev_volume(coin) < get_volume(coin)) and (get_prev_price(coin) < get_start_price(coin, base)):
                    investing_price = invest_limit * investing_rate * 0.9995
                    investing_prices2.append(investing_price)
                else:
                    investing_prices2.append(0)
#             print(investing_prices2)
            
            for ind, coin in enumerate(coin_list):
                if (buy_check2[coin] == 0) and (sonjeol_check[coin] == 0):
                    if investing_prices2[ind] > 0:
                        upbit.buy_market_order(coin, investing_prices2[ind])
                        buy_check2[coin] = 1
#                         print(coin, ' 전략2로 매수했음ㅋ_ㅋ')
                        time.sleep(0.2)
            
            target_prices = []
            for ind, coin in enumerate(coin_list):
                target_price = get_target_price(coin, noise_list[ind], base)
                target_prices.append(target_price)

        if start_time < now < end_time - datetime.timedelta(seconds=59):
            for ind, coin in enumerate(coin_list):
                current_price = get_current_price(coin)
                investing_rate = get_investing_rate(coin, 3, base)
                
                # 상승장의 정도를 0~1로 판단 for 전략 1
                try:
                    tmp = 0
                    if (get_ma3(coin, base) < current_price):
                        tmp += 1
                    if (get_ma5(coin, base) < current_price):
                        tmp += 1
                    if (get_ma7(coin, base) < current_price):
                        tmp += 1
                    if (get_ma10(coin, base) < current_price):
                        tmp += 1
                    investing_rate2 = tmp / 4
                    time.sleep(0.1)
                
                except:
                    tmp = 0
                    if (get_ma3(coin, base) < current_price):
                        tmp += 1
                    if (get_ma5(coin, base) < current_price):
                        tmp += 1
                    if (get_ma7(coin, base) < current_price):
                        tmp += 1
                    if (get_ma9(coin, base) < current_price):
                        tmp += 1
                    investing_rate2 = tmp / 4
                    time.sleep(0.1)
                    
                investing_price = invest_limit * investing_rate * investing_rate2 * 0.9995
                
                if (buy_check[coin] == 0) and (sonjeol_check[coin] == 0):
                    if (target_prices[ind] < current_price) and (investing_price > 0):
                        upbit.buy_market_order(coin, investing_price)
                        buy_check[coin] = 1
#                         print(coin, ' 전략1로 매수했음ㅋ_ㅋ')
                        time.sleep(0.2)
                
                if (buy_check[coin] == 1) or (buy_check2[coin] == 1):
                    if (0.8 * target_prices[ind]) > current_price:
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        upbit.sell_market_order(coin, units)
                        sonjeol_check[coin] = 1
#                         print(coin, ' 손절 매도했음ㅜ_ㅜ')
                time.sleep(0.2)

        else:
            for ind, coin in enumerate(coin_shortlist):
                units = get_balance(coin)
                if units > 0.00000001:
                    upbit.sell_market_order(coin_list[ind], units)
#                     print(coin, ' 투자시간 끝나서 매도했음ㅋ_ㅋ')
#                 print('테스트', coin, units)
                time.sleep(0.2)
                
            my_balance = upbit.get_balance("KRW")
            invest_limit = my_balance / len(coin_list) / 2  # 코인 5개 2개 전략
            
            update_yn = 0
            
            time.sleep(5)
    
    except Exception as e:
        print(e)
        time.sleep(1)