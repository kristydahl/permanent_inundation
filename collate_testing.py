# I think this has been fully incorporated into the wetland_analysis.py script, but keeping in the repo as a standalone just in case.

import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
import csv
arcpy.CheckOutExtension("Spatial")
import zipfile

arcpy.env.overwriteOutput = True

def collate_shp_municipalities_and_write_csv(years, projections, region, flood_frequency, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            print 'Year is: ' + year

            for state_number in state_numbers:

                print 'State number is: ' + state_number

                municipalities = 'tl_2016_{0}_cousub_clip_for_wetlands' .format(state_number)

                file_with_results = 'tl_2016_{0}_clip_no_wetlands_or_mhhw' .format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

                arcpy.MakeFeatureLayer_management(file_with_results, 'to_read')

                arcpy.AddField_management('municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields to municipalities file'

                arcpy.SelectLayerByLocation_management('municipalities',"INTERSECT", 'to_read', "", "NEW_SELECTION")


                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_summary'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                #csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/test_collate.csv' .format(region)

                with open(csv_filename, 'wb') as csvfile:
                    fields = ['GEOID', "STATEFP", "COUNTYFP", "NAME", "Area_inun_{0}_{1}".format(year, projection), "Pct_inun_{0}_{1}".format(year, projection), "Shape_Area"]

                    count = 0
                    with arcpy.da.UpdateCursor('municipalities', fields) as cursor:
                        for row in cursor:

                            count = count + 1

                            geoid = row[0]
                            muni_state = row[1]
                            muni_county = row[2]
                            muni_name = row[3]
                            muni_area = row[6]

                            fc = arcpy.SelectLayerByAttribute_management('to_read',"NEW_SELECTION", " GEOID = '{0}' " .format(geoid))

                            output_table_name_total = 'output_total_area_collate_' + str(count)

                            output_table_name_inundated = 'output_inundated_area_collate_'+ str(count)

                            arcpy.Statistics_analysis(fc, output_table_name_total, [["Shape_Area", "SUM"]])

                            arcpy.Statistics_analysis(fc,output_table_name_inundated, [["Area_inun_{0}_{1}".format(year, projection), "SUM"]])

                            print 'Muni name is: ' + muni_name

                            if muni_area > 0:

                                total_area_orig = arcpy.da.TableToNumPyArray(output_table_name_total, 'SUM_Shape_Area')

                                print total_area_orig

                                if len(total_area_orig) > 0:

                                    total_area = total_area_orig[0]

                                    inundated_area = arcpy.da.TableToNumPyArray(output_table_name_inundated,'SUM_Area_inun_{0}_{1}'.format(year,projection))[0]

                                    print 'Total area is: ' + str(total_area[0]) + ' and inundated area is: ' + str(inundated_area[0])

                                    if total_area[0] is None:
                                        print 'Total area is none'

                                    elif inundated_area is None:
                                        print 'Inundated area is none'

                                    if inundated_area[0] > 0:
                                        percent_inundated = (inundated_area[0]/total_area[0])*100

                                        row[4] = inundated_area[0]
                                        row[5] = percent_inundated

                                        cursor.updateRow(row)

                                        writer = csv.writer(csvfile)

                                        writer.writerow(
                                            [muni_state, muni_county, muni_name, "%.2f" % total_area[0], year, projection, "%.2f" % inundated_area[0], "%.2f" % percent_inundated])

                                else:
                                    print 'Area is 0'

#collate_shp_municipalities_and_write_csv(['2060','2100'], ['NCAL'], 'east_coast', '26', ['13','23','24','25','28','33','34','36','37','42','44','45','48','51'])
collate_shp_municipalities_and_write_csv(['2100'], ['NCAL'], 'east_coast', '26', ['01','09','10','11'])
collate_shp_municipalities_and_write_csv(['2060','2100'], ['NCAL'], 'east_coast', '26', ['12','22'])
#collate_shp_municipalities_and_write_csv(['2060','2100'], ['NCAL'], 'west_coast', '26', ['06','41','53'])

#collate_shp_municipalities_and_write_csv(['2035','2060','2080','2100'], ['NCAI'], 'east_coast', '26', ['01'])

# Need to merge shps for FL and LA before running those states

#'01','09','10','11','13','23','24','25','28','33','34','36','37','42','44','45','48','51'