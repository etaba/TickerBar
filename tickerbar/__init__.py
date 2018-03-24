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
            "BTTTouchBarAppleScriptString" :    "from tickerbar import *\nprint(dailyGainPrintout())",
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
                "BTTTouchBarAppleScriptString":"from tickerbar import *\nprint(percentPrintout('{}'))".format(symbol),
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
                "BTTAdditionalActions" : widgets,
                "BTTIconData": "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",
                    "BTTTriggerConfig" : {
                    "BTTTouchBarItemIconHeight" : 22,
                    "BTTTouchBarItemIconWidth" : 22,
                    "BTTTouchBarItemPadding" : 30,
                    "BTTTouchBarFreeSpaceAfterButton" : "5.000000",
                    "BTTTouchBarButtonColor" : "75.323769, 75.323769, 75.323769, 255.000000",
                    "BTTTouchBarAlwaysShowButton" : "0",
                    "BTTTouchBarAlternateBackgroundColor" : "0.000000, 0.000000, 0.000000, 0.000000",
                    "BTTTouchBarOnlyShowIcon" : 1
                }
            }]
        }]
    }
    bttFile = open("bttStockConfig.json","w+")
    bttFile.write(json.dumps(btt))
    bttFile.close()

