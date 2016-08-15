import glob
import csv
from numpy import genfromtxt
import collections

def find_threshold(t): # add parameter for file with all location data

    gauge_data = genfromtxt('Atlantic City_hourly_data/Atlantic City_hourly_data_2003', dtype=float, skip_header=1, delimiter=',')

    # build in a check of the number of hourly obs in each year.

    # exclude any years with >X% of obs missing


    print "t is: ", t
    flood_count = 0

    for idx,row in enumerate(gauge_data):
        current_observation = gauge_data[idx,1]

        if idx < (len(gauge_data) - 1):
            next_observation = gauge_data[(idx+1),1]

            if (current_observation < t and next_observation > t):
                flood_count = flood_count + 1

            end_of_file = (idx == len(gauge_data) - 2)
            if flood_count == 50 and end_of_file:
                print "DONE! The threshold is " + str(t)
                return

    find_threshold(t+.001)

#find_threshold(2.87)