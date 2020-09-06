"""
@author Varun Shah
A program to find the next trading date given a date and optionally an RIC

This module might need to be renamed to something better.
"""

# Front contract means the next contract due to expire.


import numpy as np
import pandas as pd
import calendar
import math
import datetime

MONTH_DICT = {'F': 'Jan',  # I keep forgetting these, which is why it's here.
              'G': 'Feb',
              'H': 'Mar',
              'J': 'Apr',
              'K': 'May',
              'M': 'Jun',
              'N': 'Jul',
              'Q': 'Aug',
              'U': 'Sep',
              'V': 'Oct',
              'X': 'Nov',
              'Z': 'Dec'
              }


def go_to_last_business_day(some_date):
    if some_date.weekday() == 5:
        return some_date - np.timedelta64(1, 'D')
    elif some_date.weekday() == 6:
        return some_date - np.timedelta64(2, 'D')
    else:
        return some_date


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
    def __init__(self, start_date, ric, k_contracts=1, n_months=False):
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
        if self.n_months:
            self.k_contracts = 1
        else:
            self.k_contracts = k_contracts

        self.today_date \
            = go_to_last_business_day(pd.to_datetime(datetime.datetime.now().
                                                     strftime('%Y-%m-%d')))
        self.full_df = pd.read_csv('metaMaster.csv')

    def get_kth_contract(self, date, given_ric):
        """
        Finds the next trading date
        :param given_ric:
        :param date:
        :return: next_date[pd_datetime]
        """
        working_df = self.get_ric_contracts(given_ric)
        roll_series = pd.to_datetime(working_df['myRollDT'], dayfirst=True)
        date_df = pd.DataFrame(
            dict(roll_date=roll_series, given_date=date))
        date_df['diff_days'] = (date_df['roll_date'] - date_df['given_date'])
        date_df['diff_days'] = date_df['diff_days'] / np.timedelta64(1, 'D')
        future_dates = date_df.where(date_df['diff_days'] > 0).dropna()
        for j in range(1, self.k_contracts):
            future_dates = date_df.where(future_dates['diff_days']
                                         != future_dates[
                                             'diff_days'].min()).dropna()
        next_date = date_df.where(future_dates['diff_days'] ==
                                  future_dates['diff_days'].min()).dropna()
        return next_date.index

    def get_ric_contracts(self, given_ric):
        """
        If an RIC is specified then makes a working dataframe containing only
        the specified RIC.
        :return: ric_df; the working dataframe.
        """
        ric_df = self.full_df.where(self.full_df['code'] == given_ric).dropna()
        return ric_df

    def append_prices(self, given_timeseries):
        price_array = []
        for j in range(0, len(given_timeseries)):
            ticker = given_timeseries['Ticker'][j]
            year = '20' + given_timeseries['Ticker'][j][3:5]
            date = pd.to_datetime(given_timeseries['Date'][j], dayfirst=True)
            date = datetime.datetime.strftime(date, "%Y-%m-%d")
            year_df = pd.read_csv(year + '.csv')
            try:
                price = year_df.loc[year_df['date'] == date][ticker].iloc[0]
            except IndexError:
                price = np.nan
            price_array.append(price)
        given_timeseries['Price'] = price_array
        return given_timeseries

    def append_return(self, given_timeseries):
        return_array = [np.nan]
        price_array = given_timeseries['Price'].to_numpy(dtype=float)
        for j in range(1, len(price_array)):
            indexer = j-1
            if np.isnan(price_array[j]):
                return_array.append(np.nan)
            else:
                while np.isnan(price_array[j] / price_array[indexer]):
                    indexer -= 1
                return_array.append(price_array[j] / price_array[indexer])

        given_timeseries['Return'] = return_array
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
            else:
                added_month_date = checking_date

            if checking_date.weekday() != 6 and checking_date.weekday() != 5:
                df_index = self.get_kth_contract(added_month_date, given_ric)
                try:
                    ticker = self.full_df.iloc[df_index[0]]['ticker']
                except IndexError:
                    ticker = "Error: Contract not found in meta"

                checking_date_string = checking_date.strftime('%d/%m/%Y')
                timeseries_new_row = {'Ticker': ticker,
                                      'Date': checking_date_string}
                timeseries_df = timeseries_df.append(timeseries_new_row,
                                                     ignore_index=True)

        timeseries_df = self.append_prices(timeseries_df)
        timeseries_df = self.append_return(timeseries_df)
        return timeseries_df

    def build_timeseries(self):
        timeseries_list = []
        for given_ric in self.ric:
            timeseries_list.append(self.build_ric_timeseries(given_ric))
        return timeseries_list


obj = ContinuousTimeseries("2019-01-01", ['w', 'c'])
a = obj.build_timeseries()
