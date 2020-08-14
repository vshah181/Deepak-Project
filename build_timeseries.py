"""
@author Varun Shah
A program to build a timeseries given a date in the past to the current
system date
"""

import numpy as np
import pandas as pd
import calendar
import math
import datetime
import argparse

empty_data = {'Ticker': [],
              'Date': []}

timeseries_df = pd.DataFrame(empty_data)

def go_back_to_friday(some_date):
    if some_date.weekday() == 5:
        return some_date - np.timedelta64(1, 'D')
    elif some_date.weekday() == 6:
        return some_date - np.timedelta64(2, 'D')
    else:
        return some_date


def check_input_date(date):
    error_msg = "Error: Please enter the date in the correct yyyy-mm-dd format"
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(error_msg)


def get_inputs():
    parser = argparse.ArgumentParser(description="Build a fat time-series.")

    parser.add_argument("--date", help="Enter date in yyyy-mm-dd format, 2nd "
                                       "October 2017 = 2017-10-02",
                        required=False, type=check_input_date,
                        default="2017-01-01")  # The program
    # can't do anything without a date
    parser.add_argument("--ric", help="Enter RIC in capitals", type=str,
                        required=False, default="C")
    args = parser.parse_args()

    if len(args.ric) == 1:
        args.ric = args.ric + " "

    return args.ric.upper(), pd.to_datetime(args.date)


def get_date_indices(working_df, working_date, k_contract=0):
    """
    Finds the next trading date
    :param working_df:
    :param working_date:
    :param k_contract:
    :return: next_date[pd_datetime]
    """
    roll_series = pd.to_datetime(working_df['myRollDT'], dayfirst=True)
    date_df = pd.DataFrame(dict(roll_date=roll_series, given_date=working_date))
    date_df['diff_days'] = (date_df['roll_date'] - date_df['given_date'])
    date_df['diff_days'] = date_df['diff_days'] / np.timedelta64(1, 'D')
    future_dates = date_df.where(date_df['diff_days'] > 0).dropna()
    for j in range(0, k_contract):
        future_dates = date_df.where(future_dates['diff_days']
                                     != future_dates[
                                         'diff_days'].min()).dropna()
    next_date = date_df.where(future_dates['diff_days'] ==
                              future_dates['diff_days'].min()).dropna()
    return next_date.index


meta_master = pd.read_csv('metaMaster.csv')
user_ric, user_date = get_inputs()
today_date = pd.to_datetime(datetime.datetime.now().strftime('%Y-%m-%d'))

today_date = go_back_to_friday(today_date)
user_date = go_back_to_friday(user_date)

days_diff = (today_date - user_date) / np.timedelta64(1, 'D')

ric_df = meta_master.where(meta_master['code'] == user_ric).dropna()

for days_to_add in range(0, 1+int(days_diff)):
    checking_date = user_date + np.timedelta64(days_to_add, 'D')
    if checking_date.weekday() != 6 and checking_date.weekday() != 5:
        df_index = get_date_indices(ric_df, checking_date)
        ticker = meta_master.iloc[df_index[0]]['ticker']
        checking_date_string = checking_date.strftime('%d/%m/%Y')
        timeseries_new_row = {'Ticker': ticker, 'Date': checking_date_string}
        timeseries_df = timeseries_df.append(timeseries_new_row,
                                             ignore_index=True)

print(timeseries_df)
