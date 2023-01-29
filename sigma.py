# NOTES
# Position amount based on deviation from 


import csv
import statistics
import datetime
import math
from statistics import NormalDist
from dataclasses import dataclass
import string
import matplotlib.pyplot as plt

@dataclass
class Option:
    type:bool
    ticker:string
    underlying_price:float
    strike:float
    time:int
    rfr:float
    sigma:float
    entry_date:datetime
    delta:float = 0.5
    price:float = 0
    quantity:float = 1

# sp = stock price at expiry, strike = option strike at entry, premium = option price at entry, quantity = number of options purchased
def short_put_calc(sp, strike, premium, quantity):
    result = 0
    if sp < strike: # Stock price went below strike
        result = (sp - strike + premium)*100
    else: # Stock price stayed above strike
        result = premium*100
    return round(float(result*quantity), 2)

# sp = stock price at expiry, strike = option strike at entry, premium = option price at entry
def short_call_calc(sp, strike, premium, quantity):
    result = 0
    if sp > strike:
        result = (strike - sp + premium)*100
    else:
        result = premium*100
    return round(float(result*quantity), 2)

# sp = stock price at expiry, strike = option strike at entry, premium = option price at entry
def long_put_calc(sp, strike, premium, quantity):
    result = 0
    if sp < strike:
        result = (strike - sp - premium)*100
    else:
        result = -premium*100
    return round(float(result*quantity), 2)

# sp = stock price at expiry, strike = option strike at entry, premium = option price at entry
def long_call_calc(sp, strike, premium, quantity):
    result = 0
    if sp > strike:
        result = (sp - strike - premium)*100
    else:
        result = -premium*100
    return round(float(result*quantity), 2)

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

# returns a list of available strike prices
def get_strikes(price, _range, _width):
    strikes = []
    # search the available strikes
    for i in range(_range*2+1):
        strikes.append(int(price - _range*_width + i*_width))
    return strikes

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

# Parameters: type(bool): option type (call = 1/put = 0), underlying(float): stock price, 
# strike(int): option strike, time(int): time left to option expiry, 
# rfr(float): risk free rate (US treasury 10yr), sigma(float) stdev of returns for time period, 
# mean(float): average return for time period
def get_option(type, ticker, underlying_price, strike, time, rfr, sigma, entry_date, quantity): 

    option = Option(type, ticker, underlying_price, strike, time, rfr, sigma, entry_date)
    option_price = 0
    option.quantity = quantity

    # time is annualized
    time = float(time/364)
    # ln(So/K)
    ln = math.log(underlying_price/strike)

    # (r+σ2/2)t
    r = (rfr + (math.pow(sigma, 2)) / 2) * time

    # σ√t
    s = sigma * math.sqrt(time)

    # d1
    d1 = (ln + r)/s

    # d2
    d2 = -(s - d1)

    # e-rt
    e = math.pow(math.e, -rfr*time)

    # N(d1)
    nd1_pos = NormalDist().cdf(d1)
    # N(d2)
    nd2_pos = NormalDist().cdf(d2)
    # N(d1)
    nd1_neg = NormalDist().cdf(-d1)
    # N(d2)
    nd2_neg = NormalDist().cdf(-d2)

    if type == True:
        option_price = (underlying_price*nd1_pos) - (strike*e*nd2_pos)
        option.delta = nd1_pos

    elif type == False:
        option_price = strike*e*nd2_neg - underlying_price*nd1_neg
        option.delta = nd1_neg

    else:
        print("ERROR: No option type specified")

    option.price = option_price

    return option

def sigma(ticker1, ticker2, start, end):

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')

    # get .csv files for tickers
    filename1 = ticker1 + ".csv"
    filename2 = ticker2 + ".csv"

    # get all data at daily market open for start-end periods
    stock_data1 = get_open_data(filename1, start_date - datetime.timedelta(days=30), end_date)
    stock_data2 = get_open_data(filename2, start_date - datetime.timedelta(days=30), end_date)
    rfr_data = get_open_data('^TNX.csv', start_date - datetime.timedelta(days=30), end_date)

    # desired contract length
    expiry_period = 30
    # contract width is the distance between strikes
    option_width = 1

    returns_sp = []
    returns_sc = []
    returns_lp = []
    returns_lc = []

    short_put = Option
    short_call = Option
    long_put = Option
    long_call = Option

    rfr_last = 0

    sigma_list_1 = []
    sigma_list_2 = []
    sigma_list_avg = []

    for (date1, price1), (date2, price2) in zip(stock_data1.items(), stock_data2.items()):

        if date1 >= start_date and date1 <= end_date:

            # Both have same date
            date = date1

            try:
                rfr = rfr_data[date]/100
            except KeyError:
                rfr = rfr_last
            
            rfr_last = rfr

            # check for option expiry (all options will have same expiry)
            if short_put.price != 0:

                if date >= short_put.entry_date + datetime.timedelta(days=expiry_period):
                    # Short put profit calculation
                    # print(price1, price2)
                    if short_put.ticker == ticker1: # For ticker 1
                        returns_sp.append(short_put_calc(price1, short_put.strike, short_put.price, short_put.quantity))
                        # print("short put", round(short_put_calc(price1, short_put.strike, short_put.price, short_put.quantity),2))
                    else: # For ticker 2
                        returns_sp.append(short_put_calc(price2, short_put.strike, short_put.price, short_put.quantity))
                        # print("short put", round(short_put_calc(price2, short_put.strike, short_put.price, short_put.quantity),2))
                    short_put.price = 0

                    if short_call.ticker == ticker1:
                        returns_sc.append(short_call_calc(price1, short_call.strike, short_call.price, short_call.quantity))
                        # print("short call", round(short_call_calc(price1, short_call.strike, short_call.price, short_call.quantity),2))
                    else:
                        returns_sc.append(short_call_calc(price2, short_call.strike, short_call.price, short_call.quantity))
                        # print("short call", round(short_call_calc(price2, short_call.strike, short_call.price, short_call.quantity),2))

                    if long_put.ticker == ticker1:
                        returns_lp.append(long_put_calc(price1, long_put.strike, long_put.price, long_put.quantity))
                        # print("long put", round(long_put_calc(price1, long_put.strike, long_put.price, long_put.quantity),2))
                    else:
                        returns_lp.append(long_put_calc(price2, long_put.strike, long_put.price, long_put.quantity))
                        # print("long put", round(long_put_calc(price2, long_put.strike, long_put.price, long_put.quantity),2))

                    if long_call.ticker == ticker1:
                        returns_lc.append(long_call_calc(price1, long_call.strike, long_call.price, long_call.quantity))
                        # print("long call", round(long_call_calc(price1, long_call.strike, long_call.price, long_call.quantity),2))
                    else:
                        returns_lc.append(long_call_calc(price2, long_call.strike, long_call.price, long_call.quantity))
                    #     print("long call", round(long_call_calc(price2, long_call.strike, long_call.price, long_call.quantity),2))
                    # print()

            # Only enter contract if difference in IV is greater than 2%
            if short_put.price == 0:
                # get sigma for time period
                sigma1_30 = get_sigma(stock_data1, date - datetime.timedelta(days=30), date)

                sigma2_30 = get_sigma(stock_data2, date - datetime.timedelta(days=30), date)

                # sigma_list_1.append(sigma1_30)
                # sigma_list_2.append(sigma2_30)
                # sigma_list_avg.append((sigma1_30+sigma2_30)/2)

                # difference in 30 day sigma
                sigma_d = sigma1_30 - sigma2_30

                if abs(sigma_d) >= 0.02:
                    # set option quantities so exposure is close to even as possible
                    quantity1 = 1
                    quantity2 = 1
                    if (price1 > price2):
                        quantity2 = round(price1/price2,2)
                    else:
                        quantity1 = round(price2/price1,2)

                    if sigma1_30 > sigma2_30:
                        # print("short", ticker1, "long", ticker2)
                        short_call = get_option(1, ticker1, price1, round(price1,2), expiry_period, rfr, sigma1_30, date, quantity1)
                        short_put = get_option(0, ticker1, price1, round(price1,2), expiry_period, rfr, sigma1_30, date, quantity1)
                        long_call = get_option(1, ticker2, price2, round(price2,2), expiry_period, rfr, sigma1_30, date, quantity2)
                        long_put = get_option(0, ticker2, price2, round(price2,2), expiry_period, rfr, sigma1_30, date, quantity2)

                        # print(date, "PEP", round(price1,2), round(sigma1_30,2), round(short_call.price*short_call.quantity,2), round(short_put.price*short_put.quantity,2))
                        # print(date, "KO", round(price2,2), round(sigma2_30,2), round(long_call.price*long_call.quantity,2), round(long_put.price*long_put.quantity,2))
                        # print()

                        # print(date, "short_call", \
                        #             "\n\tticker", short_call.ticker, \
                        #             "\n\tunderlying_price", short_call.underlying_price, \
                        #             "\n\tstrike", short_call.strike, \
                        #             "\n\tsigma", short_call.sigma, \
                        #             "\n\tentry_date", short_call.entry_date, \
                        #             "\n\tdelta", short_call.delta, \
                        #             "\n\tprice", short_call.price)
                        # print(date, "short_put", \
                        #             "\n\tticker", short_put.ticker, \
                        #             "\n\tunderlying_price", short_put.underlying_price, \
                        #             "\n\tstrike", short_put.strike, \
                        #             "\n\tsigma", short_put.sigma, \
                        #             "\n\tentry_date", short_put.entry_date, \
                        #             "\n\tdelta", short_put.delta, \
                        #             "\n\tprice", short_put.price)
                        # print(date, "long_call", \
                        #             "\n\tticker", long_call.ticker, \
                        #             "\n\tunderlying_price", long_call.underlying_price, \
                        #             "\n\tstrike", long_call.strike, \
                        #             "\n\tsigma", long_call.sigma, \
                        #             "\n\tentry_date", long_call.entry_date, \
                        #             "\n\tdelta", long_call.delta, \
                        #             "\n\tprice", long_call.price)
                        # print(date, "long_put", \
                        #             "\n\tticker", long_put.ticker, \
                        #             "\n\tunderlying_price", long_put.underlying_price, \
                        #             "\n\tstrike", long_put.strike, \
                        #             "\n\tsigma", long_put.sigma, \
                        #             "\n\tentry_date", long_put.entry_date, \
                        #             "\n\tdelta", long_put.delta, \
                        #             "\n\tprice", long_put.price, "\n")
                                        
                    else:
                        # print("long", ticker1, "short", ticker2)
                        long_call = get_option(1, ticker1, price1, round(price1,2), expiry_period, rfr, sigma1_30, date, quantity1)
                        long_put = get_option(0, ticker1, price1, round(price1,2), expiry_period, rfr, sigma1_30, date, quantity1)
                        short_call = get_option(1, ticker2, price2, round(price2,2), expiry_period, rfr, sigma1_30, date, quantity2)
                        short_put = get_option(0, ticker2, price2, round(price2,2), expiry_period, rfr, sigma1_30, date, quantity2)

                        # print(date, "PEP", round(price1,2), round(sigma1_30,2), round(long_call.price*long_call.quantity,2), round(long_put.price*long_put.quantity,2))
                        # print(date, "KO", round(price2,2), round(sigma2_30,2), round(short_call.price*short_call.quantity,2), round(short_put.price*short_put.quantity,2))
                        # print()

                        # print(date, "short_call", \
                        #             "\n\tticker", short_call.ticker, \
                        #             "\n\tunderlying_price", short_call.underlying_price, \
                        #             "\n\tstrike", short_call.strike, \
                        #             "\n\tsigma", short_call.sigma, \
                        #             "\n\tentry_date", short_call.entry_date, \
                        #             "\n\tdelta", short_call.delta, \
                        #             "\n\tprice", short_call.price)
                        # print(date, "short_put", \
                        #             "\n\tticker", short_put.ticker, \
                        #             "\n\tunderlying_price", short_put.underlying_price, \
                        #             "\n\tstrike", short_put.strike, \
                        #             "\n\tsigma", short_put.sigma, \
                        #             "\n\tentry_date", short_put.entry_date, \
                        #             "\n\tdelta", short_put.delta, \
                        #             "\n\tprice", short_put.price)
                        # print(date, "long_call", \
                        #             "\n\tticker", long_call.ticker, \
                        #             "\n\tunderlying_price", long_call.underlying_price, \
                        #             "\n\tstrike", long_call.strike, \
                        #             "\n\tsigma", long_call.sigma, \
                        #             "\n\tentry_date", long_call.entry_date, \
                        #             "\n\tdelta", long_call.delta, \
                        #             "\n\tprice", long_call.price)
                        # print(date, "long_put", \
                        #             "\n\tticker", long_put.ticker, \
                        #             "\n\tunderlying_price", long_put.underlying_price, \
                        #             "\n\tstrike", long_put.strike, \
                        #             "\n\tsigma", long_put.sigma, \
                        #             "\n\tentry_date", long_put.entry_date, \
                        #             "\n\tdelta", long_put.delta, \
                        #             "\n\tprice", long_put.price, "\n")
            else:
                # print(date, "No Sigma Difference Significance (Sigma Difference < 2) sigma_d =", sigma_d) 
                continue
    
    # print(returns_sp)
    # print(returns_sc)
    # print(returns_lp)
    # print(returns_lc)

    returns_sum = []

    for i in range(0, len(returns_sp), 1):
        returns_sum.append(returns_sp[i]+returns_sc[i]+returns_lp[i]+returns_lc[i])

    # for i in returns_sum:
    #     print(i)

    print(sum(returns_sum))

    # plt.plot(returns_sp, label= "Short Puts")
    # plt.plot(returns_sc, label="Short Calls")
    # plt.plot(returns_lp, label="Long Puts")
    # plt.plot(returns_lc, label="Long Calls")
    plt.plot(returns_sum, label="Sum")
    # plt.plot(sigma_list_1, label="Sigma1")
    # plt.plot(sigma_list_2, label="Sigma2")
    # plt.plot(sigma_list_avg, label="Sigma avg")
    plt.legend(loc='lower center')
    plt.show()

def main():
    sigma('PEP', 'KO', '2020-10-05', '2021-10-20')
    
if __name__ == "__main__":
    main()