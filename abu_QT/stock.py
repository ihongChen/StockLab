#! encoding = utf8
from collections import namedtuple
from collections import OrderedDict
import pandas as pd 
from abc import ABCMeta, abstractmethod

class StockTradeDays:
    def __init__(self, price_array, start_date, date_array = None):
        ## private price array
        self.__price_array = price_array
        ## private date array
        self.__date_array = self._init_days(start_date, date_array)
        ## private stock change array
        self.__change_array = self.__init_change()
        ## Ordered Dict 
        self.stock_dict = self._init_stock_dict()
    
    def __init_change(self):
        """從price array生成change_array
        """
        price_float_array = [float(price_str) for price_str in 
                             self.__price_array]
        # 通過平移將錯開的收盤價格序列透過zip打包,每個元素為相鄰的兩個收盤價
        pp_array = [(price1,price2) for price1,price2 in 
                   zip(price_float_array[:-1],price_float_array[1:])]
        
        change_array = list(
            map(lambda e:round((e[1]-e[0])/e[0],3) ,pp_array)
        )        
        change_array.insert(0,0)
        return change_array
    
    def _init_days(self, start_date, date_array):
        """protect方法
        start_date : 初始日期
        date_array : 給定日期序列
        """
        if date_array is None:
            ## 簡易（不正確?)由start_date & self.__price_array來確定日期序列
            date_array = [str(start_date + ind) for ind, _ in 
                         enumerate(self.__price_array)]
        else:
            date_array = [str(date) for date in date_array]
        return date_array
    def print_private(self):
        print('date_array:{},\nprice_array:{},\nchange_array:{}'.format(
            self.__date_array,self.__price_array,self.__change_array))
    def _init_stock_dict(self):
        """使用namedtuple, OrderDict將結果合併
        """
        stock_namedtuple = namedtuple('stock',
                                      ('date','price','change'))
        
        stock_dict = OrderedDict(
            (date,stock_namedtuple(date, price, change)) 
            for date, price, change in 
            zip(self.__date_array, self.__price_array, 
                self.__change_array)
        )
                
        return stock_dict
    
    def filter_stock(self, want_up=True, want_calc_sum=False):
        """篩選結果子集
        params
        ======
        want_up : 是否上漲
        want_calc_sum : 是否計算漲幅
        """
        filter_func = (lambda day:day.change >0) if want_up else (
            lambda day:day.change<0)
        want_days = filter(filter_func, self.stock_dict.values())
        
        if not want_calc_sum:
            return want_days
        ## 計算漲幅
        change_sum = 0.0 
        for day in want_days:
            change_sum += day.change
            
        return change_sum
            
    def __str__(self):
        return str(self.stock_dict)
        
    __repr__  = __str__
    
    def __iter__(self):
        for key in self.stock_dict:
            yield self.stock_dict[key]
        
    
    def __getitem__(self,ind):
        date_key = self.__date_array[ind]
        return self.stock_dict[date_key]
    
    def __len__(self):
        return len(self.stock_dict)
    
class TradeStrategyBase(metaclass=ABCMeta):
    """
    交易策略的抽象類別
    """
    @abstractmethod
    def buy_strategy(self, *args, **kwargs):
        pass
    @abstractmethod
    def sell_strategy(self, *args, **kwargs):
        pass        

class TradeStrategy1(TradeStrategyBase):
    """
    交易策略1 : 
    =========
    追漲策略,當股價上漲一個閥值（預設7%)
    買入並持有s_keep_stock_threshold(20)天
    """
    s_keep_stock_threshold = 20
    def __init__(self):
        self.keep_stock_day = 0 
        ## 7%漲幅作為買入策略的閥值
        self.__buy_change_threshold = 0.07
        
    def buy_strategy(self, trade_ind, trade_day, trade_days):
        if self.keep_stock_day == 0 and \
            trade_day.change > self.__buy_change_threshold :
                ## 如果上漲超過幅度，並且沒有持有則買入
                self.keep_stock_day += 1
        elif self.keep_stock_day > 0:
            ## 持有股票,持有股票時間遞增
            self.keep_stock_day +=1
            
    def sell_strategy(self, trade_ind, trade_day, trade_days):
        if self.keep_stock_day >= \
            TradeStrategy1.s_keep_stock_threshold:
                ## 若持有股票天數 > 閥值 s_keep_stock_threshold 則賣出
                self.keep_stock_day = 0 
    
    @property
    def buy_change_threshold(self):
        return self.__buy_change_threshold
    
    @buy_change_threshold.setter
    def buy_change_threshold(self, buy_change_threshold):
        if not isinstance(buy_change_threshold, float):
            raise TypeError('buy change threshold must be float!')
        self.__buy_change_threshold = round(buy_change_threshold,2)
 
class TradeStrategy2(TradeStrategyBase):
    """
    交易策略2:
    ========
    均值回復策略當股價連續兩個交易日下跌,
    且下跌幅度超過默認 s_buy_change_threshold(-10%)
    買入並持有 s_keep_stock_threshold(10)天
    """
    s_keep_stock_threshold = 10 #買入後持有N天
    s_buy_change_threshold = -0.10 #下跌買入閥值
    def __init__(self):
        self.keep_stock_day = 0
    def buy_strategy(self, trade_ind, trade_day, trade_days):
        if self.keep_stock_day == 0 and trade_ind >= 1:
            """
            當沒有持有股票的時候self.keep_stock_day == 0 並且
            trade_ind >= 1, 不是交易開始的第一天, 因為需要前一天數據
            """
            # trade_day.change < 0 bool:今天股價是否下跌
            today_down = trade_day.change < 0 
            yesterday_down = trade_days[trade_ind - 1].change < 0 
            down_rate = trade_day.change + \
                trade_days[trade_ind - 1].change
            if today_down and yesterday_down and down_rate < \
                TradeStrategy2.s_buy_change_threshold:
                    # 買入條件成立
                    self.keep_stock_day += 1
        elif self.keep_stock_day > 0 :
            # 代表持有股票,持有日數增加
            self.keep_stock_day += 1
    
    def sell_strategy(self, trade_ind, trade_day, trade_days):
        if self.keep_stock_day >= \
            TradeStrategy2.s_keep_stock_threshold:
                self.keep_stock_day = 0
    @classmethod
    def set_keep_stock_threshold(cls, keep_stock_threshold):
        cls.s_keep_stock_threshold = keep_stock_threshold
    @staticmethod
    def set_buy_change_threshold(buy_change_threshold):
        TradeStrategy2.s_buy_change_threshold = buy_change_threshold    


class TradeLoopBack:
    """回測"""
    def __init__(self, trade_days, trade_strategy):
        """
        使用前面封裝的StockTradeDays和交易策略TradeStrategy
        params
        ======
        trade_days : StockTradeDays 交易數據序列
        trade_strategy : TradeStrategyBase 交易策略
        """
        self.trade_days = trade_days
        self.trade_strategy = trade_strategy 
        ## 交易盈虧序列
        self.profit_array = []
        
    def execute_trade(self):
        """執行交易回測"""
        for ind,day in enumerate(self.trade_days):
            """以時間驅動,完成交易回測"""
            if self.trade_strategy.keep_stock_day > 0:
                ## 如果持有股票,加入交易盈虧結果序列
                self.profit_array.append(day.change)
            #hasattr : 查詢object是否有實現某個方法
            if hasattr(self.trade_strategy, 'buy_strategy'):
                ## 買入策略
                self.trade_strategy.buy_strategy(ind, day, 
                                                 self.trade_days)
            if hasattr(self.trade_strategy, 'sell_strategy'):
                ## 賣出策略
                self.trade_strategy.sell_strategy(ind, day,
                                                 self.trade_days)    

if __name__ == '__main__':

    price_lst = ['23.2','22.1','24.5','27.3','25.6']
    date_lst = ['20170103','20170104','20170105','20170106','20170107']
    trade_days = StockTradeDays(price_lst,start_date = None,date_array = date_lst)
    strategy1 = TradeStrategy1()
    # price_float_lst = [float(e) for e in price_lst]
    # price_zip_float_lst = list(zip(price_float_lst[1:],price_float_lst[:-1]))
    # price_updown_perc_lst = [
    #         round((e1-e2)/e1,4) for e1,e2 in price_zip_float_lst
    #     ]
    # # print(price_updown_perc_lst)
    # price_updown_perc_lst.insert(0,0)

    # stock_namedtuple = namedtuple('stock',['date','price','updown_perc'])
    # print(stock_namedtuple)
    # stock_namedtuple_lst = [
    #         stock_namedtuple(date,price,price_updown_perc) for \
    #         date, price, price_updown_perc 
    #         in zip(date_lst, price_float_lst, price_updown_perc_lst)
    #     ]
    # # print(stock_namedtuple_lst)
    # stock_dict = OrderedDict(
    #     (date, stock_namedtuple(date, price, change))
    #     for date, price, change in  
    #     zip(date_lst, price_float_lst, price_updown_perc_lst)        
    # )

