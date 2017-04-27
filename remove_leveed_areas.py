# These methods remove leveed areas from inundation layers and county subdivision layers that have already had wetland areas erased.
# They read from a national database that has east and west coast communities all in the same layers.

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

# reproject levee data


def erase_leveed_area_from_state_inundation_layers(region, projections, years, state_numbers, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    usace_leveed_areas = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/national.gdb/usace_nld_leveed_area_proj'

    for projection in projections:

        for state_number in state_numbers:

            for year in years:

                print 'Projection is {0}, state number is {1}, and year is {2}' .format(projection, state_number, year)

                inundation_minus_mhhw_and_wetlands = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw' .format(flood_frequency, year, projection, state_number) # will need to do the different regions for FL and LA

                inundation_minus_levees = arcpy.Erase_analysis(inundation_minus_mhhw_and_wetlands, usace_leveed_areas,
                                                                          'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees'.format(
                                                                              flood_frequency, year, projection,
                                                                              state_number))

                print 'Erased leveed area from state {0} for {1} ' .format(state_number, year)

def erase_leveed_area_from_munis(region, state_numbers):
    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for state_number in state_numbers:
        print 'Starting state number ' + state_number

        municipalities = 'tl_2016_{0}_clip_no_wetlands_or_mhhw'.format(state_number)

        usace_leveed_areas = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/national.gdb/usace_nld_leveed_area_proj'


        municipalities_minus_levees = arcpy.Erase_analysis(municipalities, usace_leveed_areas,
                                                             'tl_2016_{0}_clip_no_wetlands_or_mhhw_or_levees'.format(
                                                                 state_number))

        print 'Erased levees from municipalities'

def update_results_for_munis_with_levees(projections, years, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/national.gdb'

    usace_leveed_areas = 'usace_nld_leveed_area_proj'

    #original_results = 'tl_2016_all_states_cousub_for_wetlands' # this is in national.gdb

    #original_results = 'tl_2016_all_states_cousub_for_wetlands_no_levees_testing'

    original_results_to_update = 'tl_2016_all_states_cousub_clip_for_wetlands_remove_levees'

    #arcpy.CopyFeatures_management(original_results, original_results_to_update)

    file_with_muni_area_to_join = 'tl_2016_all_states_no_wetlands_or_mhhw_or_levees'

    arcpy.MakeFeatureLayer_management(file_with_muni_area_to_join, 'municipalities_with_no_wetlands_or_mhhw_or_levees')

    arcpy.JoinField_management(original_results_to_update, "GEOID", file_with_muni_area_to_join, "GEOID", ["Shape_Area"])

    fields = arcpy.ListFields(original_results_to_update)

    for field in fields:

        print field.name

    arcpy.MakeFeatureLayer_management(original_results_to_update, 'original_results_to_update')

    arcpy.MakeFeatureLayer_management(usace_leveed_areas, 'usace_leveed_areas')

    arcpy.SelectLayerByLocation_management('original_results_to_update', "INTERSECT", 'usace_leveed_areas', "", "NEW_SELECTION")

    result = arcpy.GetCount_management('original_results_to_update')

    rows_to_update = int(result.getOutput(0))

    print 'There are {0} rows to be updated'.format(rows_to_update)

    for projection in projections:

        for year in years:

            fields = ["SHAPE@", "STATEFP", "COUNTYFP", "NAME", "Shape_Area", "Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection), "GEOID", "Shape_Area_1"]

            #print fields

            count = 0

            with arcpy.da.UpdateCursor('original_results_to_update', fields) as cursor:

                for row in cursor:

                    count = count + 1

                    print 'Count is: ' + str(count)
                    muni = row[0]
                    muni_state = row[1]
                    muni_county = row[2]
                    muni_name = row[3]
                    geoid = row[7]
                    total_muni_area = row[8]

                    outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni_022417_' + str(count)

                    print 'Year: ' + year + '; State number: ' + muni_state + '; Municipality: ' + muni_name

                    if muni_state in ['06','41','53']:

                        path = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/west_coast/west_coast.gdb/'

                    else:

                        path = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_coast.gdb/'

                    inundation_minus_mhhw_wetlands_and_levees = path + 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees'.format(
                                                                              flood_frequency, year, projection,
                                                                              muni_state)

                    arcpy.SelectLayerByAttribute_management('municipalities_with_no_wetlands_or_mhhw_or_levees', "NEW_SELECTION", " GEOID = '{0}' " .format(geoid))

                    if total_muni_area is None:

                        print 'Municipality area is None'

                    elif total_muni_area > 0:

                        arcpy.Clip_analysis(str(inundation_minus_mhhw_wetlands_and_levees), 'municipalities_with_no_wetlands_or_mhhw_or_levees', outname)

                        print 'Clipped inundation minus wetlands layer to municipality'

                        fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                        print 'Created clipped_inundation_surface_layer to municipality'

                        result = int(arcpy.GetCount_management(fc).getOutput(0))

                        if result == 0:
                            print 'Table is empty'
                            # writer = csv.writer(csvfile)
                            #
                            # writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, 0, year, projection, 0])
                            # print 'Wrote to csv'

                        else:

                            # get sum of all rows
                            output_table_name = 'output_sum_area_{0}' .format(str(count))

                            arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                            print 'Calculated stats'

                            sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                            print 'Inundated non-wetland, non-leveed area is: ' + str(sum_area[0]) + ', and municipality area is: ' + str(total_muni_area)

                            current_dry_area = total_muni_area

                            inundated_nonwetland_area = sum_area[0]

                            percent_inundated_nonwetland_area_minus_mhhw = (inundated_nonwetland_area/current_dry_area)*100

                            # writer = csv.writer(csvfile)
                            #
                            # writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year, projection, "%.2f" % sum_area[0], "%.2f" % percent_inundated_nonwetland_area_minus_mhhw])
                            # print 'Wrote to csv'

                            row[5] = inundated_nonwetland_area
                            row[6] = percent_inundated_nonwetland_area_minus_mhhw

                            cursor.updateRow(row)

                            del fc

def merge(projections, years, state_numbers, date):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_coast.gdb/'

    for state_number in state_numbers:

        for projection in projections:

            for year in years:

                #list_to_merge = arcpy.ListFeatureClasses('final_polygon_26x_{0}_{1}_merged_clip_to_{2}_no_wetlands_or_mhhw_{3}' .format(year, projection, state_number, date))

                to_merge = []

                for number in ['1','2','3']:

                    to_merge_file = 'final_polygon_26x_{0}_{1}_merged_clip_to_{2}_no_wetlands_or_mhhw_{3}_{4}' .format(year, projection, state_number, number, date)

                    to_merge.append(to_merge_file)

                print to_merge
                print len(to_merge)

                arcpy.Merge_management(to_merge, 'final_polygon_26x_{0}_{1}_merged_clip_to_{2}_no_wetlands_or_mhhw' .format(year, projection, state_number))

                print 'Merged files for {0} {1} state {2}' .format(year, projection, state_number)

def clip_la_inundation_files(projections, years, state_number, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_coast.gdb/'

    for projection in projections:

        for year in years:

            file_to_clip = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees' .format(flood_frequency, year, projection, state_number)

            clip_with = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

            arcpy.Clip_analysis(file_to_clip, clip_with, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees_clip' .format(flood_frequency, year, projection, state_number))

            print 'Clipped for {0}{1}' .format(year, projection)

def rename_inundation_files(projections, years, state_number, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_coast.gdb/'

    for projection in projections:

        for year in years:

            input_file_1 = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees' .format(flood_frequency, year, projection, state_number)

            output_file_1 = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees_old' .format(flood_frequency, year, projection, state_number)

            input_file_2 = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees_clip'.format(
                flood_frequency, year, projection, state_number)

            output_file_2 = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw_or_levees'.format(
                flood_frequency, year, projection, state_number)

            arcpy.Rename_management(input_file_1, output_file_1)

            print 'Renamed old file {0} {1}' .format(year, projection)

            arcpy.Rename_management(input_file_2, output_file_2)

            print 'Renamed new file {0} {1}' .format(year, projection)




# rename_inundation_files(['NCAH'], ['2006','2030','2045','2060','2070','2080','2090','2100'], '22','26')
# rename_inundation_files(['NCAI'], ['2035','2060','2080','2100'], '22','26')
# rename_inundation_files(['NCAL'], ['2060','2100'], '22','26')

#clip_la_inundation_files(['NCAL'],['2100'], '22','26')

#merge(['NCAH'],['2006','2030','2045'],['22'],'012317')
# update_results_for_munis_with_levees(['NCAI'], ['2100'], '26')
# update_results_for_munis_with_levees(['NCAL'], ['2060','2100'], '26')
update_results_for_munis_with_levees(['NCAH'],['2070','2080','2090','2100'],'26')

#erase_leveed_area_from_state_inundation_layers('east_coast',['NCAH'],['2006','2030','2045'],['22'],'26')





