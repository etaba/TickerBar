#!/usr/local/bin/python
import json, collections, os, sys
from pinance import Pinance
from functools import partial
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool, Lock

fullPath = os.path.dirname(os.path.realpath(__file__))
JSON_CACHE = fullPath+"/quotes.json"
CONFIG = fullPath+"/config.json"
STOCKS = json.load(open(CONFIG,'r'))

def addPosition(symbol, quantity):
    try:
        with open(CONFIG,'r') as config:
            positions = json.load(config)
        positions[symbol] = int(quantity)
        with open(CONFIG,'w') as config:
            json.dump(positions,config)
    except Exception as e:
        print("Error adding position: "+type(e))

def removePosition(symbol):
    try: 
        with open(CONFIG,'r') as config:
            positions = json.load(config)
        positions.pop(symbol)
        with open(CONFIG,'w') as config:
            json.dump(positions,config)
    except Exception as e:
        print("Error removing position: "+str(type(e)))

def clearConfig():
    with open(CONFIG,'w') as config:
        config.write('{}')

def printPositions():
    with open(CONFIG,'r') as config:
        positions = json.load(config)
        [print("{} : {}".format(symbol,quantity)) for (symbol,quantity) in positions.items()]

def cacheQuote(symbol,quote,lock=None):
    try:
        if lock !=None:
            lock.acquire()
        try:
            cachedQuotes = json.load(open(JSON_CACHE,'r'))
        #except Exception:
        #    with open(JSON_CACHE,"w+") as f:
        #        f.write("{}")
        #    cachedQuotes = {}

            if symbol in cachedQuotes.keys():
                for (k,v) in quote.items():
                    cachedQuotes[symbol][k] = v
            else:
                cachedQuotes[symbol] = quote
            jsonCache = open(JSON_CACHE,'w+')
            jsonCache.write(json.dumps(cachedQuotes))
            jsonCache.close()
            if lock !=None:
                lock.release()
        except Exception:
            if lock !=None:
                lock.release()
    except Exception as e:
        pass

def liveQuote(symbol, lock=None):
    stock = Pinance(symbol)
    stock.get_quotes()
    if 'postMarketPrice' in stock.quotes_data.keys():
        currValue = float(stock.quotes_data['postMarketPrice'])*STOCKS[symbol]
        dayChange = float(stock.quotes_data['regularMarketChange'] + stock.quotes_data['postMarketChange'])*STOCKS[symbol]
    else:
        currValue = float(stock.quotes_data['regularMarketPrice'])*STOCKS[symbol]                
        dayChange = stock.quotes_data['regularMarketChange']*STOCKS[symbol]
    cacheQuote(symbol,
                {'lastPrice':stock.quotes_data['regularMarketPrice'],
                'change':stock.quotes_data['regularMarketChange'],
                'percentChange':stock.quotes_data['regularMarketChangePercent']},
                lock)
    return (currValue,dayChange)

def cachedQuote(symbol):
    try:
        with open(JSON_CACHE) as jsonCache:
            cachedQuotes = collections.defaultdict(lambda: {"lastPrice":0,"change":0},json.load(jsonCache))
            return cachedQuotes[symbol]
    except Exception as e:
        return {"lastPrice":0,"change":0,"percentChange":0}

def liveDailyPercent(symbol):
    stock = Pinance(symbol)
    stock.get_quotes()
    percentChange = stock.quotes_data['regularMarketChangePercent']
    cacheQuote(symbol,{'percentChange':percentChange,
                        'lastPrice':stock.quotes_data['regularMarketPrice'],
                        'change':stock.quotes_data['regularMarketChange']})
    return percentChange

def liveTotal():
    cacheLock = Lock()
    liveQuoteAtomic = partial(liveQuote,lock=cacheLock)
    threadPool = Pool(5)
    dailyTotals = threadPool.map(liveQuoteAtomic,STOCKS.keys())
    threadPool.close()
    threadPool.join()
    balance = int(sum([dt[0] for dt in dailyTotals]))
    totalDayChange = int(sum([dt[1] for dt in dailyTotals]))
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(balance,totalDayChange)

def cachedTotal():
    totalChange = 0
    totalVal = 0
    for (symbol,quantity) in STOCKS.items():
        quote = cachedQuote(symbol)
        totalChange += quote['change'] * quantity
        totalVal += quote['lastPrice'] * quantity
        #print("{}: {} ({})".format(symbol,totalVal,totalChange))
    Result = collections.namedtuple("Result",["balance","dayChange"])
    return Result(int(totalVal),int(totalChange))

def lastOpen():
    today = datetime.today()
    if today.weekday() > 4:
        #find last friday
        lastOpen = today - timedelta(today.weekday() - 4)
    else:
        lastOpen = today
    return lastOpen.strftime('%Y-%m-%d')

def percentPrintout(symbol):
    try:
        percentChange = liveDailyPercent(symbol)
    except Exception:
        percentChange = cachedQuote(symbol)['percentChange']
    percentChange = round(percentChange,2)
    return "{}{}{}%".format(symbol,"+" if percentChange>0 else "",str(percentChange))

def dailyGainPrintout():
    try:
        total = liveTotal()
    except Exception:
        total = cachedTotal()
    if total.dayChange < 0:
        return "Total-$"+str(-1 * total.dayChange)
    else:
        return "Total+$"+str(total.dayChange)

def outputForBTT():
    widgets = [{
        "BTTWidgetName" : "Total",
        "BTTTriggerType" : 642,
        "BTTTriggerTypeDescription" : "Shell Script / Task Widget",
        "BTTTriggerClass" : "BTTTriggerTypeTouchBar",
        "BTTPredefinedActionType" : -1,
        "BTTPredefinedActionName" : "No Action",
        "BTTShellScriptWidgetGestureConfig" : "{}:::-c".format(sys.executable),
        "BTTAdditionalConfiguration" : "{}:::-c".format(sys.executable),
        "BTTEnabled" : 1,
        "BTTOrder" : 5,
        "BTTTriggerConfig" : {
            "BTTTouchBarItemIconHeight" : 22,
            "BTTTouchBarItemIconWidth" : 22,
            "BTTTouchBarItemPadding" : 0,
            "BTTTouchBarFreeSpaceAfterButton" : "5.000000",
            "BTTTouchBarButtonColor" : "63.000000, 249.000000, 105.000000, 255.000000",
            "BTTTouchBarAlwaysShowButton" : "1",
            "BTTTouchBarAppleScriptString" :    "from symbolbar import *\nprint(dailyGainPrintout())",
            "BTTTouchBarColorRegex" : "[-]+",
            "BTTTouchBarAlternateBackgroundColor" : "255.000000, 16.000000, 30.000000, 255.000000",
            "BTTTouchBarScriptUpdateInterval" : 100
        }
    }]
    for (symbol,_) in STOCKS.items():
        widgets.append(
            {
              "BTTWidgetName" : symbol,
              "BTTTriggerType" : 642,
              "BTTTriggerTypeDescription" : "Shell Script / Task Widget",
              "BTTTriggerClass" : "BTTTriggerTypeTouchBar",
              "BTTPredefinedActionType" : -1,
              "BTTPredefinedActionName" : "No Action",
              "BTTShellScriptWidgetGestureConfig" : "{}:::-c".format(sys.executable),
              "BTTAdditionalConfiguration" : "{}:::-c".format(sys.executable),
              "BTTEnabled" : 1,
              "BTTOrder" : 0,
              "BTTTriggerConfig" : {
                "BTTTouchBarItemIconHeight" : 22,
                "BTTTouchBarItemIconWidth" : 22,
                "BTTTouchBarItemPadding" : 0,
                "BTTTouchBarFreeSpaceAfterButton" : "5.000000",
                "BTTTouchBarButtonColor" : "63.000000, 249.000000, 105.000000, 255.000000",
                "BTTTouchBarAlwaysShowButton" : "0",
                "BTTTouchBarAppleScriptString":"from symbolbar import *\nprint(percentPrintout('{}'))".format(symbol),
                "BTTTouchBarColorRegex" : "[-]+",
                "BTTTouchBarAlternateBackgroundColor" : "255.000000, 16.000000, 30.000000, 255.000000",
                "BTTTouchBarScriptUpdateInterval" : 5,
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

