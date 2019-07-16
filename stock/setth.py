import requests
from bs4 import BeautifulSoup
import re

MARKETDATA_SET_DOMAIN = 'https://marketdata.set.or.th'
SET_DOMAIN = 'https://www.set.or.th'
API_LIST_STOCK_NAME = '/mkt/sectorquotation.do'
API_STOCK_FACTSHEET ='/set/factsheet.do'
AXIS_ROW = 0
AXIS_COL = 1

INDUSTRIES = ['AGRO', 'CONSUMP', 'FINCIAL', 'INDUS', 'PROPCON', 'RESOURC',
    'SERVICE', 'TECH']

SECTORS = {
    'AGRI': 'AGRO', 'FOOD': 'AGRO',
    'FASHION':'CONSUMP', 'HOME': 'CONSUMP', 'PERSON':'CONSUMP',
    'BANK':'FINCIAL', 'FIN':'FINCIAL', 'INSUR':'FINCIAL',
    'AUTO':'INDUS', 'IMM':'INDUS', 'PAPER':'INDUS', 'PETRO':'INDUS', 'PKG':'INDUS', 'STEEL':'INDUS',
    'CONMAT':'PROPCON', 'PROP':'PROPCON', 'PF&REIT':'PROPCON', 'CONS':'PROPCON',
    'ENERG':'RESOURC', 'MINE':'RESOURC',
    'COMM':'SERVICE', 'HELTH':'SERVICE', 'MEDIA':'SERVICE', 'PROF':'SERVICE', 'TOURISM':'SERVICE','TRANS':'SERVICE',
    'ETRON':'TECH', 'ICT':'TECH',
}

MAPPING_KEYWORD_TO_SECTION = {
    'Price (B.)': 'basic_info',
    'Top 10 Major Shareholders': 'holders',
    'News': 'news',
    'Company Profile': 'profile',
    'Price Performance': 'price_perfomance',
    'Business': 'description',
    'Management': 'managers',
    'Statistics': 'stat',
    'Rate of Return': 'return_rate',
    'Dividend': 'dividends',
    'Statement of Financial Position': 'financial_statement',
    'Statement of Comprehensive Income': 'income_statement',
    'Statement of Cash Flow': 'cashflow_statement',
    'Ratios': 'ratios',
    'Growth Rate': 'growth_rate',
    'Cash Cycle': 'cash_cycle',
}

def set_headers():
    return {
        'Accept': 'ext/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'marketdata.set.or.th',
        'Upgrade-Insecure-Requests': '1',
    }

def get_stock_name(sector=''):
    url = MARKETDATA_SET_DOMAIN + API_LIST_STOCK_NAME
    if sector == '':
        sectors = [key for key in SECTORS]
    else:
        sectors = [sector]

    res = {}
    for s in sectors:
        params = {'language': 'en', 'country':'US', 'market':'SET','sector': s}
        resp = requests.get(url, timeout=5, params=params)
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        stocks = soup.find_all('table', class_='table-info')[-1].select('a')

        for stock in stocks:
            res[stock.text.replace('\r','').replace('\n','').strip()] = s
 
    return res

def _extract_table(
    bs4_object, 
    ignore_column=[], 
    ignore_row=[], 
    head_column_shift=0, 
    major_axis=0,
    head_major_exist=True,
    head_minor_exist=True,
):
    '''
        decode a table from beautifulSoup object into a dictionary object.
        major_axis: (0: row, 1: column)
        head_major_exist: whether header does exist in the first major axis or not
        head_minor_exist: whether header does exist in the first minor axis or not
    '''

    def format_field_name(x):
        x = x.replace('\xa0','').strip().lower()
        x = x.replace('.','')
        x = x.replace(' ','_')
        x = x.replace('-','_')
        x = x.replace('%','percent')
        return x

    fieldname_row = [x.text for x in bs4_object.select('tr > td:first-child')]
    fieldname_row = [format_field_name(x) for x in fieldname_row]

    fieldname_col = [x.text for x in bs4_object.select('tr:first-child > td')]
    fieldname_col = [format_field_name(x) for x in fieldname_col]

    len_row, len_col = len(fieldname_row), len(fieldname_col) + head_column_shift

    ignore_row = [x+len_row if x < 0 else x for x in ignore_row]
    ignore_column = [x+len_col if x < 0 else x for x in ignore_column]
    ignore_column = set(ignore_column)
    ignore_row = set(ignore_row)

    if major_axis is AXIS_ROW:
        fieldname_major = list(range(0,len_row))
        fieldname_minor = list(range(0,len_col))
        if head_major_exist:
            ignore_column.add(0)
            fieldname_major = fieldname_row 
        if head_minor_exist:
            ignore_row.add(0)
            fieldname_minor = list(range(0,head_column_shift)) + fieldname_col
    else:
        fieldname_major = list(range(0,len_col))
        fieldname_minor = list(range(0,len_row))
        if head_major_exist:
            ignore_row.add(0)
            fieldname_major = list(range(0,head_column_shift)) + fieldname_col 
        if head_minor_exist:
            ignore_column.add(0)
            fieldname_minor = fieldname_row

    res = {}
    ignore_major = ignore_row if major_axis is AXIS_ROW else ignore_column
    for i, name in enumerate(fieldname_major):
        if i not in ignore_major:
            res[name] = {}


    row_objs = bs4_object.find_all('tr')
    try:
        for i, row_obj in enumerate(row_objs):
            if i in ignore_row:
                continue
            
            col_objs = row_obj.find_all('td')
            for j, col_obj in enumerate(col_objs):
                if j in ignore_column:
                    continue
                
                data = col_obj.text.replace('\xa0','').strip()
                if data == 'No Information Found':
                    continue
                if major_axis is AXIS_ROW:
                    res[fieldname_major[i]][fieldname_minor[j]] = data
                else:
                    res[fieldname_major[j]][fieldname_minor[i]] = data
    except IndexError as err:
        print("get_stock_detail error: {}".format(err))
        print("major fieldname is {}", fieldname_major)
        print("minor fieldname is {}", fieldname_minor)
        raise
    return res


def _convert_float(x=''): 
    if x in ['N/A', 'NaN']:
        return float('NaN')
    if x in ['-']:
        return 0.0
    return float(x.replace(',',''))

def get_stock_detail(name=''):
    url = SET_DOMAIN + API_STOCK_FACTSHEET

    if name == '':
        return {}
        
    params = {'language': 'en', 'country':'US', 'symbol': name}
    resp = requests.get(url, timeout=5, params=params)

    soup = BeautifulSoup(resp.content, 'html.parser')
    full_name = soup.find('table', class_='table-factsheet-padding3').text.replace(name,'',1).strip()

    blocks = soup.find_all('table', attrs={"class": re.compile('^(?!.*padding3).*factsheet.*$')})
    status = '-'

    if len(blocks[1].select('tr > td')) == 2:
        status = blocks[1].select('tr > td')[0].text.replace('\xa0','').strip()
    
    details = {}
    for block in blocks:
        keyword_block = block.select('tr > td > strong:first-child')
        if len(keyword_block) == 0:
            continue
        
        keyword = keyword_block[0].text
        matched = False
        for key, item in MAPPING_KEYWORD_TO_SECTION.items():
            if keyword.startswith(key):
                matched = True
                details[item] = block
                break
        
        if not matched:
            details[keyword] = block
    
    try: 
        basic_info = _extract_table(
            details['basic_info'],
            head_major_exist=False,
        )
        basic_info = [x[1] for x in basic_info.items()]
    except:
        basic_info = []
    
    try:
        details['news'].select('tr:first-child')[0].extract()
        news = _extract_table(
            details['news'],
            head_major_exist=False,
            ignore_row=[-1],
        )
        news = [x[1] for x in news.items()]
    except:
        news = []
    
    try:
        description = details['description'].select('tr:last-child > td')[0].text
    except:
        description = ''

    try:
        details['holders'].select('tr:first-child > td:first-child')[0].string = 'name'
        holders = _extract_table(
            details['holders'],
            head_column_shift=1, 
            head_major_exist=False,
            ignore_column=[0],
        )
        holders = [x[1] for x in holders.items()]
    except:
        holders = []

    try:
        details['managers'].select('tr:first-child > td:first-child')[0].string = 'name'
        managers = _extract_table(
            details['managers'],
            head_column_shift=1, 
            head_major_exist=False,
            ignore_column=[0],
        )
        managers = [x[1] for x in managers.items()]
    except:
        managers = []
    
    try:
        details['dividends'].select('tr:first-child')[0].extract()
        dividends = _extract_table(
            details['dividends'],
            head_major_exist=False,
            ignore_column=[0],
        )
        dividends = [x[1] for x in dividends.items()]
    except:
        dividends = []
    
    try:
        financial_statement = _extract_table(
            details['financial_statement'],
            major_axis=1,
            ignore_row=[-1],
        )
    except:
        financial_statement = {}

    try:
        income_statement = _extract_table(
            details['income_statement'],
            major_axis=1,
            ignore_row=[-1],
        )
    except:
        income_statement = {},
    
    try:
        cashflow_statement = _extract_table(
            details['cashflow_statement'],
            major_axis=1,
            ignore_row=[-1],
        )
    except:
        cashflow_statement = {}

    try:
        details['ratios'].select('tr:first-child')[0].extract()
        ratios = _extract_table(
            details['ratios'],
            major_axis=1,
            ignore_row=[-1],
        )
    except:
        ratios = {}

    try:
        growth_rate = _extract_table(
            details['growth_rate'],
            major_axis=1,
        )
    except:
        growth_rate = {}

    try:
        details['cash_cycle'].select('tr:first-child')[0].extract()
        cash_cycle = _extract_table(
            details['cash_cycle'],
            major_axis=1,
        )
    except:
        cash_cycle = {}

    stock_info = {
        'full_name': full_name,
        'status': status,
        'basic_info': basic_info,
        'news': news,
        'business_description': description,
        'major_holders': holders,
        'managers': managers,
        'dividends': dividends,
        'financial_statement': financial_statement,
        'income_statement': income_statement,
        'cashflow_statement': cashflow_statement,
        'ratios': ratios,
        'growth_rate': growth_rate,
        'cash_cycle': cash_cycle,
    }
    return stock_info
    


        