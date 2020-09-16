"""
@author Varun Shah
A program to find the next trading date given a date and optionally an RIC

"""

import numpy as np
import pandas as pd
import calendar
import math
import datetime

# TODO Make the user roll date customizable relative to gsci roll date
#  (+/- n days)
#  (Remember to check if the contract has expired - logger warning or error)

# TODO Check that the rolling days aren't holidays.

MONTH_DICT = {'F': 1,  # Jan (I keep forgetting these, which is why it's here.)
              'G': 2,  # Feb
              'H': 3,  # Mar
              'J': 4,  # Apr
              'K': 5,  # May
              'M': 6,  # Jun
              'N': 7,  # Jul
              'Q': 8,  # Aug
              'U': 9,  # Sep
              'V': 10,  # Oct
              'X': 11,  # Nov
              'Z': 12  # Dec
              }

prices_dict = {'2007': pd.read_csv('2007.csv'),
               '2008': pd.read_csv('2008.csv'),
               '2009': pd.read_csv('2009.csv'),
               '2010': pd.read_csv('2010.csv'),
               '2011': pd.read_csv('2011.csv'),
               '2012': pd.read_csv('2012.csv'),
               '2013': pd.read_csv('2013.csv'),
               '2014': pd.read_csv('2014.csv'),
               '2015': pd.read_csv('2015.csv'),
               '2016': pd.read_csv('2016.csv'),
               '2017': pd.read_csv('2017.csv'),
               '2018': pd.read_csv('2018.csv'),
               '2019': pd.read_csv('2019.csv'),
               '2020': pd.read_csv('2020.csv'),
               '2021': pd.read_csv('2021.csv')
               }


def go_to_last_business_day(some_date):
    if some_date.weekday() == 5:
        return some_date - np.timedelta64(1, 'D')
    elif some_date.weekday() == 6:
        return some_date - np.timedelta64(2, 'D')
    else:
        return some_date


def get_eighth_business_day(string_date):
    # Date is the first day of a given month
    # 1st Mon - Wed becomes 10th
    date = pd.to_datetime(string_date)
    if 0 <= date.weekday() <= 2:
        eighth_business_day = date + np.timedelta64(9, 'D')
    # 1st Thurs - Sat becomes 12th
    elif 3 <= date.weekday() <= 5:
        eighth_business_day = date + np.timedelta64(11, 'D')
    # 1st Sun becomes 11th
    else:
        eighth_business_day = date + np.timedelta64(10, 'D')
    return eighth_business_day.strftime('%d/%m/%Y')


def add_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    if add_days > 0:
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:
                continue
            business_days_to_add -= 1
    elif add_days < 0:
        while business_days_to_add < 0:
            current_date -= datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5:
                continue
            business_days_to_add += 1
    return current_date


def add_months(user_date, months_to_add):
    month = user_date.month + (months_to_add - 1)
    if months_to_add >= 0:
        year = user_date.year + int(month / 12)
    else:
        year = user_date.year - math.ceil(abs(month) / 12)
    month = month % 12 + 1
    day = min(user_date.day, calendar.monthrange(year, month)[1])
    if datetime.date(year, month, day).weekday() == 5:
        new_date = datetime.date(year, month, day) - datetime.timedelta(days=1)
        return pd.to_datetime(new_date)
    elif datetime.date(year, month, day).weekday() == 6:
        new_date = datetime.date(year, month, day) - datetime.timedelta(days=2)
        return pd.to_datetime(new_date)
    else:
        return pd.to_datetime(datetime.date(year, month, day))


class ContinuousTimeseries:
    def __init__(self, start_date, ric, k_contracts=1, n_months=False,
                 use_gsci=False, business_days_to_add=0):
        # Constructor method
        self.start_date = pd.to_datetime(start_date)

        self.ric = ric
        ric_list = []
        for single_ric in self.ric:
            single_ric = single_ric.upper()
            if len(single_ric) == 1:
                single_ric = single_ric + " "
            ric_list.append(single_ric)
        self.ric = ric_list

        self.n_months = n_months
        self.k_contracts = k_contracts
        self.today_date \
            = go_to_last_business_day(pd.to_datetime(datetime.datetime.now().
                                                     strftime('%Y-%m-%d')))
        self.full_df = pd.read_csv('metaMaster.csv')
        self.use_gsci = use_gsci
        self.business_days_to_add = business_days_to_add

    def add_gsci_column(self):
        gsci_info = pd.read_csv('gsci.csv', index_col=0)
        gsci_column = [np.nan] * len(self.full_df['ticker'])
        user_roll_date_column = [np.nan] * len(self.full_df['ticker'])
        for (cmdty, data) in gsci_info.iteritems():
            for ticker in self.full_df['ticker']:
                df_index = self.full_df['ticker'].where(
                    self.full_df['ticker'] == ticker).notna().idxmax()
                if ticker[:2] == cmdty:
                    cmdty_series = gsci_info[ticker[:2]]
                    cmdty_month_series = cmdty_series.where(cmdty_series
                                                            == ticker[2])
                    if (cmdty_month_series.notna()[::-1].idxmax() == 12
                            and cmdty_month_series.notna().idxmax() == 1):
                        # Then we need to iterate from the beginning
                        month = 1
                        while True:
                            if cmdty_month_series.notna()[month + 1]:
                                month += 1
                            else:
                                break
                    else:
                        month = cmdty_month_series.notna()[::-1].idxmax()

                    if MONTH_DICT[ticker[2]] < month:
                        # Then we need to go to the last year
                        year = int(ticker[3:5]) + 1999
                    else:
                        # Then we stay in the same year
                        year = int(ticker[3:5]) + 2000
                    date_string = str(month) + '/' + str(year)
                    gsci_roll_date = get_eighth_business_day(date_string)
                    gsci_column[df_index] = gsci_roll_date
                    user_roll_date_raw = \
                        add_business_days(pd.to_datetime(gsci_roll_date,
                                                         dayfirst=True),
                                          self.business_days_to_add)
                    last_date_str \
                        = self.full_df.loc[self.full_df['ticker']
                                           == ticker]['LAST_TRADEABLE_DT'].\
                        iloc[0]
                    last_date = pd.to_datetime(last_date_str, dayfirst=True)
                    if last_date < user_roll_date_raw:
                        # Then there should be a warning
                        user_roll_date_str = last_date_str
                    else:
                        user_roll_date_str \
                            = user_roll_date_raw.strftime('%d/%m/%Y')
                    user_roll_date_column[df_index] = user_roll_date_str
        self.full_df["GSCIRollDT"] = gsci_column
        self.full_df["userRollDT"] = user_roll_date_column
        return self.full_df

    def get_kth_contract(self, date, given_ric, contract_k):
        if self.use_gsci:
            date_column = 'userRollDT'
        else:
            date_column = 'myRollDT'
        working_df = self.get_ric_contracts(given_ric)
        roll_series = pd.to_datetime(working_df[date_column], dayfirst=True)
        date_df = pd.DataFrame(
            dict(roll_date=roll_series, given_date=date))
        date_df['diff_days'] = (date_df['roll_date'] - date_df['given_date'])
        date_df['diff_days'] = date_df['diff_days'] / np.timedelta64(1, 'D')
        future_dates = date_df.where(date_df['diff_days'] > 0).dropna()
        for j in range(1, contract_k):
            future_dates = date_df.where(future_dates['diff_days']
                                         != future_dates[
                                             'diff_days'].min()).dropna()
        next_date = date_df.where(future_dates['diff_days'] ==
                                  future_dates['diff_days'].min()).dropna()
        return next_date.index

    def get_ric_contracts(self, given_ric):
        ric_df = self.full_df.where(self.full_df['code'] == given_ric).dropna()
        return ric_df

    def append_prices_and_returns(self, given_timeseries):
        price_list = []
        return_list = []
        for j in range(0, len(given_timeseries)):
            ticker = given_timeseries['Ticker'][j]
            year = '20' + given_timeseries['Ticker'][j][3:5]
            date = pd.to_datetime(given_timeseries['Date'][j], dayfirst=True)
            date_str = datetime.datetime.strftime(date, "%Y-%m-%d")
            year_df = prices_dict[year]
            try:
                price = year_df.loc[year_df['date']
                                    == date_str][ticker].iloc[0]
                price_index = year_df.loc[year_df['date']
                                          == date_str][ticker].index[0]
                first_price_index = year_df[ticker].dropna().index[0]
                if first_price_index == price_index:
                    this_return = np.nan
                else:
                    prices_til_now = year_df[ticker].dropna().loc[:price_index]
                    last_day_price = prices_til_now.iloc[-2]
                    this_return = (price / last_day_price) - 1
            except IndexError:
                price = np.nan
                this_return = np.nan
            price_list.append(price)
            return_list.append(this_return)
        given_timeseries['Price'] = price_list
        given_timeseries['Return'] = return_list
        return given_timeseries

    def build_ric_timeseries(self, given_ric):
        empty_data = {'Ticker': [],
                      'Date': []}

        timeseries_df = pd.DataFrame(empty_data)
        user_date = go_to_last_business_day(self.start_date)
        days_diff = (self.today_date - user_date) / np.timedelta64(1, 'D')

        for days_to_add in range(0, 1 + int(days_diff)):
            checking_date = user_date + np.timedelta64(days_to_add, 'D')
            if self.n_months:
                added_month_date = add_months(checking_date, self.k_contracts)
                kth_contract = 1
            else:
                added_month_date = checking_date
                kth_contract = self.k_contracts

            if checking_date.weekday() != 6 and checking_date.weekday() != 5:
                df_index = self.get_kth_contract(added_month_date, given_ric,
                                                 kth_contract)
                try:
                    ticker = self.full_df.iloc[df_index[0]]['ticker']
                except IndexError:
                    ticker = "Error: Contract not found in meta"

                checking_date_string = checking_date.strftime('%d/%m/%Y')
                timeseries_new_row = {'Ticker': ticker,
                                      'Date': checking_date_string}
                timeseries_df = timeseries_df.append(timeseries_new_row,
                                                     ignore_index=True)
        timeseries_df = self.append_prices_and_returns(timeseries_df)
        return timeseries_df

    def build_timeseries(self):
        timeseries_list = []
        if self.use_gsci:
            self.add_gsci_column()
        for given_ric in self.ric:
            timeseries_list.append(self.build_ric_timeseries(given_ric))
        return timeseries_list


obj = ContinuousTimeseries("2019-01-02", 'w', use_gsci=True)
ts = obj.build_timeseries()
