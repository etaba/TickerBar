#!/usr/local/bin/python
import json, collections, os, sys
from pinance import Pinance

from config import *
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool

JSON_CACHE = "../quotes.json"

def cacheQuote(ticker,quote):
    try:
        cachedQuotes = json.load(open(JSON_CACHE,'r'))
    except Exception:
        cachedQuotes = {}

    if ticker in cachedQuotes.keys():
        for (k,v) in quote.items():
            cachedQuotes[ticker][k] = v
    else:
        cachedQuotes[ticker] = quote
    jsonCache = open(JSON_CACHE,'w+')
    jsonCache.write(json.dumps(cachedQuotes))
    jsonCache.close()


def cachedQuote(ticker):
    with open(JSON_CACHE) as jsonCache:
        cachedQuotes = collections.defaultdict(lambda: {"currVal":0,"change":0},json.load(jsonCache))
        return cachedQuotes[ticker]

def cachedStockAssets():
    totalChange = 0
    totalVal = 0
    for (symbol,quantity) in STOCKS.items():
        quote = cachedQuote(symbol)
        totalChange += quote['change'] * quantity
        totalVal += quote['currVal'] * quantity
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(int(totalVal),int(totalChange))

def dailyAsset(ticker):
    try:
        stock = Pinance(ticker)
        stock.get_quotes()
        if 'postMarketPrice' in stock.quotes_data.keys():
            currValue = float(stock.quotes_data['postMarketPrice'])*STOCKS[ticker]
            dayChange = float(stock.quotes_data['regularMarketChange'] + stock.quotes_data['postMarketChange'])*STOCKS[ticker]
        else:
            currValue = float(stock.quotes_data['regularMarketPrice'])*STOCKS[ticker]                
            dayChange = stock.quotes_data['regularMarketChange']*STOCKS[ticker]
        cacheQuote(ticker,{'currVal':currValue,'change':dayChange})
    except Exception:
        quote = cachedQuote(ticker)
        currValue = quote['currValue']*STOCKS[ticker]
        dayChange = quote['change']*STOCKS[ticker]
    return (currValue,dayChange)

def dailyPercent(ticker):
    try:
        stock = Pinance(ticker)
        stock.get_quotes()
        change = stock.quotes_data['regularMarketChangePercent']
        cacheQuote(ticker,{'change':change})
    except Exception:
        change = cachedQuote(ticker)['change']
    return round(change,2)

def currentPrice(ticker):
    try:
        stock = Pinance(ticker)
        stock.get_quotes()
        price = float(stock.quotes_data['LastTradePrice'])
        cacheQuote(ticker,{'currVal':price})
    except Exception:
        price = cachedQuote(ticker)['currVal']
    return price

def liveStockAssets():
    threadPool = Pool(5)
    dailyTotals = threadPool.map(dailyAsset,STOCKS.keys())
    threadPool.close()
    threadPool.join()
    balance = int(sum([dt[0] for dt in dailyTotals]))
    totalDayChange = int(sum([dt[1] for dt in dailyTotals]))
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(balance,totalDayChange)

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
            "BTTTouchBarAppleScriptString" : "cd {}/tickerbar; ./__init__.py daily".format(os.path.abspath('.')),
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
                "BTTTouchBarAppleScriptString":"cd {}/tickerbar; ./__init__.py ticker {}".format(os.path.abspath('.'),ticker),
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
    if sys.argv[1] == "ticker":
        ticker = sys.argv[2]
        change = dailyPercent(ticker)
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

