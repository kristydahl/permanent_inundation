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


def prep_wetlands_data(region, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    file_with_projection = 'all_noaa_mhhw_mosaic_polygon'

    desc = arcpy.Describe(file_with_projection)
    SR = desc.SpatialReference

    print SR

    for state_number in state_numbers:
        wetlands_data = 'wetlands_orig_{0}'.format(state_number) # Get wetlands data into db and format with state number

        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

        state_muni_boundary = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

        print 'wetlands file is: ' + wetlands_data
        wetlands_clip = arcpy.Clip_analysis(wetlands_data,state_muni_boundary,str('wetlands_{0}_clip' .format(state_number)))

        print 'Clipped wetlands to NOAA mhhw polygon for state number: ' + state_number

        outname = 'wetlands_{0}_clip_proj'.format(state_number)
        arcpy.Project_management(wetlands_clip .format(state_number), outname, SR)

        print 'Projected wetlands data'

        municipalities = 'tl_2016_{0}_cousub_proj'.format(state_number)

        arcpy.Clip_analysis(municipalities, 'all_noaa_mhhw_mosaic_polygon', str('tl_2016_{0}_cousub_clip_for_wetlands'.format(state_number)))

        print 'Clipped state municipalities to NOAA mhhw polygon for state number: ' + state_number


def municipality_wetlands_analysis(years, projections, region, flood_frequency, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

                print 'Year is: ' + year + ' and projection is: ' + projection

                municipalities = 'tl_2016_{0}_cousub_clip_for_wetlands'.format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

                arcpy.AddField_management('clipped_municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('clipped_municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields'

                wetlands = 'wetlands_{0}_clip_proj'.format(state_number)

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:

                    state_inundation_surface = arcpy.ListFeatureClasses(
                        'final_polygon*{0}x_{1}_{2}_merged_clip_to_{3}'.format(flood_frequency, year, projection, state_number))[0]

                    state_mhhw_surface = arcpy.ListFeatureClasses('final_polygon_mhhw_merged_clip_to_{0}' .format(state_number))[0]

                    municipalities_minus_wetlands = arcpy.Erase_analysis(municipalities, wetlands,'tl_2016_{0}_clip_no_wetlands'.format(state_number))

                    print 'Erased wetlands from municipalities'
                    municipalities_minus_mhhw_and_wetlands = arcpy.Erase_analysis(municipalities_minus_wetlands, state_mhhw_surface,'tl_2016_{0}_clip_no_wetlands_or_mhhw'.format(state_number))

                    print 'Erased MHHW from municipalities'

                    arcpy.MakeFeatureLayer_management(municipalities_minus_mhhw_and_wetlands, 'clipped_municipalities')

                    inundation_minus_wetlands = arcpy.Erase_analysis(state_inundation_surface, wetlands, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands'.format(flood_frequency, year, projection, state_number))

                    print 'Erased wetlands from inundation layer'

                    inundation_minus_mhhw_and_wetlands = arcpy.Erase_analysis(inundation_minus_wetlands, state_mhhw_surface, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw'.format(flood_frequency, year, projection, state_number))

                    print 'Erased MHHW from inundation layer'

                    arcpy.MakeFeatureLayer_management(inundation_minus_mhhw_and_wetlands, 'inundation_minus_mhhw_and_wetlands')


                    arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", 'inundation_minus_mhhw_and_wetlands', "", "NEW_SELECTION")


                    fields = ["SHAPE@", "STATEFP", "COUNTYFP", "NAME", "Shape_Area", "Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

                    count = 0
                    with arcpy.da.UpdateCursor('clipped_municipalities', fields) as cursor:
                        for row in cursor:

                            count = count + 1

                            print 'Count is: ' + str(count)
                            muni = row[0]
                            muni_state = row[1]
                            muni_county = row[2]
                            muni_name = row[3]
                            total_muni_area = row[4]

                            outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni_' + str(count)

                            print 'Year: ' + year + '; State number: ' + state_number + '; Municipality: ' + muni_name

                            if total_muni_area is None:

                                print 'Municipality area is None'

                            elif total_muni_area > 0:

                                arcpy.Clip_analysis(str(inundation_minus_mhhw_and_wetlands), muni, outname)

                                print 'Clipped inundation minus wetlands layer to municipality'

                                fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, 0, year, projection, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows
                                    output_table_name = 'output_sum_area_{0}' .format(str(count))

                                    arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    print 'Inundated non-wetland area is: ' + str(sum_area[0]) + ', and municipality area is: ' + str(total_muni_area)

                                    current_dry_area = total_muni_area # this should work because 'clipped municipalities' already has the mhhw and wetland areas erased.

                                    inundated_nonwetland_area = sum_area[0]
                                    #newly_inundated_nonwetland_area = sum_area[0] - mhhw_area

                                    percent_inundated_nonwetland_area_minus_mhhw = (inundated_nonwetland_area/current_dry_area)*100

                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year, projection, "%.2f" % sum_area[0], "%.2f" % percent_inundated_nonwetland_area_minus_mhhw])
                                    print 'Wrote to csv'

                                    row[5] = inundated_nonwetland_area
                                    row[6] = percent_inundated_nonwetland_area_minus_mhhw

                                    # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                    cursor.updateRow(row)

                            del fc

                        else:
                            print 'Land area is 0.'

        print 'Finished municipality analysis for state number ' + state_number + ' for {0} {1}' .format(year, projection)

prep_wetlands_data('east_coast',['48'])

#municipality_wetlands_analysis(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'], 'east_coast','26',['48'])