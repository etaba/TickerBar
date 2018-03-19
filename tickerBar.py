import json, sys, collections, sqlite3, os
from pinance import Pinance

from config import *
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool

DB_FILE = "stocks.sql"

def insertQuote(ticker,currVal,openPrice):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        qry = 'UPDATE stock SET insertDate = DATE("now", "localtime"), currVal = {}, openPrice = {} WHERE ticker="{}"'.format(ticker, currVal, openPrice)
        c.execute(qry)
    except Exception:
        qry = 'INSERT INTO stock (ticker, insertDate, currVal, openPrice) VALUES ("{}",DATE("now", "localtime"),{},{})'.format(ticker, currVal, openPrice)
        c.execute(qry)
    conn.commit()
    conn.close()

def cachedQuote(ticker):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    qry = 'SELECT * FROM stock WHERE ticker = "{}"'.format(ticker)
    c.execute(qry)
    stocks = c.fetchall()
    price = collections.namedtuple('price','ticker insertDate currVal openPrice')
    return price(*stocks[0])

def dailyAsset(ticker):
    stock = Pinance(ticker)
    stock.get_quotes()
    if stock.quotes_data['marketState'] == 'CLOSED':
        if 'postMarketPrice' in stock.quotes_data.keys():
            currValue = float(stock.quotes_data['postMarketPrice'])*STOCKS[ticker]
        else:
            currValue = float(stock.quotes_data['regularMarketPrice'])*STOCKS[ticker]                
        dayChange = stock.quotes_data['regularMarketChange']*STOCKS[ticker]
    else:
        currValue = float(stock.quotes_data['price'])*STOCKS[ticker]
        dayChange = float(stock.quotes_data['change'])*STOCKS[ticker]
    return (currValue,dayChange)

def dailyPercent(ticker):
    stock = Pinance(ticker)
    stock.get_quotes()
    if stock.quotes_data['marketState'] == 'CLOSED':
        change = stock.quotes_data['regularMarketChangePercent']
    else:
        change = float(stock.quotes_data['ChangePercent'])
    return round(change,2)

def currentPrice(ticker):
    stock = Pinance(ticker)
    stock.get_quotes()
    return float(stock.quotes_data['LastTradePrice'])

def liveStockAssets():
    threadPool = Pool(5)
    dailyTotals = threadPool.map(dailyAsset,STOCKS.keys())
    threadPool.close()
    threadPool.join()
    balance = int(sum([dt[0] for dt in dailyTotals]))
    totalDayChange = int(sum([dt[1] for dt in dailyTotals]))
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(balance,totalDayChange)

def cachedStockAssets():
    prices = [cachedQuote(ticker) for ticker in STOCKS.keys()]
    totalOpen = int(sum([price.openPrice*STOCKS[price.ticker] for price in prices]))
    totalCurrent = int(sum([price.currVal*STOCKS[price.ticker] for price in prices]))
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(totalCurrent,totalCurrent - totalOpen)

def lastOpen():
    today = datetime.today()
    if today.weekday() > 4:
        #find last friday
        lastOpen = today - timedelta(today.weekday() - 4)
    else:
        lastOpen = today
    return lastOpen.strftime('%Y-%m-%d')

def outputForBTT():
    widgets = [{
        "BTTWidgetName" : "Total",
        "BTTTriggerType" : 642,
        "BTTTriggerTypeDescription" : "Shell Script / Task Widget",
        "BTTTriggerClass" : "BTTTriggerTypeTouchBar",
        "BTTPredefinedActionType" : -1,
        "BTTPredefinedActionName" : "No Action",
        "BTTShellScriptWidgetGestureConfig" : "/bin/bash:::-c",
        "BTTAdditionalConfiguration" : "/bin/bash:::-c",
        "BTTEnabled" : 1,
        "BTTOrder" : 5,
        "BTTTriggerConfig" : {
            "BTTTouchBarItemIconHeight" : 22,
            "BTTTouchBarItemIconWidth" : 22,
            "BTTTouchBarItemPadding" : 0,
            "BTTTouchBarFreeSpaceAfterButton" : "0.000000",
            "BTTTouchBarButtonColor" : "63.000000, 249.000000, 105.000000, 255.000000",
            "BTTTouchBarAlwaysShowButton" : "1",
            "BTTTouchBarAppleScriptString" : "cd {}; source ~/.virtualenvs/TickerBar/bin/activate; python tickerBar.py daily".format(os.path.abspath('.')),
            "BTTTouchBarColorRegex" : "[-]+",
            "BTTTouchBarAlternateBackgroundColor" : "255.000000, 16.000000, 30.000000, 255.000000",
            "BTTTouchBarScriptUpdateInterval" : 100
        }
    }]
    for (ticker,_) in STOCKS.items():
        widgets.append(
            {
              "BTTWidgetName" : ticker,
              "BTTTriggerType" : 642,
              "BTTTriggerTypeDescription" : "Shell Script / Task Widget",
              "BTTTriggerClass" : "BTTTriggerTypeTouchBar",
              "BTTPredefinedActionType" : -1,
              "BTTPredefinedActionName" : "No Action",
              "BTTShellScriptWidgetGestureConfig" : "/bin/bash:::-c",
              "BTTAdditionalConfiguration" : "/bin/bash:::-c",
              "BTTEnabled" : 1,
              "BTTOrder" : 0,
              "BTTTriggerConfig" : {
                "BTTTouchBarItemIconHeight" : 22,
                "BTTTouchBarItemIconWidth" : 22,
                "BTTTouchBarItemPadding" : 0,
                "BTTTouchBarFreeSpaceAfterButton" : "5.000000",
                "BTTTouchBarButtonColor" : "63.000000, 249.000000, 105.000000, 255.000000",
                "BTTTouchBarAlwaysShowButton" : "0",
                "BTTTouchBarAppleScriptString" : "cd {}; source ~/.virtualenvs/TickerBar/bin/activate; python tickerBar.py ticker {}".format(os.path.abspath('.'),ticker),
                "BTTTouchBarColorRegex" : "[-]+",
                "BTTTouchBarAlternateBackgroundColor" : "255.000000, 16.000000, 30.000000, 255.000000",
                "BTTTouchBarScriptUpdateInterval" : 5.00726,
                "BTTHUDText" : "title",
                "BTTHUDDetailText" : "text"
              }
              })
    btt = { 
        "BTTPresetName" : "Stocks",
        "BTTPresetContent" : [{
            "BTTAppBundleIdentifier" : "BT.G",
            "BTTAppName" : "Global",
            "BTTTriggers" : [{
                "BTTTouchBarButtonName" : "Stocks",
                "BTTTriggerType" : 630,
                "BTTTriggerClass" : "BTTTriggerTypeTouchBar",
                "BTTPredefinedActionType" : -1,
                "BTTPredefinedActionName" : "No Action",
                "BTTEnabled" : 1,
                "BTTOrder" : 6,
                "BTTAdditionalActions" : widgets
            }]
        }]
    }
    bttFile = open("bttStockConfig.json","w+")
    bttFile.write(json.dumps(btt))
    bttFile.close()



if __name__ == "__main__":

    if sys.argv[1] == "init":
        initDb()

    elif sys.argv[1] == "daily":
        try:
            stockAssets = liveStockAssets()
        except Exception:
            stockAssets = cachedStockAssets()
        if stockAssets.dayChange < 0:
            print("-$"+str(-1 * stockAssets.dayChange))
        else:
            print("$"+str(stockAssets.dayChange))

    elif sys.argv[1] == "ticker":
        ticker = sys.argv[2]
        try:
            change = dailyPercent(ticker)
        except Exception:
            cachedData = cachedQuote(ticker)
            change = round(100*(cachedData[2] - cachedData[3])/cachedData[3],2)
        statement = "{}{}{}%".format(ticker,"+" if change>0 else "",str(change))
        print(statement)

    elif sys.argv[1] == "daily":
        try:
            stockAssets = liveStockAssets()
        except Exception:
            stockAssets = cachedStockAssets()
        if stockAssets.dayChange < 0:
            print("Total-$"+str(-1 * stockAssets.dayChange))
        else:
            print("Total+$"+str(stockAssets.dayChange))


    elif sys.argv[1] == "btt":
        outputForBTT()

