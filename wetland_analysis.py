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

def municipality_analysis_year(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['28']
    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

                print 'Year is: ' + year + ' and projection is: ' + projection

                municipalities_orig = 'tl_2016_{0}_cousub_clip'.format(state_number)

                municipalities = arcpy.CopyFeatures_management(municipalities_orig, 'tl_2016{0}_cousub_clip_wetland' .format(state_number))

                arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

                arcpy.AddField_management('clipped_municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('clipped_municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields'

                # Get wetlands shapefiles into db and formatted so that state number can be specified
                wetlands = arcpy.ListFeatureClasses().format(state_number)

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:

                    state_inundation_surface = arcpy.ListFeatureClasses(
                        'final_polygon*{0}x_{1}_{2}_merged_clip_to_{3}'.format(flood_frequency, year, projection, state_number))[0]

                    state_mhhw_surface = arcpy.ListFeatureClasses('final_polygon_mhhw_merged_clip_to_{0}' .format(state_number))[0]

                    municipalities_minus_wetlands = arcpy.Erase_analysis('clipped municipalities', wetlands,
                                                                         'tl_2016_{0}_clip_no_wetlands'.format(state_number))

                    municipalities_minus_mhhw_and_wetlands = arcpy.Erase_analysis(municipalities_minus_wetlands, state_mhhw_surface,
                                                                         'tl_2016_{0}_clip_no_wetlands_or_mhhw'.format(state_number))

                    arcpy.MakeFeatureLayer_management(municipalities_minus_mhhw_and_wetlands, 'clipped_municipalities')

                    inundation_minus_wetlands = arcpy.Erase_analysis(state_inundation_surface, wetlands, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands'.format(flood_frequency, year, projection, state_number))

                    inundation_minus_mhhw_and_wetlands = arcpy.Erase_analysis(inundation_minus_wetlands, state_mhhw_surface, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw'.format(flood_frequency, year, projection, state_number))

                    arcpy.MakeFeatureLayer_management(inundation_minus_mhhw_and_wetlands, 'inundation_minus_mhhw_and_wetlands')


                    arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", 'inundation_minus_mhhw_and_wetlands', "", "NEW_SELECTION")


                    fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Shape_Area", "Area_MHHW","Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection), "Wetland_area"]

                    count = 0
                    with arcpy.da.UpdateCursor('clipped_municipalities', fields) as cursor:
                        for row in cursor:

                            count = count + 1

                            print 'Count is: ' + str(count)
                            muni = row[0]
                            muni_land_area = row[1]
                            muni_state = row[2]
                            muni_county = row[3]
                            muni_name = row[4]
                            muni_water_area = row[5]
                            total_muni_area = row[6]
                            mhhw_area = row[7]

                            wetland_area = row[10]

                            outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni_' + str(count)

                            #outname_mhhw = 'clip_mhhw_surface_' + year + '_' + projection + '_to_muni_' + str(count)

                            print 'Year is: ' + year + ' and state number is ' + state_number

                            print 'Municipality is: ' + muni_name

                            print 'Total muni area is: ' + str(total_muni_area)

                            print 'MHHW area is: ' + str(mhhw_area)


                            if total_muni_area is None:

                                print 'Municipality area is None'

                            elif total_muni_area > 0:

                                arcpy.Clip_analysis(str(inundation_minus_mhhw_and_wetlands), muni, outname)

                                print 'Clipped inundation minus wetlands layer to tract'

                                fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                # arcpy.Clip_analysis(str(mhhw_minus_wetlands), muni, outname)
                                #
                                # print 'Clipped mhhw minus wetlands layer to tract'

                                #fc_mhhw = arcpy.MakeFeatureLayer_management(outname_mhhw, 'clipped_mhhw_surface_layer')

                                #print 'Created mhhw_inundation_surface_layer to municipality'

                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                result_mhhw = int(arcpy.GetCount_management(fc).getOutput(0))

                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, "%.2f" % muni_water_area, year, projection, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows in Area_acres
                                    output_table_name = 'output_sum_area_{0}' .format(str(count))

                                    arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                                    # output_table_name_mhhw = 'output_sum_area_mhhw_{0}' .format(str(count))
                                    #
                                    # arcpy.Statistics_analysis(fc_mhhw, output_table_name_mhhw, [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    # sum_area_mhhw = arcpy.da.TableToNumPyArray(output_table_name_mhhw, 'SUM_Shape_Area')[0]

                                    print 'Inundated non-wetland area is: ' + str(sum_area[0]) + ', and municipality area is: ' + str(total_muni_area)


                                    if mhhw_area is None:

                                        current_dry_area = total_muni_area - wetland_area

                                        newly_inundated_nonwetland_area = sum_area[0]

                                        percent_inundated_nonwetland_area_minus_mhhw = (newly_inundated_nonwetland_area/current_dry_area)*100

                                        writer = csv.writer(csvfile)

                                        writer.writerow(
                                            [muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year,
                                             projection, "%.2f" % sum_area[0],
                                             "%.2f" % percent_inundated_nonwetland_area_minus_mhhw])

                                        print 'Wrote to csv'

                                        row[8] = newly_inundated_nonwetland_area
                                        row[9] = percent_inundated_nonwetland_area_minus_mhhw

                                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                        cursor.updateRow(row)

                                    else:

                                        current_dry_area = total_muni_area # this should work because 'clipped municipalities' already has the mhhw and wetland areas erased.

                                        inundated_nonwetland_area = sum_area[0]
                                        #newly_inundated_nonwetland_area = sum_area[0] - mhhw_area

                                        percent_inundated_nonwetland_area_minus_mhhw = (inundated_nonwetland_area/current_dry_area)*100

                                        writer = csv.writer(csvfile)


                                        writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year, projection, "%.2f" % sum_area[0], "%.2f" % percent_inundated_nonwetland_area_minus_mhhw])
                                        print 'Wrote to csv'

                                        row[8] = inundated_nonwetland_area
                                        row[9] = percent_inundated_nonwetland_area_minus_mhhw

                                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                        cursor.updateRow(row)

                                del fc

                            else:
                                print 'Land area is 0.'

        print 'Finished municipality analysis for state number ' + state_number + ' for {0} {1}' .format(year, projection)

