# IDEAS
# Support/resistance levels
# Delta 
# RSI (Oversold/Overbought + Direction)
# 50/200MA crossover
# Sell put when IV is 1 standard deviation away and when min return is satisfied (ex. 20% annual)

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
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        # loop through all rows in the excel data file
        open_data = {}
        for row in csv_reader:
            # skip first row with column headers
            if row[0] == 'Date':
                continue
            else:
                if datetime.datetime.strptime(row[0], '%Y-%m-%d') >= start_date and datetime.datetime.strptime(row[0], '%Y-%m-%d') <= end_date:
                    # key = date, value = open
                    key = datetime.datetime.strptime(row[0], '%Y-%m-%d')
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
                return option_list[i-1]
    
    print("ERROR: No option found")
    return option

def get_sigma(data, start_date, end_date):
    # list of daily returns
    daily_returns = get_daily_returns(data, start_date, end_date)
    # get the standard deviation of daily returns for the time period
    sigma = stdev(daily_returns) * math.sqrt(252)
    return sigma

def DualWheel(filename):
    
    shares = Share

    prev_price = 0
    portfolio_prev = 0

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime('2016-09-30', '%Y-%m-%d')
    end_date = datetime.datetime.strptime("2021-09-20", '%Y-%m-%d')

    # get all data at daily market open for start-end periods
    open_data = get_open_data(filename, start_date - datetime.timedelta(days=30), end_date)

    portfolio_beg = open_data[start_date]*2*100
    portfolio = portfolio_beg

    # desired contract length
    expiry_period = 30
    # contract width is the distance between strikes
    option_width = 1

    put_list = []
    call_list = []

    portfolio_returns = []
    underlying_returns = []

    for date in open_data:

        if date >= start_date and date <= end_date:

            # get stock price at day
            price = open_data[date]

            # risk free rate is bond price at date (/100 to put it into percent)
            rfr = get_price('^TNX.csv', date)/100

            # option range is how far to search for strikes
            # in this case we are searching until half the price
            option_range = int(price/2)

            # get strikes list
            strikes = get_strikes(price, option_range, option_width)
            
            # get sigma for time period
            sigma = get_sigma(open_data, date - datetime.timedelta(days=30), date)

            # get default option
            put_params = get_option(0, price, strikes[0], expiry_period, rfr, sigma, date)
            call_params = get_option(1, price, strikes[0], expiry_period, rfr, sigma, date)

            # Shares portfolio adjustment
            if shares.quantity > 0:
                portfolio_alloc = prev_price*shares.quantity/portfolio
                portfolio *= (1 + (price-prev_price)/prev_price*portfolio_alloc)

            # Put expiry adjustment
            for put in put_list:
                if date >= put.entry_date + datetime.timedelta(days=expiry_period):
                    if price < put.strike:
                        shares.quantity += 100
                        shares.cost_avg = (shares.cost_avg*100 + put.strike*100)/shares.quantity
                        portfolio += (price - put.strike)*100
                    put_list.remove(put)

            # Call expiry adjustment
            for call in call_list:
                if date >= call.entry_date + datetime.timedelta(days=expiry_period):
                    if price > call.strike:
                        portfolio += (call.strike - price)*100
                        shares.quantity -= 100
                    call_list.remove(call)

            if len(put_list) == 0 and shares.quantity < 200:
                put_atm = get_option_by_delta(put_params, strikes, 0.5)
                put_list.append(put_atm)
                portfolio += put_atm.price*100
                print("PUT SLD", put_atm.price, put_atm.strike, put_atm.delta)

            if len(put_list) == 1 and shares.quantity < 100:
                if put_list[0].delta < 0.3:
                    put_atm = get_option_by_delta(put_params, strikes, 0.5)
                    put_list.append(put_atm)
                    portfolio += put_atm.price*100
                    print("PUT SLD", put_atm.price, put_atm.strike, put_atm.delta)  
                else:
                    put_otm = get_option_by_delta(put_params, strikes, 0.2)
                    put_list.append(put_otm)
                    portfolio += put_otm.price*100
                    print("PUT SLD", put_otm.price, put_otm.strike, put_otm.delta)

            if len(call_list) == 0 and shares.quantity >= 100:
                call_atm = get_option_by_delta(call_params, strikes, 0.5)
                call_list.append(call_atm)
                portfolio += call_atm.price*100
                print("CALL SLD", call_atm.price, call_atm.strike, call_atm.delta)

            if len(call_list) == 1 and shares.quantity >= 200:
                call_otm = get_option_by_delta(call_params, strikes, 0.2)
                call_list.append(call_otm)
                portfolio += call_otm.price*100
                print("CALL SLD", call_otm.underlying, call_otm.price, call_otm.strike, call_otm.delta)

            if prev_price != 0 and portfolio_prev != 0:
                underlying_returns.append((price-prev_price)/prev_price)
                portfolio_returns.append((portfolio-portfolio_prev)/portfolio_prev)

            prev_price = price
            portfolio_prev = portfolio

            print(date, portfolio)

    underlying_start = open_data[start_date]
    underlying_end = open_data[end_date]
        
    print("Return", (portfolio/portfolio_beg-1)*100)
    print("Portfolio std", stdev(portfolio_returns) * math.sqrt(252) * 100)
    print("Underlying", (underlying_end/underlying_start-1)*100)
    print("Underlying std", stdev(underlying_returns) * math.sqrt(252) * 100)

def main():
    DualWheel('NCLH.csv')
    # print(get_option_price("call", 27.41, 18, 844, 0.0147, 0.557))

if __name__ == "__main__":
    main()