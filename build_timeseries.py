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


def check_input_date(date):
    error_msg = "Error: Please enter the date in the correct yyyy-mm-dd format"
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(error_msg)


def get_inputs():
    parser = argparse.ArgumentParser(description="Find the next trading date "
                                                 "of a future from RIC and a "
                                                 "given date.")

    parser.add_argument("--date", help="Enter date in yyyy-mm-dd format, 2nd "
                                       "October 2017 = 2017-10-02",
                        required=True, type=check_input_date)  # The program
    # can't do anything without a date
    parser.add_argument("--ric", help="Enter RIC in capitals", type=str,
                        required=True)


meta_master = pd.read_csv('metaMaster.csv')

