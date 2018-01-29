#! encoding = utf8

import pandas as pd
import numpy as np
import asyncio
import datetime,time
import sqlite3
import logging
import requests
import re
from io import StringIO
from tqdm import tqdm


def create_db(tablename, con, drop=False):
    cursor = con.cursor()
    if drop:
        SQL_DROP = """DROP TABLE IF EXISTS {} """.format(tablename)
        cursor.execute(SQL_DROP)
        logging.info('DROP TABLE {} SUCCESSED!!'.format(tablename))
    if tablename == 'tse_price':
        SQL_CREATE = """
            CREATE TABLE {}(
                yyyymmdd date,
                證券代號 TEXT,
                成交量 REAL,
                成交筆數 INTEGER, 
                開盤價 REAL, 
                最高價 REAL, 
                最低價 REAL, 
                收盤價 REAL, 
                本益比 REAL,
                PRIMARY KEY (yyyymmdd,證券代號)
            )
        """.format(tablename)
    elif tablename =='otc_price':
        SQL_CREATE = """
            CREATE TABLE {}(
                yyyymmdd date,
                證券代號 TEXT,
                成交量 REAL,
                成交筆數 INTEGER,
                成交金額 INTEGER,
                開盤價 REAL,
                最高價 REAL,
                最低價 REAL,
                收盤價 REAL,
                PRIMARY KEY (yyyymmdd,證券代號)
            )
        """.format(tablename)
    cursor.execute(SQL_CREATE)
    con.commit()
    logging.info('CREATE TABLE {} SUCCESSED!!'.format(tablename))


def get_tse_data(date):
    """上市公司每日股價 
    params
    ======
    date :(str)
        106/01/20

    return 
    ======
    dataframe 
    """
    r = requests.post('http://app.twse.com.tw/ch/trading/exchange/MI_INDEX/MI_INDEX.php', data={
        'download': 'csv',
        'qdate': date,
        'selectType': 'ALL',
    })
    r.encoding = 'big5'
    df = pd.read_csv(StringIO("\n".join([i.translate({ord(c): None for c in ' '})
                                         for i in r.text.split('\n')
                                         if len(i.split('",')) == 16 and i[0] != '='])), header=0)
    df.set_index('證券代號', inplace=True)
    df.columns = ['證券名稱', '成交量', '成交筆數', '成交金額', '開盤價', '最高價', '最低價', '收盤價',
                  '漲跌(+/-)', '漲跌價差', '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量', '本益比']

    df['成交量'] /= 1000
    df = df.drop(['漲跌(+/-)', '證券名稱', '最後揭示買量', '最後揭示賣量'], axis=1)
    df = df.replace('--', np.nan)
    df = df.apply(pd.to_numeric)
    assert len(set(df.index)) == len(df.index)

    return df


def get_tse_ndays_data(n_days):
    """抓距離今天n_days資料
    """
    data = {}  # 股價資料
    time = datetime.datetime.now()
    count = 0
    while (len(data) < n_days) and (count < n_days):
        count += 1
        # 假如日月 < 9 要補零
        month_str = str(time.month) if time.month > 9 else '0' + \
            str(time.month)
        day_str = str(time.day) if time.day > 9 else '0' + str(time.day)

        # e.x 20100101
        taiwan_time_str = str(time.year - 1911) + '/' + \
            month_str + '/' + day_str
        international_time_str = str(time.year) + month_str + day_str

        print('parsing', international_time_str)
        # 使用 get_tse_data 爬資料
        try:
            data[international_time_str] = get_tse_data(taiwan_time_str)
            print('success!')
        except:
            # 假日爬不到
            print('fail! check the date is holiday')

        # 減一天
        time -= datetime.timedelta(days=1)

    # 把資料疊起來
    tw_stock_list = []
    for date, df in tqdm(data.items()):
        df['yyyymmdd'] = pd.to_datetime(date)
        tw_stock_list.append(df)
    tw_stock_df = pd.concat(tw_stock_list)
    # 重置index
    tw_stock_df = tw_stock_df.reset_index()
    tw_stock_df.drop_duplicates(
        subset=['證券代號', '成交量', '成交筆數', '開盤價', '最高價', '最低價', '收盤價', '本益比'], inplace=True
    )
    tw_stock_df = tw_stock_df[['證券代號', 'yyyymmdd', '成交量',
                               '成交筆數', '開盤價', '最高價', '最低價', '收盤價', '本益比']]
    tw_stock_df['yyyymmdd'] = tw_stock_df['yyyymmdd'].astype('str')
    return tw_stock_df


def get_otc_data(date_tuple):
    ## stolen from https://github.com/Asoul/tsec/blob/master/crawl.py#L76
    """下載上櫃股價資料
    params
    ======
    data_tuple : (tuple)
        (2018,1,29)
    
    return
    ======
    當日otc股價 dataframe
    """
    

    date_str = '{0}/{1:02d}/{2:02d}'.format(
        date_tuple[0] - 1911, date_tuple[1], date_tuple[2])
    yyyymmdd = str(date_tuple[0]) + date_str[4:6] + date_str[-2:]
    
    ttime = str(int(time.time() * 100))
    url = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={}&_={}'.format(
        date_str, ttime)
    page = requests.get(url)

    if not page.ok:
        logging.error("Can not get OTC data at {}".format(date_str))
        return

    result = page.json()

    if result['reportDate'] != date_str:
        logging.error("Get error date OTC data at {}".format(date_str))
        return
    
    
    stock_ids = []
    yyyymmdd_dates = []
    volumns_amount = []
    deal_amount = []
    turnover = []
    open_price = []
    close_price = []
    highest_price = []
    lowest_price = []

    for table in [result['mmData'], result['aaData']]:        
        for tr in table:
            if len(tr) == 17:
                row = clean_row([
                    yyyymmdd,
                    tr[8],  # 成交股數 -- 成交量
                    tr[10],  # 成交筆數
                    tr[9],  # 成交金額
                    # tr[3],  # 漲跌價差                
                    # tr[-4]  # 發行股數
                    tr[4],  # 開盤價
                    tr[5],  # 最高價
                    tr[6],  # 最低價
                    tr[2]  # 收盤價
                ])
                row.insert(0,tr[0])
                stock_ids.append(row[0])
                yyyymmdd_dates.append(row[1])
                volumns_amount.append(float(row[2])/1000)
                deal_amount.append(int(row[3]))
                turnover.append(int(row[4]))
                open_price.append(float(row[5]))
                close_price.append(float(row[6]))
                highest_price.append(float(row[7]))
                lowest_price.append(float(row[8]))
    otc_price_df = pd.DataFrame({
        '證券代號' : stock_ids,
        'yyyymmdd' : yyyymmdd_dates,
        '成交量' : volumns_amount,
        '成交筆數' : deal_amount,
        '成交金額': turnover,
        '開盤價' : open_price,
        '最高價':highest_price,
        '最低價':lowest_price,
        '收盤價':close_price
    })
    return otc_price_df                
        
def get_otc_ndays_data(n_days):
    assert (n_days > 0) and isinstance(n_days,int),'n_days must be positive int'
    today = datetime.datetime.today()
    otc_ndays_price = pd.DataFrame()
    count = 0
    while (count < n_days):
        parse_day = today
        count+=1
        date_tuple = (parse_day.year, parse_day.month, parse_day.day)
        otc_price_df = get_otc_data(date_tuple)
        otc_ndays_price = otc_ndays_price.append(otc_price_df)
        parse_day -= datetime.timedelta(days=1)
    return otc_ndays_price

def clean_row(row):
    ''' Clean comma and spaces '''
    for index, content in enumerate(row):
        row[index] = re.sub(",", "", content.strip())
        if '---' in content :
            row[index] = np.nan
    return row





def insertDataFrameToDb(df, con, tablename):
    """
    df: dataframe to be inserted 
    con: db connection
    """
    print('更改pd.nan --> None')

    df = df.where(pd.notnull(df), None)
    print('塞入資料...')
    cursor = con.cursor()
    idx = 0
    for row_series in df.iterrows():
        idx += 1
        row_dict = {k: v for k, v in row_series[1].items()}
        col, val = list(zip(*row_dict.items()))
        sql_insert = """INSERT INTO {0} ({1}) VALUES ({2});"""
        num_quest = '?' + ',?' * (len(row_dict) - 1)
        # cols_bracket = ['[' + e + ']' for e in col]
        # cols_bracket = ','.join(col)
        fields = ','.join(col)
        sql_insert.format(tablename, fields, num_quest)

        try:
            cursor.execute(sql_insert.format(
                tablename, fields, num_quest), val)
        except sqlite3.IntegrityError:
            print('data exist!!', row_dict)
            continue
        except sqlite3.DataError:
            print('data db schema error', row_dict)
        if idx % 1000 == 0:
            print('insert {} data'.format(idx))
            
    con.commit()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    con = sqlite3.connect('twse.db')
    create_db('tse_price',con,drop=True)
    create_db('otc_price',con,drop=True)
    cursor = con.cursor()

    # df = crawlPrice('107/01/03')
    # logging.info(df)
    df_tse = get_tse_ndays_data(5) #
    df_otc = get_otc_ndays_data(5) # 
