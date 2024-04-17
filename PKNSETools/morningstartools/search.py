"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import json
import re
import xmltodict
import urllib

import requests
from bs4 import BeautifulSoup

from PKNSETools.morningstartools.error import not_200_response
from PKNSETools.morningstartools.utils import (ASSET_TYPE, EXCHANGE, FIELDS, FILTER_FUND, FILTER_STOCK,
                    SITE)
from PKDevTools.classes.Utils import random_user_agent
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.OutputControls import OutputControls

from PKNSETools.morningstartools.NSEStockDB import NSEStockDB

def filter_universe(field = FILTER_FUND, proxies = {}):
  """
  This function will use the screener of morningstar.co.uk to find the possible filters and their values.

  Args:
    
    field (str | list) : field to find

  Returns:
    dict of filter
      {'LargestRegion': ['', 'RE_AfricaDeveloped', 'RE_AfricaEmerging', 'RE_Asia4TigersEmerging', 'RE_Asiaex4TigersEmerging', 'RE_Australasia', 'RE_Canada', 'RE_CentralandEasternEurope', 'RE_CentralandLatinAmericaEmerging', 'RE_Japan', 'RE_UnitedKingdom', 'RE_UnitedStates', 'RE_WesternEuropeEuro', 'RE_WesternEuropeNonEuroexUK'], 'SustainabilityRank': ['1', '2', '3', '4', '5']}
    
  Examples:
    >>> filter_universe(['LargestRegion','SustainabilityRank'])
    >>> filter_universe('FeeLevel')
    >>> filter_universe(FILTER_STOCK)
    
  """
  
  if not isinstance(field, (str, list)):
    raise TypeError('field parameter should be a string or a list')

  if 'StarRatingM255' in field:
    raise ValueError('StarRatingM255 cannot be a field')
  
  if isinstance(field, list):
    filterDataPoints = '|'.join(field)
  else:
    filterDataPoints = field

  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')

  params = {
  'outputType' : 'json',
  'filterDataPoints' : filterDataPoints,
  }

  result = general_search(params, proxies=proxies)

  all_filter ={}

  if "filters" not in result:
    return all_filter
  if not result['filters']:
    return all_filter

  for r in result['filters'][0]:
    all_filter[list(r)[0]] = r[list(r)[0]]
  
  return all_filter


def general_search(params, proxies={}):
  """
  This function will use the screener of morningstar.co.uk to find informations about funds or classification

  Args:
    params (dict) : paramaters of the request
    proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}
  
  Returns:
    list of information

  Examples:
    >>> general_search(params = {
                                'page' : 1,
                                'pageSize' : 10,
                                'sortOrder' : 'LegalName asc',
                                'outputType' : 'json',
                                'version' : 1,
                                'universeIds' : 'FOFRA$$ALL',
                                'currencyId': 'INR',
                                'securityDataPoints' : ['FundTNAV','GBRReturnD1'],
                                'term' : 'myria',
                                })
  

  """
  if not isinstance(params, dict):
    raise TypeError('params parameter should be dict')

  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')
  #url
  url = "https://tools.morningstar.co.in/api/rest.svc/klr5zyak8x/security/screener"
  #headers
  headers = {
              'user-agent': random_user_agent(),
              }   

  response = requests.get(url,params=params, headers=headers,proxies=proxies)

  not_200_response(url, response)
    
  return json.loads(response.content.decode())


def search_field(pattern = ''):
  """
  This function retrieves the possible fields for the function dataPoint

  Args:
  pattern (str) : text contained in the field

  Returns:
      list of possible fields for the method dataPoint

  Example:
      >>> search_field('feE')
      >>> search_field('reTurn')

  """

  regex = re.compile(f'(?i){pattern}')
  filtered_list = list(filter(lambda field : regex.search(field),FIELDS))
  print(f"possible fields for function dataPoint can be : {', '.join(filtered_list)}")

  return filtered_list


def search_filter(pattern = '', asset_type ='fund'):
  """
  This function retrieves the possible filters for the parameter filters of the function search_funds
  

  Args:
  pattern (str) : text contained in the filter

  Returns:
      list of possible filters

  Example:
      >>> search_filter('RetUrn')
      >>> search_filter('id')

  """
  if not isinstance(pattern, (str)):
    raise TypeError('pattern parameter should be a string')
  
  if not isinstance(asset_type, (str)):
    raise TypeError('asset_type parameter should be a string')

  if asset_type not in ASSET_TYPE:
     raise TypeError(f"asset_type parameter can only take one of the values : {','.join(ASSET_TYPE)}")

  if asset_type == 'stock':
     filter_type = FILTER_STOCK
  else:
     filter_type = FILTER_FUND
    
  regex = re.compile(f'(?i){pattern}')
  filtered_list = list(filter(lambda field : regex.search(field),filter_type))
  if asset_type == 'stock':
     print(f"possible keys for the parameter filters of the method search_stock can be : {', '.join(filtered_list)}")
  else:
    print(f"possible keys for the parameter filters of the method seach_funds can be : {', '.join(filtered_list)}")

  return filtered_list

def search_funds(term, field, country = "", pageSize=10, currency ='INR', filters={}, proxies = {}):
  """
  This function will use the screener of morningstar.co.uk to find funds which include the term.

  Args:
    term (str): text to find a funds can be a the name, part of a name or the isin of the funds
    field (str | list) : field to find
    country (str) : text for code ISO 3166-1 alpha-2 of country
    pageSize (int): number of funds to return
    currency (str) : currency in 3 letters
    filters (dict) : filter funds, use the method filter_universe to find the different possible filter keys and values
    proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}

  Returns:
    list of dict with fund information
      [{'SecId': 'F00000270E', 'TenforeId': '52.8.FR0010342600', 'LegalName': '21 Gestion Active'}, {'SecId': 'F000013BGI', 'TenforeId': '52.8.MT7000022612', 'LegalName': '24 Capital Management SICAV plc - 24 Global Currency Fund Share Class A USD Accumulation'}, {'SecId': 'F00000PZHI', 'TenforeId': '52.8.FR0011443225', 'LegalName': '29 Haussmann Actions Europe C'}, {'SecId': 'F0GBR06QS1', 'TenforeId': '52.8.FR0007057427', 'LegalName': '29 Haussmann Actions Europe D'}, {'SecId': 'F0000101BL', 'TenforeId': '52.8.FR0013266590', 'LegalName': '29 Haussmann Actions Europe 
      I'}, {'SecId': 'F00000JW7U', 'TenforeId': '52.8.LU0532306957', 'LegalName': '3F Generation Acc'}, {'SecId': 'F00000UDVR', 'TenforeId': '52.8.FR0011911189', 'LegalName': 'AAM Family Values E1'}, {'SecId': 'F00000UDVS', 'TenforeId': '52.8.FR0011911197', 'LegalName': 'AAM Family Values 
      I'}, {'SecId': 'F0GBR04RG5', 'TenforeId': '52.8.FR0007022025', 'LegalName': 'AAZ Capitalisation'}, {'SecId': 'F000000ITD', 'TenforeId': '52.8.FR0010361600', 'LegalName': 'AAZ Prestige Or'}]
    
  Examples:
    >>> search_funds("Myria",['SecId','TenforeId','LegalName'],country="fr", pageSize=25)
    >>> search_funds("FR0011399914", 'LegalName', country="fr", pageSize=25)
    
  """

  if not isinstance(field, (str, list)):
    raise TypeError('field parameter should be a string or a list')

  if not isinstance(country, str):
    raise TypeError('country parameter should be a string')

  if country and not country.lower() in SITE.keys():
      raise ValueError(f'country parameter can only take one of the values: {", ".join(SITE.keys())}')

  if not isinstance(pageSize, int):
    raise TypeError('pageSize parameter should be an integer')

  if not isinstance(currency, str):
    raise TypeError('currency parameter should be a string')

  if not isinstance(filters, dict):
    raise TypeError('filters parameter should be a dict')

  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')


  if isinstance(field, list):
      securityDataPoints = '|'.join(field)
  else:
      securityDataPoints = field
  #if country find iso
  if country:
    iso = SITE[country.lower()]["iso3"]
    universeIds = f'FO{iso}$$ALL'
  else:
    universeIds = ""

  filter_list = []
  #loop on filter dict
  for f in filters:
    if f not in FILTER_FUND:
      print(f"{f} is not a valid filter and will be ignored. You can find the possible filters with the method search_filter().")
    else:
      #if list, IN condition
      if isinstance(filters[f], list):
          filter_list.append(f'{f}:IN:{":".join(filters[f])}')
      #if tuple, either, BTW, LT or GT condition
      elif isinstance(filters[f], tuple):
          if len(filters[f]) == 2:
              if isinstance(filters[f][0], (int,float)):
                  filter_list.append(f'{f}:BTW:{filters[f][0]}:{filters[f][1]}')
              elif filters[f][0] =="<":
                  filter_list.append(f'{f}:LT:{filters[f][1]}')
              elif filters[f][0] ==">":
                  filter_list.append(f'{f}:GT:{filters[f][1]}')
      #else IN condition
      else:
          filter_list.append(f'{f}:IN:{filters[f]}')

  params = {
  'page' : 1,
  'pageSize' : pageSize,
  'sortOrder' : 'LegalName asc',
  'outputType' : 'json',
  'version' : 1,
  'universeIds' : universeIds,
  'currencyId': currency,
  'securityDataPoints' : securityDataPoints,
  'term' : term,
  'filters' : '|'.join(filter_list),
  }

  result = general_search(params, proxies=proxies)

  if result['rows']:
    return result['rows']
  else:
    OutputControls().printOutput('0 fund found with the term %s' % (term))
    return {}

def search_stock(term,field,exchange, pageSize =10,currency ='INR', filters={}, proxies={}):
  """
  This function will use the screener of morningstar.co.uk to find stocks which include the term.

  Args:
    term (str): text to find a funds can be a the name, part of a name or the isin of the funds
    field (str | list) : field to find
    exchange (str) : stock echange closed list (.utils EXCHANGE)
    pageSize (int): number of funds to return
    currency (str) : currency in 3 letters
    filters (dict) : filter funds, use the method filter_universe to find the different possible filter keys and values
    proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}

  Returns:
    list of dict with stocks information
      [{'SecId': '0P0001OMLZ', 'TenforeId': '126.1.VCXB', 'LegalName': '10X Capital Venture Acquisition Corp III Ordinary Shares 
      - Class A'}, {'SecId': '0P0001O9WE', 'TenforeId': '126.1.VCXB/U', 'LegalName': '10X Capital Venture Acquisition Corp III Units (1 Ord Share Class A & 1/2 War)'}, {'SecId': '0P000184MI', 'TenforeId': '126.1.COE', 'LegalName': '51Talk无忧英语 ADR'}, {'SecId': '0P0001NAQE', 'TenforeId': '126.1.AKA', 'LegalName': 'a.k.a. Brands Holding Corp'}]
    
  Examples:
    >>> search_stock("visa",['SecId','TenforeId','LegalName'],exchange="NYSE", pageSize=25)
    >>> search_stock("FR0000125486", 'LegalName', exchange="PARIS", pageSize=10)
    
  """

  if not isinstance(field, (str, list)):
    raise TypeError('field parameter should be a string or a list')

  if not isinstance(exchange, str):
    raise TypeError('exchange parameter should be a string')

  if not exchange.upper() in EXCHANGE.keys():
      raise ValueError(f'exchange parameter can only take one of the values : {", ".join(EXCHANGE.keys())}')

  if not isinstance(pageSize, int):
    raise TypeError('pageSize parameter should be an integer')

  if not isinstance(currency, str):
    raise TypeError('currency parameter should be a string')

  if not isinstance(filters, dict):
    raise TypeError('filters parameter should be a dict')

  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')


  if isinstance(field, list):
      securityDataPoints = '|'.join(field)
  else:
      securityDataPoints = field

  universeIds = EXCHANGE[exchange.upper()]["id"]

  filter_list = []
  #loop on filter dict
  for f in filters:
    if f not in FILTER_STOCK:
      print(f"{f} is not a valid filter and will be ignored. You can find the possible filters with the method search_filter().")
    else:
      #if list, IN condition
      if isinstance(filters[f], list):
          filter_list.append(f'{f}:IN:{":".join(filters[f])}')
      #if tuple, either, BTW, LT or GT condition
      elif isinstance(filters[f], tuple):
          if len(filters[f]) == 2:
              if isinstance(filters[f][0], (int,float)):
                  filter_list.append(f'{f}:BTW:{filters[f][0]}:{filters[f][1]}')
              elif filters[f][0] =="<":
                  filter_list.append(f'{f}:LT:{filters[f][1]}')
              elif filters[f][0] ==">":
                  filter_list.append(f'{f}:GT:{filters[f][1]}')
      #else IN condition
      else:
          filter_list.append(f'{f}:IN:{filters[f]}')

  params = {
  'page' : 1,
  'pageSize' : pageSize,
  'sortOrder' : 'LegalName asc',
  'outputType' : 'json',
  'version' : 1,
  'universeIds' : universeIds,
  'currencyId': currency,
  'securityDataPoints' : securityDataPoints,
  'term' : term,
  'filters' : '|'.join(filter_list),
  }
  result = search_stock_autocomplete(term=term, filter=False)
  if len(result) > 0:
    return result
  else:
    result = search_stock_autocomplete(term=term, filter=True)
    if len(result) > 0:
      return result
  result = general_search(params, proxies=proxies)

  if result['rows']:
    if len(result['rows']) > 0:
      NSEStockDB().saveCache(ticker=term, stockDict=result['rows'][0])
    return result['rows']
  else:
    default_logger().debug(f'0 stock found with the term {term}')
    return {}

def search_stock_autocomplete(term,filter=False):
  term = term.replace("*","").strip().upper()
  search_results = []
  cachedData = NSEStockDB().searchCache(ticker=term)
  if cachedData is not None:
     return [cachedData]
  try:
    r = requests.get(f"https://morningstar.in/handlers/autocompletehandler.ashx?criteria={urllib.parse.quote(term)}{'&sender=sm' if filter else ''}")
    # with sender=sm
    # <StockList xmlns="" Criteria="RELIANCE">
    # <Table>
    # <ID>0P0000CBCF</ID>
    # <ScripName>Reliance Capital Ltd</ScripName>
    # <ShortName>RELCAPITAL</ShortName>
    # <ISIN>INE013A01015</ISIN>
    # <Exchange>BOM</Exchange>
    # <Symbol>500111</Symbol>
    # <Sector>Financial Services</Sector>
    # <LastPrice>11.78</LastPrice>
    # <LastPriceDate>14/02/2024</LastPriceDate>
    # <LastToLastPrice>11.78</LastToLastPrice>
    # <PercentChange>0.00</PercentChange>
    # <STARRATING>-</STARRATING>
    # </Table>
    
    # Without sender=sm
    #<QuoteData>
    # <Table>
    # <ID>0P0000NIOL</ID>
    # <Type>Stock</Type>
    # <Ticker>533143</Ticker>
    # <Description>Reliance Broadcast Network Ltd</Description>
    # <Exchange>BSE</Exchange>
    # </Table>
    if r is not None:
      stockDict = xmltodict.parse(r.text) # '{"QuoteData": {"Table": {"ID":"0P0000BI86", "Type":, "Ticker":, "Description":, "Exchange":}}}'
      jsonResponseNSE = {}
      jsonResponseBSE = {}
      if filter:
         rootKey = "StockList"
         tickerKey = "ShortName"
         descKey = "ScripName"
         isinKey = "ISIN"
         ratingKey = "STARRATING"
      else:
         rootKey = "QuoteData"
         tickerKey = "Ticker"
         descKey = "Description"
         isinKey = "Ticker"
         ratingKey = "STARRATING"
      if rootKey not in stockDict.keys() or stockDict[rootKey] is None or "Table" not in stockDict[rootKey].keys():
         return search_results
      tables = stockDict[rootKey]["Table"]
      if not isinstance(tables, list):
         tables = [tables]
      possibleFindInBSE = False
      for table in tables:
        tickerCondition = (table[tickerKey] == term.upper())
        nameCondition = (("(INDIA)" in table[descKey].upper() or "(" not in table[descKey]) and "*" not in table[descKey]) and ((term.upper() == table[descKey].upper()) or (len(term.split(" ")) > 1 and term.upper() in table[descKey].upper() and f'{term.upper().split(" ")[0]} ' in table[descKey].upper()))
        nseExchangeCondition = (table["Exchange"] == "NSE")
        bseExchangeCondition = (table["Exchange"] == "BSE")
        if (tickerCondition and bseExchangeCondition) or (nameCondition and bseExchangeCondition):
           possibleFindInBSE = True
        if tickerCondition or (nameCondition and nseExchangeCondition):
          jsonResponseNSE =  {"fundShareClassId": table["ID"],
                "LegalName": table[descKey],
                "Universe": "E0" + table["Exchange"],
                "TenforeId": table[isinKey],
                "Ticker": table[tickerKey],
                "StarRating": table[ratingKey] if ratingKey in table.keys() else "-"
                }
          if tickerCondition and nseExchangeCondition:
             break
        if possibleFindInBSE:
           jsonResponseBSE =  {"fundShareClassId": table["ID"],
                "LegalName": table[descKey],
                "Universe": "E0" + table["Exchange"],
                "TenforeId": table[isinKey],
                "Ticker": f"{table['Exchange']}:{table[tickerKey]}",
                "StarRating": table[ratingKey] if ratingKey in table.keys() else "-"
                }
           if tickerCondition and bseExchangeCondition:
             break
      if jsonResponseNSE != {}:
        search_results = [jsonResponseNSE]
        NSEStockDB().saveCache(ticker=term, stockDict=jsonResponseNSE)
      elif jsonResponseBSE != {}:
        NSEStockDB().saveCache(ticker=term, stockDict=jsonResponseBSE)
        search_results = [jsonResponseBSE]
  except Exception as e:
     default_logger().debug(e, exc_info=True)
     pass
  return search_results

def token_chart(proxies={}):
  """
  This function will scrape the Bearer Token needed to access MS API chart data

  Args:
  proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}

  Returns:
  str bearer token

  """

  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')

  url = 'https://www.morningstar.com/funds/xnas/afozx/chart'

  headers = {'user-agent' : random_user_agent()}

  response = requests.get(url, headers=headers,proxies=proxies)

  all_text = response.text
  if all_text.find("token") ==-1:
    return None

  token_start =all_text[all_text.find("token"):]
  return token_start[7:token_start.find("}")-1]


def token_fund_information(proxies={}):
  """
  This function will scrape the Bearer Token needed to access MS API funds information

  Args:
  proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}

  Returns:
  str bearer token

  """
  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')

  url = 'https://www.morningstar.co.uk/Common/funds/snapshot/PortfolioSAL.aspx'

  headers = {'user-agent' : random_user_agent()}


  response = requests.get(url, headers=headers,proxies=proxies)
  soup = BeautifulSoup(response.text, 'html.parser')
  script = soup.find_all('script', {'type':'text/javascript'})
  bearerToken = str(script).split('tokenMaaS:')[-1].split('}')[0].replace('"','').strip()
  return bearerToken

def token_investment_strategy(proxies={}):
  """
  This function will scrape the Bearer Token needed to access the investment strategy

  Args:
  proxies (dict) : set the proxy if needed , example : {"http": "http://host:port","https": "https://host:port"}

  Returns:
  str bearer token

  """
  if not isinstance(proxies, dict):
    raise TypeError('proxies parameter should be dict')

  url = 'https://www.morningstar.com.au/investments/security/ASX/VHY'

  headers = {'user-agent' : random_user_agent()}

  response = requests.get(url, headers=headers, proxies = proxies)

  all_text = response.text
  if all_text.find("token") ==-1:
    return None
  start_flag =',"'
  end_flag = '"www.morningstar.com.au"'
  token_end = all_text[:all_text.find(end_flag)-3]
  return token_end[token_end.rfind(start_flag)+2:]