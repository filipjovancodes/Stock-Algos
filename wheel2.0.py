# IDEAS
# Support/resistance levels
# Delta 
# RSI (Oversold/Overbought + Direction)
# 50/200MA crossover
# Sell put when IV is 1 standard deviation away and when min return is satisfied (ex. 20% annual)
# Delta adjustment based on IV

import csv
import statistics
import datetime
import math
from statistics import NormalDist
from dataclasses import dataclass

@dataclass
class Option:
    type:bool
    underlying:float
    strike:float
    time:int
    rfr:float
    sigma:float
    entry_date:datetime
    delta:float = 0.5
    price:float = 0

@dataclass
class Share:
    cost_avg:float = 0
    quantity:int = 0

# returns standard deviation within number array
def stdev(arr):
    return statistics.stdev(arr)

# returns price for a date in a given file
def get_price(filename, date):
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if row[0] == 'Date':
                continue
            if datetime.datetime.strptime(row[0], '%Y-%m-%d') >= date and row[1] != 'null':
                return float(row[1])
    # if here then error
    print("ERROR: No risk free rate found -> check if ^TNX.csv is up to date")
    
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
def get_option(type, underlying_price, strike, time, rfr, sigma, entry_date): 

    option = Option(type, underlying_price, strike, time, rfr, sigma, entry_date)
    option_price = 0

    # time is annualized
    time = float(time/364)
    # ln(So/K)
    ln = -math.log(strike/underlying_price)
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

    if type == True:
        # N(d1)
        nd1 = NormalDist().cdf(d1)
        # N(d2)
        nd2 = NormalDist().cdf(d2)

        option_price = underlying_price*nd1 - strike*e*nd2

    elif type == False:
        # N(d1)
        nd1 = NormalDist().cdf(-d1)
        # N(d2)
        nd2 = NormalDist().cdf(-d2)

        option_price = strike*e*nd2 - underlying_price*nd1

    else:
        print("ERROR: No option type specified")

    option.delta = nd1
    option.price = option_price

    return option

# returns the option closest to the specified delta
def get_option_by_delta(option, strikes, delta):
    option_list = []

    # Loop through the strikes getting options for each
    for i in range(0, len(strikes), 1):
        option = get_option(option.type, option.underlying, strikes[i], option.time, option.rfr, option.sigma, option.entry_date)
        # option_list is organized by strike 
        option_list.append(option)

    for i in range(0, len(option_list), 1):
        # for put select option with delta lower than desired delta
        if option.type == 0:
            if delta < option_list[i].delta:
                return option_list[i-1]
        if option.type == 1:
            if delta > option_list[i].delta:
                return option_list[i]
    
    # print("ERROR: No option found")
    return option

def get_sigma(data, start_date, end_date):
    # list of daily returns
    daily_returns = get_daily_returns(data, start_date, end_date)
    # get the standard deviation of daily returns for the time period
    sigma = stdev(daily_returns) * math.sqrt(252)
    return sigma

def DualWheel(filename, start, end):
    
    shares = Share

    prev_price = 0
    portfolio_prev = 0

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')

    # get all data at daily market open for start-end periods
    stock_data = get_open_data(filename, start_date - datetime.timedelta(days=30), end_date)
    rfr_data = get_open_data('^TNX.csv', start_date - datetime.timedelta(days=30), end_date)
    vix_data = get_open_data('^VIX.csv', start_date - datetime.timedelta(days=30), end_date)

    try:
        portfolio_beg = stock_data[start_date]*2*100
        portfolio = portfolio_beg
    except KeyError:
        print(filename, "skipped")
        return

    # desired contract length
    expiry_period = 30
    # contract width is the distance between strikes
    option_width = 1

    put_list = []
    call_list = []

    portfolio_returns = []
    underlying_returns = []

    port_ret = 0
    under_ret = 0

    underlying_start = stock_data[start_date]
    underlying_end = stock_data[end_date]

    sigma_list = []

    rfr_last = 0

    for date, price in stock_data.items():

        if date >= start_date and date <= end_date:

            # risk free rate is bond price at date (/100 to put it into percent)
            try:
                rfr = rfr_data[date]/100

            except KeyError:
                rfr = rfr_last

            # volatility index
            # vix = vix_data[date]

            # option range is how far to search for strikes
            # in this case we are searching until half the price
            option_range = int(price/2)

            # get strikes list
            strikes = get_strikes(price, option_range, option_width)
            
            # get sigma for time period
            sigma = get_sigma(stock_data, date - datetime.timedelta(days=30), date)

            # get default option
            put_params = get_option(0, price, strikes[0], expiry_period, rfr, sigma, date)
            call_params = get_option(1, price, strikes[0], expiry_period, rfr, sigma, date)

            # Shares portfolio adjustment
            if shares.quantity > 0 and prev_price > 0:
                portfolio_alloc = prev_price*shares.quantity/portfolio
                portfolio *= (1 + (price-prev_price)/prev_price*portfolio_alloc)

            # Put expiry adjustment
            for put in put_list:
                if date >= put.entry_date + datetime.timedelta(days=expiry_period):
                    if price < put.strike:
                        shares.quantity += 100
                        shares.cost_avg = shares.cost_avg*(shares.quantity-100)/shares.quantity + put.strike*100/shares.quantity
                        portfolio += (price - put.strike)*100
                    put_list.remove(put)

            # Call expiry adjustment
            for call in call_list:
                if date >= call.entry_date + datetime.timedelta(days=expiry_period):
                    if price > call.strike:
                        portfolio += (call.strike - price)*100
                        shares.quantity -= 100
                    call_list.remove(call)

            # Sell 50 delta, then 20 delta, then 50 delta, etc. depending on shares quantity
            while len(call_list) < int(shares.quantity/100):
                if len(call_list) == 0:
                    call = get_option_by_delta(call_params, strikes, 0.5)
                elif len(call_list) % 2 == 0 or call_list[0].delta < 0.3:
                    call = get_option_by_delta(call_params, strikes, 0.5)
                else:
                    call = get_option_by_delta(call_params, strikes, 0.2)
                call_list.append(call)
                portfolio += call.price*100
                # print(date, "CALL SLD", price, call.price, call.strike, call.delta)
            
            port = min(port_ret*portfolio_beg, under_ret*portfolio_beg)
            # Sell 50 delta, then 20 delta, then 50 delta, etc. depending on cash available
            while (len(put_list) < int(port/100/price) - int(shares.quantity/100)) or (len(call_list) == 0 and len(put_list) < 2) or (len(call_list) == 1 and int(shares.quantity/100) == 1 and len(put_list) == 0):
                if len(put_list) == 0:
                    put = get_option_by_delta(put_params, strikes, 0.5)
                elif len(put_list) % 2 == 0 or put_list[0].delta < 0.3:
                    put = get_option_by_delta(put_params, strikes, 0.5)
                else:
                    put = get_option_by_delta(put_params, strikes, 0.2)
                put_list.append(put)
                portfolio += put.price*100
                # print(date, "PUT SLD", price, put.price, put.strike, put.delta)

            # buy shares with excess capital
            if portfolio > 200*price and (int(portfolio/price) % 100) - (shares.quantity % 100) >= 2:
                # print(date, "PURCHASED", (int(portfolio/price) % 100) - (shares.quantity % 100), "SHARES AT SHARE PRICE OF", price, "WHILE PORTFOLIO TOTAL IS", portfolio)
                shares.quantity += (int(portfolio/price) % 100) - (shares.quantity % 100)

            if prev_price != 0 and portfolio_prev != 0:
                underlying_returns.append((price-prev_price)/prev_price)
                portfolio_returns.append((portfolio-portfolio_prev)/portfolio_prev)

            prev_price = price
            portfolio_prev = portfolio

            # print(date, portfolio)

            port_ret = (portfolio-portfolio_beg)/portfolio_beg
            under_ret = (underlying_start-price)/underlying_start

            sigma_list.append(sigma)

            rfr_last = rfr
    
    print(filename)
    print("\tReturn", round((portfolio/portfolio_beg-1)*100,2))
    print("\tPortfolio std", round(stdev(portfolio_returns) * math.sqrt(252) * 100,2))
    print("\tCAGR", round((portfolio/portfolio_beg-1)*100/abs((end_date - start_date).days)*364,2))
    print("\tUnderlying", round((underlying_end/underlying_start-1)*100,2))
    print("\tUnderlying std", round(stdev(underlying_returns) * math.sqrt(252) * 100,2))
    print("\tCAGR", round((underlying_end/underlying_start-1)*100/abs((end_date - start_date).days)*364,2))
    print("\tAVG Sigma",round(sum(sigma_list)/len(sigma_list)*100,2))

def main():
    # stock_list = ['AAL.csv','AAPL.csv','AMD.csv','GOLD.csv','KO.csv','CCL.csv','SPY.csv','HD.csv','CAG.csv','QQQ.csv','ABT.csv','KL.csv','MU.csv','CGX.TO.csv']
    stock_list = ['KO.csv','IBM.csv','SJM.csv','CCL.csv','SPY.csv','FE.csv','GIS.csv']
    for stock in stock_list:
        DualWheel(stock,'2003-01-06','2021-09-20')
    # print(get_option_price("call", 27.41, 18, 844, 0.0147, 0.557))

if __name__ == "__main__":
    main()