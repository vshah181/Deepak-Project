"""
@author Varun Shah
A program to find the next trading date given a date and optionally an RIC
"""

# TODO: Handle exceptions!!!!

# TODO: Build time-series returning contract code from front contract everyday
#  from user specified date to today's date (system date)

# Front contract means the next contract due to expire.

import numpy as np
import pandas as pd
import calendar
import math
import datetime
import argparse

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


def check_input_date(date):
    error_msg = "Error: Please enter the date in the correct yyyy-mm-dd format"
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(error_msg)


def positive_int(num_contracts):
    not_an_int = "Error: The number of additional contracts must be an integer"
    try:
        int(num_contracts)
        if int(num_contracts) != num_contracts:
            raise argparse.ArgumentTypeError(not_an_int)
        elif num_contracts < 0:
            raise argparse.ArgumentTypeError("Error, cannot have negative "
                                             "number of extra contracts")
        else:
            return num_contracts
    except ValueError:
        raise argparse.ArgumentTypeError(not_an_int)


def get_inputs():
    """
    Use the argparser to get the date and RIC (optional)
    :return: args.ric[str]
    :return: args.date[pd_datetime]
    """
    parser = argparse.ArgumentParser(description="Find the next trading date "
                                                 "of a future from RIC and a "
                                                 "given date.")

    parser.add_argument("--date", help="Enter date in yyyy-mm-dd format, 2nd "
                                       "October 2017 = 2017-10-02",
                        required=True, type=check_input_date)  # The program
    # can't do anything without a date
    parser.add_argument("--ric", help="Enter RIC in capitals", type=str)

    parser.add_argument("--contracts", help="The number of additional "
                                            "contracts to display",
                        type=positive_int, default=0)

    parser.add_argument("--months", help="The number of months to add "
                                         "(-1 goes back a month)", type=int,
                        default=0)

    args = parser.parse_args()

    if isinstance(args.ric, str):
        args.ric = args.ric.upper()
        if len(args.ric) == 1:
            args.ric = args.ric + " "  # Sorts out the space issue with single
        # letter RICs.
    return (args.ric, pd.to_datetime(args.date),
            args.contracts, args.months)


def make_ric_dataframe(user_ric, full_df):
    """
    If an RIC is specified then makes a working dataframe containing only the
    specified RIC.
    :param full_df: From input file
    :param user_ric: From user input
    :return: ric_df; the working dataframe.
    """
    ric_df = full_df.where(full_df['code'] == user_ric).dropna()
    return ric_df


def get_date_indices(working_df, user_date, k_contract):
    """
    Finds the next trading date
    :param working_df:
    :param user_date:
    :param k_contract:
    :return: next_date[pd_datetime]
    """
    roll_series = pd.to_datetime(working_df['myRollDT'], dayfirst=True)
    date_df = pd.DataFrame(dict(roll_date=roll_series, given_date=user_date))
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


def month_changer(user_date, months_to_add):
    """
    Add or subtract n months from the given date
    :param user_date: date input by the user
    :param months_to_add: number of months to add (int)
    :return: The new date, excluding weekends.
    """
    month = user_date.month + (months_to_add - 1)
    if months_to_add > 0:
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


meta_master = pd.read_csv('metaMaster.csv')
given_ric, given_date, extra_contracts, n_months = get_inputs()

if n_months != 0:
    working_date = month_changer(given_date, n_months)
else:
    working_date = given_date

if given_ric is None:
    work_df = meta_master
    extra_contracts = 0
    print("No RIC specified. Any input given under '--contracts' will be",
          "ignored.")
else:
    work_df = make_ric_dataframe(given_ric, meta_master)

i = 0
required_row_indices = np.zeros(0)
while True:
    required_row_indices = np.append(required_row_indices,
                                     get_date_indices(work_df, working_date, i))
    i += 1
    if i > extra_contracts:
        break
print(meta_master.loc[required_row_indices])
