# NOTES
# Test real trades
# Find for more correlated assets

# curr 0.2 avg 0.3

import csv
import statistics
import datetime
import math
from statistics import NormalDist
from dataclasses import dataclass
import matplotlib.pyplot as plt
import string

class Trade():
    type = False
    sigma = 0
    expiry_date = 0
    weight = 0

    def __init__(self):
        pass

class Straddle():
    type:bool # short = 0, long = 1
    ticker:string # underlying ticker symbol
    underlying_price:float # underlying price at entry
    strike:float # strike to enter straddle
    time:int # time to expiry
    rfr:float # risk free rate
    sigma:float # IV at entry
    entry_date:datetime # entry date
    price:float = 0 # price of option at entry
    quantity:float = 1 # quantity entered

    def __init__(self):
        pass

# Parameters: type(bool): option type (call = 1/put = 0), underlying(float): stock price, 
# strike(int): option strike, time(int): time left to option expiry, 
# rfr(float): risk free rate (US treasury 10yr), sigma(float) stdev of returns for time period, 
# mean(float): average return for time period
def get_straddle(type, ticker, underlying_price, strike, time, rfr, sigma, entry_date, quantity):
    # OPTION Initialization
    a = Straddle()
    straddle = a.__class__

    option = straddle()
    option.type = type
    option.ticker = ticker
    option.underlying_price = underlying_price
    option.strike = strike
    option.time = time
    option.rfr = rfr
    option.sigma = sigma
    option.entry_date = entry_date

    option_price = 0
    option.quantity = quantity
    time = float(time/364) # time is annualized
    ln = math.log(underlying_price/strike) # ln(So/K)
    r = (rfr + (math.pow(sigma, 2)) / 2) * time # (r+σ2/2)t
    s = sigma * math.sqrt(time) # σ√t
    d1 = (ln + r)/s # d1
    d2 = -(s - d1) # d2
    e = math.pow(math.e, -rfr*time) # e-rt
    nd1_pos = NormalDist().cdf(d1) # N(d1)
    nd2_pos = NormalDist().cdf(d2) # N(d2)
    nd1_neg = NormalDist().cdf(-d1) # N(d1)
    nd2_neg = NormalDist().cdf(-d2) # N(d2)
    if type == 1: # call cals
        option_price = (underlying_price*nd1_pos) - (strike*e*nd2_pos)
        option.delta = nd1_pos
    elif type == 0: # put calcs
        option_price = strike*e*nd2_neg - underlying_price*nd1_neg
        option.delta = nd1_neg
    else:
        print("ERROR: Option type invalid")
    option.price = option_price*2

    return option

# returns standard deviation within number array
def stdev(arr):
    return statistics.stdev(arr)

# returns array with all %daily returns from start date to end date within data object
def get_daily_returns(data, start_date, end_date):
    count = 0
    # previous close placeholder
    returns = []
    prev = -1
    for key, value in data.items():
        if key >= start_date and key <= end_date:
            # first iteration
            if prev == -1:
                prev = value
            else:
                # append returns to daily returns array
                returns.append(value/prev-1)
                prev = value
    return returns 

def get_sigma(data, start_date, end_date):
    # list of daily returns
    daily_returns = get_daily_returns(data, start_date, end_date)
    # get the standard deviation of daily returns for the time period
    sigma = stdev(daily_returns) * math.sqrt(252)
    return sigma

def get_sigma_average(list, days):
    sum = 0
    rlist = list
    rlist.reverse()
    for i in range(0, days, 1):
        sum += rlist[i]
    return sum/days

# type = short/long position, st = short term volatility, lt = long term average volatility
# st = 0.4, lt = 0.3
# 0.4/
def weight_alloc(type, st, lt):
    # allocating weights by taking current volatility vs 90 day average
    if type == 0: # short pos 
        if st > lt:   
            if (st-lt)/lt > 1:
                return 0.5      
            return (st-lt)/lt/2
        else:
            if (lt-st)/lt > 1:
                return 0
            return (lt-st)/lt/2
    if type == 1: # long pos
        if st > lt:
            if (st-lt)/lt > 1:
                return 0
            return (lt-st)/lt/2
        else:
            if (lt-st)/lt > 1:
                return 0.5
            return (lt-st)/lt/2

def get_open_data(filename, start_date, end_date):
    placeholder = 0
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        # loop through all rows in the excel data file
        open_data = {}
        for row in csv_reader:
            # skip first row with column headers
            if row[0] == 'Date':
                continue
            else:
                if row[1] != 'null':
                    placeholder = row[1]
                if datetime.datetime.strptime(row[0], '%Y-%m-%d') >= start_date and datetime.datetime.strptime(row[0], '%Y-%m-%d') <= end_date:
                    # key = date, value = open
                    key = datetime.datetime.strptime(row[0], '%Y-%m-%d')
                    if row[1] == 'null':
                        open_data[key] = float(placeholder)
                    else:
                        open_data[key] = float(row[1])
    return open_data

def sigma(ticker1, ticker2, start, end):

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')

    # get .csv files for tickers
    filename1 = ticker1 + ".csv"
    filename2 = ticker2 + ".csv"

    # get all data at daily market open for start-end periods
    stock_data1 = get_open_data(filename1, start_date - datetime.timedelta(days=240), end_date)
    stock_data2 = get_open_data(filename2, start_date - datetime.timedelta(days=240), end_date)

    actual_sigma_list_PEP = {}
    actual_sigma_list_KO = {}
    
    trade_list_PEP = {}
    trade_list_KO = {}

    sigma_list_PEP = []
    sigma_list_KO = []

    straddle_list_PEP = {}
    straddle_list_KO = {}

    actual_price_list_PEP = {}
    actual_price_list_KO = {}

    future_trade_list_PEP = {}
    future_trade_list_KO = {}

    for (date1, pricePEP), (date2, priceKO) in zip(stock_data1.items(), stock_data2.items()):

        # warmup sigma average
        if date1 >= start_date - datetime.timedelta(days=160) and date1 < start_date:
            date = date1

            sigma_PEP_30 = get_sigma(stock_data1, date - datetime.timedelta(days=30), date)
            sigma_KO_30 = get_sigma(stock_data2, date - datetime.timedelta(days=30), date)
            
            sigma_list_PEP.append(sigma_PEP_30)
            sigma_list_KO.append(sigma_KO_30)

        if date1 >= start_date and date1 <= end_date:

            # Both have same date
            date = date1

            # get sigma for time period

            sigma_PEP_90_avg = get_sigma_average(sigma_list_PEP, 90)
            sigma_KO_90_avg = get_sigma_average(sigma_list_KO, 90)
            sigma_avg = (sigma_PEP_90_avg+sigma_KO_90_avg)/2

            sigma_PEP_30 = get_sigma(stock_data1, date - datetime.timedelta(days=30), date)
            sigma_KO_30 = get_sigma(stock_data2, date - datetime.timedelta(days=30), date)

            # sigma_list_1.append(sigma1_30)
            # sigma_list_2.append(sigma2_30)
            # sigma_list_avg.append((sigma1_30+sigma2_30)/2)

            # difference in 30 day sigma
            sigma_d = sigma_PEP_30 - sigma_KO_30

            if abs(sigma_d) >= 0.02:

                # TRADE initialization

                a = Trade()
                b = Trade()

                tradea = a.__class__
                tradeb = b.__class__

                tradePEP = tradea()
                tradeKO = tradeb()
                    
                tradePEP.sigma = sigma_PEP_30
                tradeKO.sigma = sigma_KO_30

                result = date + datetime.timedelta(days = 30)
                
                while(True and not result > end_date):
                    try:
                        stock_data1[result]
                        tradePEP.expiry_date = result
                        tradeKO.expiry_date = result
                        break
                    except KeyError:
                        result = result + datetime.timedelta(days = 1)

                # short/long allocation based on which asset is higher volatility -> INVERSED
                if sigma_PEP_30 > sigma_KO_30: 
                    tradePEP.type = 0
                    straddlePEP = get_straddle(0, ticker1, pricePEP, pricePEP, 30, 0.01, sigma_PEP_30, date, 1)
                    tradePEP.weight = weight_alloc(0, sigma_PEP_30, sigma_avg)
                    tradeKO.type = 1
                    straddleKO = get_straddle(1, ticker2, priceKO, priceKO, 30, 0.01, sigma_KO_30, date, pricePEP / priceKO)  
                    tradeKO.weight = weight_alloc(1, sigma_KO_30, sigma_avg)
                else:
                    tradePEP.type = 1
                    straddlePEP = get_straddle(1, ticker1, pricePEP, pricePEP, 30, 0.01, sigma_PEP_30, date, 1)
                    tradePEP.weight = weight_alloc(1, sigma_PEP_30, sigma_avg)
                    tradeKO.type = 0
                    straddleKO = get_straddle(0, ticker2, priceKO, priceKO, 30, 0.01, sigma_KO_30, date, pricePEP / priceKO)  
                    tradeKO.weight = weight_alloc(0, sigma_KO_30, sigma_avg)

                if not result > end_date - datetime.timedelta(days = 30):
                    trade_list_PEP[result] = tradePEP
                    trade_list_KO[result] = tradeKO

                    straddle_list_PEP[result] = straddlePEP
                    straddle_list_KO[result] = straddleKO
                else:
                    exp = date + datetime.timedelta(days = 30)

                    tradePEP.expiry_date = exp
                    tradeKO.expiry_date = exp

                    future_trade_list_PEP[date] = tradePEP
                    future_trade_list_KO[date] = tradeKO

                    straddle_list_PEP[date] = straddlePEP
                    straddle_list_KO[date] = straddleKO

            actual_sigma_list_PEP[date] = sigma_PEP_30
            actual_sigma_list_KO[date] = sigma_KO_30

            actual_price_list_PEP[date] = pricePEP
            actual_price_list_KO[date] = priceKO

            sigma_list_PEP.append(sigma_PEP_30)
            sigma_list_KO.append(sigma_KO_30)

    PEP_IV_profits = []
    KO_IV_profits = []

    PEP_Straddle_profits = []
    KO_Straddle_profits = []

    price_PEP = []
    price_KO = []

    sigma_PEP = []
    sigma_KO = []

    last_capital = 0

    for date in trade_list_PEP:
        # trade is a short
        if trade_list_PEP[date].type == 0:
            PEP_IV_profits.append(trade_list_PEP[date].sigma - actual_sigma_list_PEP[date])
            option_profit = (straddle_list_PEP[date].price - abs(actual_price_list_PEP[date] - straddle_list_PEP[date].strike))*100
            # hedge caps losses such that collateral is the price of entry into options (times 4 for 4 options) -> Note 4 times the most expensive option since the position should be adjusted to equal size
            if option_profit < -straddle_list_PEP[date].price*100:
                option_profit = -straddle_list_PEP[date].price*100
            PEP_Straddle_profits.append(option_profit)
            print("PEP", \
                "\ttype", trade_list_PEP[date].type, \
                "\tentry sigma", round(trade_list_PEP[date].sigma,2), \
                "\tresult", round(actual_sigma_list_PEP[date],2), \
                "\tweight", round(trade_list_PEP[date].weight,2), \
                "\tprofit", round(trade_list_PEP[date].sigma - actual_sigma_list_PEP[date], 2), \
                "\tsp entry", round(straddle_list_PEP[date].underlying_price, 1), \
                "\tsp close", round(actual_price_list_PEP[date], 1), \
                "\toption price", round(straddle_list_PEP[date].price, 1), \
                "\toption profit", round(option_profit, 1), \
                "\texpiry date", trade_list_PEP[date].expiry_date)
        else: # trade is a long
            PEP_IV_profits.append(actual_sigma_list_PEP[date] - trade_list_PEP[date].sigma)
            option_profit =  (abs(actual_price_list_PEP[date] - straddle_list_PEP[date].strike) - straddle_list_PEP[date].price)*100
            # pay for short hedge by selling otm strangle -> say this offsets the other hedge therefore just caps gains
            if option_profit > straddle_list_PEP[date].price*100:
                option_profit = straddle_list_PEP[date].price*100
            PEP_Straddle_profits.append(option_profit)
            print("PEP", \
                "\ttype", trade_list_PEP[date].type, \
                "\tentry sigma", round(trade_list_PEP[date].sigma,2), \
                "\tresult", round(actual_sigma_list_PEP[date],2), \
                "\tweight", round(trade_list_PEP[date].weight,2), \
                "\tprofit", round(actual_sigma_list_PEP[date] - trade_list_PEP[date].sigma, 2), \
                "\tsp entry", round(straddle_list_PEP[date].underlying_price, 1), \
                "\tsp close", round(actual_price_list_PEP[date], 1), \
                "\toption price", round(straddle_list_PEP[date].price, 1), \
                "\toption profit", round(option_profit, 1), \
                "\texpiry date", trade_list_PEP[date].expiry_date)
        # trade is a short
        if trade_list_KO[date].type == 0:
            KO_IV_profits.append(trade_list_KO[date].sigma - actual_sigma_list_KO[date])
            option_profit = (straddle_list_KO[date].price - abs(actual_price_list_KO[date] - straddle_list_KO[date].strike))*100 * straddle_list_KO[date].quantity
            # hedge caps losses such that collateral is the price of entry into options (times 4 for 4 options) -> Note 4 times the most expensive option since the position should be adjusted to equal size
            if option_profit < -straddle_list_KO[date].price*100 * straddle_list_KO[date].quantity:
                option_profit = -straddle_list_KO[date].price*100 * straddle_list_KO[date].quantity
            KO_Straddle_profits.append(option_profit)
            print("KO", \
                "\ttype", trade_list_KO[date].type, \
                "\tentry sigma", round(trade_list_KO[date].sigma,2), \
                "\tresult", round(actual_sigma_list_KO[date],2), \
                "\tweight", round(trade_list_KO[date].weight,2), \
                "\tprofit", round(trade_list_KO[date].sigma - actual_sigma_list_KO[date], 2), \
                "\tsp entry ", round(straddle_list_KO[date].underlying_price, 1), \
                "\tsp close ", round(actual_price_list_KO[date], 1), \
                "\toption price", round(straddle_list_KO[date].price, 1), \
                "\toption profit", round(option_profit, 1), \
                "\texpiry date", trade_list_KO[date].expiry_date)
        else: # trade is a long
            KO_IV_profits.append(actual_sigma_list_KO[date] - trade_list_KO[date].sigma)
            option_profit = (abs(actual_price_list_KO[date] - straddle_list_KO[date].strike) - straddle_list_KO[date].price)*100 * straddle_list_KO[date].quantity
            # pay for short hedge by selling otm strangle -> say this offsets the other hedge therefore just caps gains
            if option_profit > straddle_list_KO[date].price*100 * straddle_list_KO[date].quantity:
                option_profit = straddle_list_KO[date].price*100 * straddle_list_KO[date].quantity
            KO_Straddle_profits.append(option_profit)
            print("KO", \
                "\ttype", trade_list_KO[date].type, \
                "\tentry sigma", round(trade_list_KO[date].sigma,2), \
                "\tresult", round(actual_sigma_list_KO[date],2), \
                "\tweight", round(trade_list_KO[date].weight,2), \
                "\tprofit", round(actual_sigma_list_KO[date] - trade_list_KO[date].sigma, 2), \
                "\tsp entry ", round(straddle_list_KO[date].underlying_price, 1), \
                "\tsp close ", round(actual_price_list_KO[date], 1), \
                "\toption price", round(straddle_list_KO[date].price, 1), \
                "\toption profit", round(option_profit, 1), \
                "\texpiry date", trade_list_KO[date].expiry_date)
        print()
        print("Trade Collateral", round(straddle_list_PEP[date].price * 4 * 100,2), "Adjusted Monthly (Total Trade Collateral)", round(straddle_list_PEP[date].price * 4 * 21 * 100,2))
        print()
        last_capital = straddle_list_PEP[date].price * 4 * 21 * 100

        price_PEP.append( actual_price_list_PEP[date] )
        price_KO.append( actual_price_list_KO[date] )
        sigma_PEP.append( actual_sigma_list_PEP[date] )
        sigma_KO.append( actual_sigma_list_KO[date] )

    sums_IV = []
    sums_Straddle = []

    for i in range(0, len(PEP_IV_profits), 1):
        if len(sums_IV) > 0:
            sums_IV.append(PEP_IV_profits[i] + KO_IV_profits[i] + sums_IV[i-1])
            sums_Straddle.append(PEP_Straddle_profits[i] + KO_Straddle_profits[i] + sums_Straddle[i-1])
        else:
            sums_IV.append(PEP_IV_profits[i] + KO_IV_profits[i])
            sums_Straddle.append(PEP_Straddle_profits[i] + KO_Straddle_profits[i])

    # future trades output
    for date in future_trade_list_PEP:
        print("PEP", \
                "\tentry date", date, \
                "\ttype", future_trade_list_PEP[date].type, \
                "\tentry sigma", round(future_trade_list_PEP[date].sigma,2), \
                "\tweight", round(future_trade_list_PEP[date].weight,2), \
                "\tsp entry", round(straddle_list_PEP[date].underlying_price, 1), \
                "\toption price", round(straddle_list_PEP[date].price, 1), \
                "\texpiry date", future_trade_list_PEP[date].expiry_date)
        print("KO", \
                "\tentry date", date, \
                "\ttype", future_trade_list_KO[date].type, \
                "\tentry sigma", round(future_trade_list_KO[date].sigma,2), \
                "\tweight", round(future_trade_list_KO[date].weight,2), \
                "\tsp entry", round(straddle_list_KO[date].underlying_price, 1), \
                "\toption price", round(straddle_list_KO[date].price, 1), \
                "\texpiry date", future_trade_list_KO[date].expiry_date)
        print()

    # print(sum(PEP_IV_profits))
    # print(sum(KO_IV_profits))

    print("PEP staddle profits", round(sum(PEP_Straddle_profits),2))
    print("KO straddle profits", round(sum(KO_Straddle_profits),2))
    print("Straddles profits", round(sum(PEP_Straddle_profits) + sum(KO_Straddle_profits),2))
    print("Annual growth", round((sum(PEP_Straddle_profits) + sum(KO_Straddle_profits)) / (end_date - start_date).days * 252,2))
    print("CAGR", round(((sum(PEP_Straddle_profits) + sum(KO_Straddle_profits)) / (end_date - start_date).days * 252) / last_capital * 100,2), "%")
    print("STDEV of profits sum", round(stdev(sums_Straddle) / (end_date - start_date).days * 252 / last_capital * 100,2),"%")

    # plt.plot(PEP_profits, label="PEP_profits")
    # plt.plot(KO_profits, label="KO_profits")
    # plt.plot(sums_IV, label="IV return")
    # plt.plot(sums_Straddle, label="Straddle return")
    # plt.plot(price_PEP, label="PEP")
    # plt.plot(price_KO, label="KO")
    # plt.legend(loc='lower center')
    # plt.show()

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('time (d)')
    ax1.set_ylabel('Straddle Returns', color=color)
    ax1.plot(sums_Straddle, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('KO', color=color)  # we already handled the x-label with ax1
    ax2.plot(price_KO, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax3 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:green'
    ax3.set_ylabel('PEP', color=color)  # we already handled the x-label with ax1
    ax3.plot(price_PEP, color=color)
    ax3.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

def main():
    sigma('PEP', 'KO', '2021-05-23', '2021-10-05')
    
if __name__ == "__main__":
    main()