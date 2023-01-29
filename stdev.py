import datetime
import csv
import numpy

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

def stdev(ticker, start, end):
    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')

    # get .csv files for tickers
    filename = ticker + ".csv"

    # get all data at daily market open for start-end periods
    stock_data = get_open_data(filename, start_date, end_date)

    arr = []

    for date in stock_data:
        arr.append(stock_data[date])

    print(ticker, ": ", numpy.std(arr))

def main():
    tickers = ['VIXY', 'GLXY', 'NFLX', 'JNJ', 'BABA', 'NIO', 'SQ', 'TSLA', 'COIN', 'HOOD', 'ARKK', 'SBUX', 'PYPL', 'TWTR', 'SLV', 'NVDA', 'AMD', 'AAPL', 'AMZN', 'USO', 'ABNB', 'MSFT', 'FB', 'DOT', 'NKE', 'DIS', 'GS', 'QQQ', 'BTC', 'IAU', 'ETH', 'KO', 'SPY']

    for ticker in tickers:
        stdev(ticker, '2017-01-01', '2022-01-01')
    
if __name__ == "__main__":
    main()