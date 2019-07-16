from .setth import get_stock_detail

class Stock:
    def __init__(self, country='', symbol='', sector='', source=''):
        self.country = country
        self.symbol = symbol
        self.sector = sector
        self.info = {}
        if source == 'web':
            self.scrape_web()

    def __str__(self):
        return '{}:{}\n{}'.format(self.country, self.symbol, self.info)
    
    def scrape_web(self):
        if self.country == 'THA':
            self._query_set()
    
    def _query_set(self):
        data = get_stock_detail(self.symbol)
        self.info = data
