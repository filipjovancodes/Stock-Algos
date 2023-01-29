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

def correlation(ticker1, ticker2, start, end):
    # yyyy/mm/dd start and end dates of algorithm
    start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d')

    # get .csv files for tickers
    filename1 = ticker1 + ".csv"
    filename2 = ticker2 + ".csv"

    # get all data at daily market open for start-end periods
    stock_data1 = get_open_data(filename1, start_date, end_date)
    stock_data2 = get_open_data(filename2, start_date, end_date) 

    array1 = []
    array2 = []

    for date in stock_data1:
        array1.append(stock_data1[date])
        array2.append(stock_data2[date])

    print(numpy.corrcoef(array1, array2))

def main():
    correlation('CRM', 'MSFT', '2021-03-20', '2021-09-20')
    
if __name__ == "__main__":
    main()