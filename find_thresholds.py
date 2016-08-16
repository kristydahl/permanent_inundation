import glob
import os
import csv
import numpy
from numpy import genfromtxt
import collections

import sys

sys.setrecursionlimit(10000)

# this function finds the threshold for a specific data file
def find_threshold(year, station_name, gauge_data, t): # add parameter for file with all location data

    #gauge_data = genfromtxt('Atlantic City_hourly_data/Atlantic City_hourly_data_2003', dtype=float, skip_header=1, delimiter=',')


    #print "t is: ", t
    flood_count = 0

    for idx,row in enumerate(gauge_data):
        current_observation = gauge_data[idx,1]

        if idx < (len(gauge_data) - 1):
            next_observation = gauge_data[(idx+1),1]

            if (current_observation < t and next_observation > t):
                flood_count = flood_count + 1

            end_of_file = (idx == len(gauge_data) - 2)
            if flood_count >48 and flood_count < 52 and end_of_file:
                print "DONE! The threshold is " + str(t)

                year_threshold_csv = station_name + '_year_threshold.csv'

                with open(year_threshold_csv, 'a') as csvfile_to_write:
                    writer = csv.writer(csvfile_to_write)
                    writer.writerow([year, t])

                    print "Added summary data for " + station_name + "to summary datafile"

                return

    find_threshold(year, station_name, gauge_data, t+.001)

#find_threshold(2.87)


# this function creates a csv with summary data for all locations

def create_summary_threshold_data (station_name):

    station_year_threshold_file = genfromtxt(station_name + '_year_threshold.csv', skip_header=0, delimiter=',')

    years_of_data = len(station_year_threshold_file)

    mean_threshold = numpy.mean(station_year_threshold_file, axis=0)[1]

    stdev_threshold = numpy.std(station_year_threshold_file, axis=0)[1]

    with open('all_locations_summary_threshold_data.csv','a') as file_to_write:

            writer = csv.writer(file_to_write)
            writer.writerow([station_name, '%.3f' % mean_threshold, '%.3f' % stdev_threshold, years_of_data])

# this function is a wrapper for find_threshold. it gets the data by location and MHHW, feeds MHHW into find_threshold,
# then collates the results into a csv for each location with year and threshold as the columns.
def thresholds_from_all_gauges(all_gauges_datafile):

    all_gauges_data = genfromtxt(all_gauges_datafile, dtype=str, skip_header=1, delimiter=',')

    for row in all_gauges_data:
        station_name = row[1]
        print station_name
        mhhw = float(row[3])

        hourly_data_folder = station_name + '_hourly_data'

        for year in range(2001,2004):

            hourly_data_file = os.path.join(hourly_data_folder, hourly_data_folder + '_' + str(year))

            gauge_data = genfromtxt(hourly_data_file, dtype=float, skip_header=1,
                            delimiter=',')

            if len(gauge_data) >= 7884:
                print "Station name: " + station_name
                print "Year is: " + str(year)
                print "Finding threshold"
                find_threshold(year, station_name, gauge_data, mhhw)

        create_summary_threshold_data(station_name)

        # this bit will call a method that creates a csv with all locations, average threshold, stdev, and # years in record

thresholds_from_all_gauges('test_data_for_looping_thresholds.csv')



