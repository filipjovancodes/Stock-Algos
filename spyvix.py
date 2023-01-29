# VIX price vs SPY return

import csv
import statistics
import datetime
import math
from statistics import NormalDist
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
import numpy as np

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

def main():

    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime('1995-07-05', '%Y-%m-%d')
    end_date = datetime.datetime.strptime("2021-09-20", '%Y-%m-%d')

    # get all data at daily market open for start-end periods
    spy_data = get_open_data('SPY.csv', start_date - datetime.timedelta(days=30), end_date)

    # get all data at daily market open for start-end periods
    vix_data = get_open_data('^VIX.csv', start_date - datetime.timedelta(days=30), end_date)

    vix_prices = []
    spy_returns = []

    spy_prev = 0

    for (k1, v1), (k2, v2) in zip(spy_data.items(), vix_data.items()):

        vix = v2
        spy = v1

        if spy_prev != 0:
            vix_prices.append(vix)
            spy_returns.append((spy-spy_prev)/spy_prev)

        spy_prev = spy

    ratios = []

    for v in range(10, 30):

        chart = []
        neg_w = 1
        pos_w = 1
        neg = 1
        pos = 1

        for i in range(0, len(vix_prices), 1):
            if vix_prices[i] < v+1 and vix_prices[i] > v-1:
                chart.append([vix_prices[i], spy_returns[i]])

        for i in range(0, len(chart), 1):
            if chart[i][1] < 0:
                neg += (1 - chart[i][1])
                neg_w *= (1 - chart[i][1])
            elif spy_returns[i] > 0:
                pos += (1 + chart[i][1])
                pos_w *= (1 + chart[i][1])

        print("VIX", v, "neg", int(neg), "pos",int(pos), "ratio", round(neg_w/pos_w*neg/pos, 2))

        ratios.append(round(neg_w/pos_w*neg/pos, 2))

    # plt.plot(spy_returns, vix_prices, '.')
    # plt.show()

    plt.plot(range(10,30), ratios, '.')
    plt.show()

if __name__ == "__main__":
    main()