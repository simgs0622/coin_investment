import time
import pyupbit
import datetime

access = ""
secret = ""
coin_list = ['KRW-XRP', 'KRW-BTC', 'KRW-LINK', 'KRW-ETC', 'KRW-ETH']
coin_shortlist = ['XRP', 'BTC', 'LINK', 'ETC', 'ETH']
buy_check = {}
for coin in coin_list:
    buy_check[coin] = 0

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_investing_rate(ticker, tv):
    """변동성 통제를 위한 투자비율 산출"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    vol = ((df.iloc[0]['high'] - df.iloc[0]['low']) / df.iloc[0]['open']) * 100
    if vol < tv:
        investing_rate = 1
    else:
        investing_rate = tv / vol
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
print("autotrade start")

# 자동매매 시작
while True:
    tmp = 0
    for coin in coin_list:
        tmp += buy_check[coin]
    if tmp == 0:
        my_balance = upbit.get_balance("KRW")
    
    try:
        now = datetime.datetime.now()
        print(buy_check, now)
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=59):
            for coin in coin_list:
                target_price = get_target_price(coin, 0.55)
                ma5 = get_ma5(coin)
                current_price = get_current_price(coin)
                investing_rate = get_investing_rate(coin, 3.5)
                
                if target_price < current_price and ma5 < current_price and (buy_check[coin] == 0):
                    my_balance = upbit.get_balance("KRW")
                    investing_price = my_balance * (1/(len(coin_list)-tmp)) * investing_rate  * 0.9995
                    upbit.buy_market_order(coin, investing_price)
                    buy_check[coin] = 1
                    print(coin, ' 매수했음ㅋ_ㅋ')
                time.sleep(0.3)
                
        else:
            buy_check = {}
            for coin in coin_list:
                buy_check[coin] = 0
            
            for ind, coin in enumerate(coin_shortlist):
                units = get_balance(coin)
                if units > 0.00000001:
                    upbit.sell_market_order(coin_list[ind], units)
                    print(coin, ' 매도했음ㅋ_ㅋ')
                time.sleep(0.3)
            
            my_balance = upbit.get_balance("KRW")
            print('현재잔고: ', my_balance)
        time.sleep(1)
    
    except Exception as e:
        print(e)
        time.sleep(1)
