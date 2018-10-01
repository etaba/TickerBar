from unittest import TestCase
import tickerbar
import os
import json

fullPath = os.path.dirname(os.path.realpath(__file__))
JSON_CACHE = fullPath+"/test_quotes.json"
CONFIG = fullPath+"/test_config.json"
STOCKS = json.load(open(CONFIG,'a+'))

class test_portfolio(TestCase):
    self.assertEqual(json.load(CONFIG),{})


if __name__ == '__main__':
    unittest.main()