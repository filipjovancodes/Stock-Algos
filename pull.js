async function fetchStockData() {
    try {
        const response = await node-fetch('https://ca.finance.yahoo.com/quote/AAPL/history?period1=1609459200&period2=1640995200&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true')
        console.log(response.json);
    } catch (error) {
        console.log(error);
    }
}

fetchStockData();
