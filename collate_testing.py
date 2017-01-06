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

            for state_number in state_numbers:

                municipalities = 'tl_2016_{0}_cousub_clip_for_wetlands' .format(state_number)

                file_with_results = 'tl_2016_{0}_clip_no_wetlands_or_mhhw_testing2' .format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

                arcpy.MakeFeatureLayer_management(file_with_results, 'to_read')

                arcpy.AddField_management('municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields to municipalities file'


                #csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_summary'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/test_collate.csv' .format(region)

                with open(csv_filename, 'wb') as csvfile:
                    fields = ['GEOID', "STATEFP", "COUNTYFP", "NAME", "Area_inun_{0}_{1}".format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

                    with arcpy.da.UpdateCursor('municipalities', fields) as cursor:
                        for row in cursor:

                            geoid = row[0]
                            muni_state = row[1]
                            muni_county = row[2]
                            muni_name = row[3]

                            #print geoid

                            #expression = "[GEOID]  = {0} "  .format(geoid)

                            #print expression
                            fc = arcpy.SelectLayerByAttribute_management('to_read',"NEW_SELECTION", " GEOID = '{0}' " .format(geoid))

                            output_table_name_total = 'output_total_area'

                            output_table_name_inundated = 'output_inundated_area'

                            arcpy.Statistics_analysis(fc, output_table_name_total, [["Shape_Area", "SUM"]])

                            arcpy.Statistics_analysis(fc,output_table_name_inundated, [["Area_inun_{0}_{1}".format(year, projection), "SUM"]])

                            print 'Calculated stats'

                            # Something here for if land area is 0
                            total_area = arcpy.da.TableToNumPyArray(output_table_name_total, 'SUM_Shape_Area')[0]

                            print 'Total area is: ' + str(total_area[0])

                            inundated_area = arcpy.da.TableToNumPyArray(output_table_name_inundated, 'SUM_Area_inun_{0}_{1}' .format(year, projection))[0]

                            print 'Inundated area is: ' + str(inundated_area[0])

                            percent_inundated = (inundated_area[0]/total_area[0])*100

                            row[4] = inundated_area[0]
                            row[5] = percent_inundated

                            cursor.updateRow(row)

                            writer = csv.writer(csvfile)

                            writer.writerow(
                                [muni_state, muni_county, muni_name, "%.2f" % total_area[0], year, projection, "%.2f" % inundated_area[0], "%.2f" % percent_inundated])

collate_shp_municipalities_and_write_csv(['2006'], ['NCAH'], 'east_coast', '26', ['48'])