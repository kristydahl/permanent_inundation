import glob
import csv
from numpy import genfromtxt
import collections

def find_threshold(t):
    gauge_data = genfromtxt('boston_march_2016.csv', dtype=float, skip_header=1, delimiter=',')
    #print len(gauge_data)
    print "t is: ", t
    count = 0
    for idx,obs in enumerate(gauge_data):
        obs = gauge_data[idx,1]
        next_obs = gauge_data[idx+1,1]


        if (obs < t and next_obs > t):
            #print "Thar she floods!"
            count = count + 1
            #print count
        #print count

        if count > 33:
            #print 'Adjusting t downward'
            tnew = t + 0.001
            find_threshold(tnew)
            #print "New t is: ", tnew

        #print 'Count: ', count
