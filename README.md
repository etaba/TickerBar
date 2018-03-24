# TickerBar
BetterTouchTool plugin which adds a button to your macbook touch bar which displays live stock data.


# Installation and Usage

1) To use this plugin you must have BetterTouchTool. Even without this plugin BetterTouchTool is a must-have for any mac power user. <link>

2) Install tickerbar: `pip install tickerbar`

3) Add the stock positions you'd like to monitor: `tickerbar add <symbol_1> <number_of_shares_1> <symbol_2> <number_of_shares_2> ...`
Note: You can remove positions with `tickerbar remove <symbol>` . To remove all of them: `tickerbar remove all`. You can change a position by simply adding it again: `tickerbar add <symbol> <new_quantity>`, this will override the existing data for that symbol.

4) Generate BetterTouchTool settings: `tickerbar btt`. This will create a JSON settings file in the directory you run the command from.

5) Import settings to BetterTouchTool

6) Enjoy! If you make changes to your positions via `tickerbar add` or `tickerbar remove` you'll need to repeat steps 4-5 to update BetterTouchTool. You can further customize the buttons you've just created through the BetterTouchTool app!


Notes:
TickerBar caches the last stock quote it finds. If you go offline it will use this cached value.