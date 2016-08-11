import requests
import urllib
from bs4 import BeautifulSoup
import csv
from numpy import genfromtxt
import glob
import scipy.stats as stats
import os


def get_hourly_data(filename):

    product = 'hourly_height'
    datum = 'navd'
    units = 'english'
    time_zone = 'lst'
    format = 'csv'

    station_numbers_names = genfromtxt(filename,dtype=str,skip_header=1,delimiter=',')

    for row in station_numbers_names:

        station_name = row[1]
        station_number = row[0]
        if not os.path.exists(station_name + '_hourly_data'):

            os.makedirs(station_name + '_hourly_data')



        for date in range(2001, 2016):

            begin_date = str(date) + '0101'
            end_date = str(date) + '1231'

            #session = requests.Session()

            output_filename = os.path.join(station_name + '_hourly_data', station_name + '_hourly_data_' + str(date))
            urllib.urlretrieve('http://tidesandcurrents.noaa.gov/api/datagetter?begin_date=%s&end_date=%s&station=%s&product=%s&datum=%s&units=%s&time_zone=%s&format=%s' %(begin_date, end_date, station_number, product, datum, units, time_zone, format), output_filename)


            # save csv to directory created above



