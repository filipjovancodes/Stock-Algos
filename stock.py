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
class Share1:
    cost_avg:float = 0
    quantity:int = 0

@dataclass
class Share2:
    cost_avg:float = 0
    quantity:int = 0

# returns standard deviation within number array
def stdev(arr):
    return statistics.stdev(arr)

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

def stock():
    
    portfolio_shares = Share1
    underlying_shares = Share2

    portfolio_shares.quantity += 1
    underlying_shares.quantity += 1

    prev_price = 0
    portfolio_prev = 0
    underlying_portfolio_prev = 0

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime('2016-01-05', '%Y-%m-%d')
    end_date = datetime.datetime.strptime("2021-09-20", '%Y-%m-%d')

    # get all data at daily market open for start-end periods
    spy_data = get_open_data('SPY.csv', start_date - datetime.timedelta(days=30), end_date)
    vix_data = get_open_data('^VIX.csv', start_date - datetime.timedelta(days=30), end_date)

    portfolio_beg = spy_data[start_date]*100
    portfolio = portfolio_beg
    underlying_portfolio = portfolio_beg

    portfolio_returns = []
    underlying_returns = []

    days_om = 0

    for (k1, v1), (k2, v2) in zip(spy_data.items(), vix_data.items()):

        spy = v1
        vix = v2

        if vix <= 18:
            portfolio_shares.quantity += 1
            if days_om > 0:
                portfolio_shares.quantity += 1
                days_om -= 1
        else: 
            days_om += 1
        
        underlying_shares.quantity += 1

        # Shares portfolio adjustment
        if portfolio_shares.quantity > 0 and prev_price != 0:
            portfolio_alloc = prev_price*portfolio_shares.quantity/portfolio
            portfolio *= (1 + (spy-prev_price)/prev_price*portfolio_alloc)

        if underlying_shares.quantity > 0 and prev_price != 0:
            portfolio_alloc = prev_price*underlying_shares.quantity/underlying_portfolio
            underlying_portfolio *= (1 + (spy-prev_price)/prev_price*portfolio_alloc)

        if underlying_portfolio_prev != 0 and portfolio_prev != 0:
            portfolio_returns.append((portfolio-portfolio_prev)/portfolio_prev)
            underlying_returns.append((underlying_portfolio-underlying_portfolio_prev)/underlying_portfolio_prev)

        prev_price = spy
        portfolio_prev = portfolio
        underlying_portfolio_prev = underlying_portfolio

        # print(date, portfolio)
        
    print("Return", (portfolio/portfolio_beg-1) * 100)
    print("Portfolio std", stdev(portfolio_returns) * math.sqrt(252) * 100)
    print("Underlying Return", (underlying_portfolio/portfolio_beg-1) * 100)
    print("Underlying std", stdev(underlying_returns) * math.sqrt(252) * 100)

def main():
    stock()
    # print(get_option_price("call", 27.41, 18, 844, 0.0147, 0.557))

if __name__ == "__main__":
    main()