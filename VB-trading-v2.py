import time
import pyupbit
import datetime

access = ""
secret = ""
coin_list = ['KRW-XRP', 'KRW-BTC', 'KRW-LTC', 'KRW-ETC', 'KRW-ETH', 'KRW-EOS']
coin_shortlist = ['XRP', 'BTC', 'LTC', 'ETC', 'ETH', 'EOS']

buy_check = {}
sonjeol_check = {}
for coin in coin_list:
    buy_check[coin] = 0
    sonjeol_check[coin] = 0
buy_check['KRW-ETC'] = 3  #############################################################################
buy_check['KRW-XRP'] = 3  #############################################################################
buy_check['KRW-LTC'] = 3  #############################################################################
buy_check['KRW-ETH'] = 3  #############################################################################
buy_check['KRW-EOS'] = 3  #############################################################################

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
    ran1 = df.iloc[0]['high'] - df.iloc[0]['low']  # 전전날 변동폭
    ran2 = df.iloc[1]['high'] - df.iloc[1]['low']  # 전날 변동폭
    target_price = df.iloc[1]['close'] + ((ran1 + ran2) / 2) * k
    return target_price

def get_investing_rate(ticker, tv):
    """변동성 통제를 위한 투자비율 산출"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
    vol1 = ((df.iloc[0]['high'] - df.iloc[0]['low']) / df.iloc[0]['open']) * 100
    vol2 = ((df.iloc[1]['high'] - df.iloc[1]['low']) / df.iloc[1]['open']) * 100
    if ((vol1 + vol2) / 2) < tv:
        investing_rate = 1
    else:
        investing_rate = tv / ((vol1 + vol2) / 2)
    return investing_rate

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

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

investing_prices = []
for coin in coin_list:
    investing_rate = get_investing_rate(coin, 3.5)
    investing_price = invest_limit * investing_rate * 0.9995
    investing_prices.append(investing_price)
print("autotrade start")

# 자동매매 시작
while True:
    tmp = 0
    for coin in coin_list:
        tmp += buy_check[coin]
    if tmp == 0:
        my_balance = upbit.get_balance("KRW")
        invest_limit = my_balance / len(coin_list)
    
    try:
        now = datetime.datetime.now()
#         print(buy_check, sonjeol_check, now)
        start_time = get_start_time("KRW-BTC")
        check_time = start_time + datetime.timedelta(minutes=10)
        end_time = start_time + datetime.timedelta(days=1)
        
        if start_time < now < check_time:
            investing_prices = []
            for coin in coin_list:
                investing_rate = get_investing_rate(coin, 3.5)
                investing_price = invest_limit * investing_rate * 0.9995
                investing_prices.append(investing_price)

        if start_time < now < end_time - datetime.timedelta(seconds=59):
            for ind, coin in enumerate(coin_list):
                ma5 = get_ma5(coin)
                ma15 = get_ma15(coin)
                current_price = get_current_price(coin)
                
                if (ma5 < current_price) and (ma15 < current_price) and (buy_check[coin] == 0) and (sonjeol_check[coin] == 0):
                    target_price = get_target_price(coin, 0.15)
                    if target_price < current_price:
                        upbit.buy_market_order(coin, investing_prices[ind])
                        buy_check[coin] = 3
#                         print(coin, ' 매수했음ㅋ_ㅋ')
                        time.sleep(0.2)
                        
                if (buy_check[coin] == 0) and (sonjeol_check[coin] == 0):
                    target_price = get_target_price(coin, 0.95)
                    if target_price < current_price:
                        upbit.buy_market_order(coin, investing_prices[ind])
                        buy_check[coin] = 2
#                         print(coin, ' 매수했음ㅋ_ㅋ')
                        time.sleep(0.2)
                
                if buy_check[coin] == 3:
                    target_price = get_target_price(coin, 0.15)
                    if (0.95 * target_price) > current_price:
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        upbit.sell_market_order(coin, units)
                        sonjeol_check[coin] = 1
#                         print(coin, ' 매도했음ㅋ_ㅋ')
                
                if buy_check[coin] == 2:
                    target_price = get_target_price(coin, 0.95)
                    if (0.95 * target_price) > current_price:
                        coin_s = coin_shortlist[ind]
                        units = get_balance(coin_s)
                        upbit.sell_market_order(coin, units)
                        sonjeol_check[coin] = 1
#                         print(coin, ' 매도했음ㅋ_ㅋ')
                time.sleep(0.2)
                
        else:
            buy_check = {}
            sonjeol_check = {}
            for coin in coin_list:
                buy_check[coin] = 0
                sonjeol_check[coin] = 0
            
            for ind, coin in enumerate(coin_shortlist):
                units = get_balance(coin)
                if units > 0.00000001:
                    upbit.sell_market_order(coin_list[ind], units)
#                     print(coin, ' 매도했음ㅋ_ㅋ')
                time.sleep(0.2)
        time.sleep(1)
    
    except Exception as e:
        print(e)
        time.sleep(1)
