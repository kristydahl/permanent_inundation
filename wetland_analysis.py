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
        wetlands_data = 'wetlands_orig_{0}'.format(state_number)

        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

        state_muni_boundary = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

        print 'wetlands file is: ' + wetlands_data

        outname = 'wetlands_{0}_proj'.format(state_number)

        arcpy.Project_management(wetlands_data .format(state_number), outname, SR)

        print 'Projected wetlands data'
        arcpy.Clip_analysis(outname,state_muni_boundary,str('wetlands_{0}_clip_proj' .format(state_number)))

        print 'Clipped wetlands to NOAA mhhw polygon for state number: ' + state_number

        municipalities = 'tl_2016_{0}_cousub_proj'.format(state_number)

        arcpy.Clip_analysis(municipalities, 'all_noaa_mhhw_mosaic_polygon', str('tl_2016_{0}_cousub_clip_for_wetlands'.format(state_number)))

        print 'Clipped state municipalities to NOAA mhhw polygon for state number: ' + state_number


def municipality_wetlands_analysis(years, projections, region, flood_frequency, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for state_number in state_numbers:

            print 'Starting state number ' + state_number

            # municipalities = 'tl_2016_{0}_cousub_clip_for_wetlands'.format(state_number) # UNCOMMENT WHEN BACK TO NORMAL; comment when running second scenario
            #
            # print 'Municipalities file is: ' + municipalities

            municipalities = 'tl_2016_{0}_clip_no_wetlands_or_mhhw' .format(state_number) # COMMENT WHEN BACK TO NORMAL; uncomment when running second scenario

            wetlands = 'wetlands_{0}_clip_proj'.format(state_number)
#
#             print 'Wetlands file is: ' + wetlands
#
#             #arcpy.RepairGeometry_management(wetlands)
#
#             #print 'Repaired geometry of wetlands layer'
#
            state_mhhw_surface = 'final_polygon_mhhw_merged_clip_to_{0}'.format(state_number)
#
#             print 'State MHHW surface is: ' + state_mhhw_surface
#
# # UNCOMMENT THROUGH ### when running second scenario
#             municipalities_minus_wetlands = arcpy.Erase_analysis(municipalities, wetlands,'tl_2016_{0}_clip_no_wetlands'.format(state_number))
#
#             print 'Erased wetlands from municipalities'
#
#             municipalities_minus_mhhw_and_wetlands = arcpy.Erase_analysis(municipalities_minus_wetlands, state_mhhw_surface, 'tl_2016_{0}_clip_no_wetlands_or_mhhw'.format(state_number))
#
#             print 'Erased MHHW from municipalities'
#
#             arcpy.MakeFeatureLayer_management(municipalities_minus_mhhw_and_wetlands, 'clipped_municipalities')
#
#             result = arcpy.GetCount_management('clipped_municipalities')
#             muni_rows = int(result.getOutput(0))
#
#             print 'State has {0} municipality rows' .format(muni_rows)

###
            arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities') # UNCOMMENT when running second scenario
            result = arcpy.GetCount_management('clipped_municipalities')
            muni_rows = int(result.getOutput(0))
            print 'State has {0} municipality rows' .format(muni_rows)

            for year in years:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

                print 'Year is: ' + year + ' and projection is: ' + projection

                arcpy.AddField_management('clipped_municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('clipped_municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields'

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:

                    state_inundation_surface = arcpy.ListFeatureClasses('final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}'.format(flood_frequency, year, projection, state_number))[0]

                    #state_inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}x_{1}_{2}*clip_to_{3}'.format(flood_frequency, year, projection, state_number))[0] # This state_inundation_surface just for TX

                    print 'state inundation surface is: ' + state_inundation_surface

                    arcpy.RepairGeometry_management(state_inundation_surface) # UNCOMMENT FOR NORMAL

                    print 'Repaired geometry of state inundation surface' # UNCOMMENT FOR NORMAL

                    inundation_minus_wetlands = arcpy.Erase_analysis(state_inundation_surface, wetlands, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands'.format(flood_frequency, year, projection, state_number))

                    print 'Erased wetlands from inundation layer'

                    inundation_minus_mhhw_and_wetlands = arcpy.Erase_analysis(inundation_minus_wetlands, state_mhhw_surface, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw'.format(flood_frequency, year, projection, state_number))

                    print 'Erased MHHW from inundation layer'


                    #inundation_minus_mhhw_and_wetlands = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}_no_wetlands_or_mhhw'.format(flood_frequency, year, projection, state_number) # COMMENT OUT

                    arcpy.MakeFeatureLayer_management(inundation_minus_mhhw_and_wetlands, 'inundation_minus_mhhw_and_wetlands')


                    arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", 'inundation_minus_mhhw_and_wetlands', "", "NEW_SELECTION")


                    fields = ["SHAPE@", "STATEFP", "COUNTYFP", "NAME", "Shape_Area", "Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

                    print fields

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

                                    current_dry_area = total_muni_area

                                    inundated_nonwetland_area = sum_area[0]

                                    percent_inundated_nonwetland_area_minus_mhhw = (inundated_nonwetland_area/current_dry_area)*100

                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year, projection, "%.2f" % sum_area[0], "%.2f" % percent_inundated_nonwetland_area_minus_mhhw])
                                    print 'Wrote to csv'

                                    row[5] = inundated_nonwetland_area
                                    row[6] = percent_inundated_nonwetland_area_minus_mhhw

                                    cursor.updateRow(row)

                            del fc


        print 'Finished municipality analysis for state number ' + state_number + ' for {0} {1}' .format(year, projection)


def collate_shp_municipalities_and_write_csv(years, projections, region, flood_frequency, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                municipalities = 'tl_2016_{0}_clip_for_wetlands' .format(state_number)

                file_with_results = 'tl_2016_{0}_clip_no_wetlands_or_mhhw' .format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

                arcpy.MakeFeatureLayer_management(file_with_results, 'to_read')

                arcpy.AddField_management('municipalities', "Area_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                arcpy.AddField_management('municipalities', "Pct_inun_{0}_{1}".format(year, projection),
                                          "FLOAT")

                print 'Added Area and Percent inundation fields to municipalities file'


                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_nonwetland_area_summary'.format(
                    region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:
                    fields = ['GEOID', "STATEFP", "COUNTYFP", "NAME", "Area_inun_{0}_{1}".format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

                    with arcpy.da.UpdateCursor('municipalities', fields) as cursor:
                        for row in cursor:

                            geoid = row[0]
                            muni_state = row[1]
                            muni_county = row[2]
                            muni_name = row[3]

                            fc = arcpy.SelectLayerByAttribute_management('to_read',"GEOID = {0}" .format(geoid))

                            output_table_name_total = 'output_total_area'

                            output_table_name_inundated = 'output_inundated_area'

                            arcpy.Statistics_analysis(fc, output_table_name_total, [["Shape_Area", "SUM"]])

                            arcpy.Statistics_analysis(fc,output_table_name_inundated [["Area_inun_{0}_{1}".format(year, projection), "SUM"]])


                            print 'Calculated stats'

                            total_area = arcpy.da.TableToNumPyArray(output_table_name_total, 'SUM_Shape_Area')[0]

                            inundated_area = arcpy.da.TableToNumPyArray(output_table_name_inundated, 'SUM_Area_inun{0}_{1}' .format(year, projection))[0]

                            percent_inundated = (inundated_area/total_area)*100

                            row[4] = inundated_area
                            row[5] = percent_inundated

                            cursor.UpdateRow(row)

                            writer = csv.writer(csvfile)

                            writer.writerow(
                                [muni_state, muni_county, muni_name, "%.2f" % total_area, year, projection, "%.2f" % inundated_area[0], "%.2f" % percent_inundated])



#prep_wetlands_data('east_coast',['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45'])

def erase_wetlands_and_mhhw_from_municipalities(region, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for state_number in state_numbers:
        print 'Starting state number ' + state_number

        municipalities_orig = 'tl_2016_{0}_cousub_proj'.format(state_number)

        municipalities = arcpy.Clip_analysis(municipalities_orig, 'all_noaa_mhhw_mosaic_polygon',
                                             str('tl_2016_{0}_cousub_clip_for_wetlands'.format(state_number)))

        print 'Clipped state municipalities to NOAA mhhw polygon for state number: ' + state_number

        wetlands = 'wetlands_{0}_clip_proj'.format(state_number)

        print 'Wetlands file is: ' + wetlands

        state_mhhw_surface = 'final_polygon_mhhw_merged_clip_to_{0}'.format(state_number)

        print 'State MHHW surface is: ' + state_mhhw_surface

        municipalities_minus_wetlands = arcpy.Erase_analysis(municipalities, wetlands,
                                                             'tl_2016_{0}_clip_no_wetlands'.format(
                                                                 state_number))

        print 'Erased wetlands from municipalities'

        municipalities_minus_mhhw_and_wetlands = arcpy.Erase_analysis(municipalities_minus_wetlands,
                                                                      state_mhhw_surface,
                                                                      'tl_2016_{0}_clip_no_wetlands_or_mhhw'.format(
                                                                          state_number))

        print 'Erased MHHW from municipalities'

        arcpy.MakeFeatureLayer_management(municipalities_minus_mhhw_and_wetlands, 'clipped_municipalities')

        result = arcpy.GetCount_management('clipped_municipalities')
        muni_rows = int(result.getOutput(0))

        print 'State {0} has {1} municipality rows'.format(state_number, muni_rows)


#erase_wetlands_and_mhhw_from_municipalities('east_coast',['13'])

municipality_wetlands_analysis(['2006'], ['NCAH'], 'east_coast','26',['22'])


#municipality_wetlands_analysis(['2080','2090','2100'], ['NCAH'], 'east_coast','26',['13'])

# LEFT TO RUN': 12 (NCAH 2090 and 2100); 13 (NCAH, need to remake MHHW layer first); 22 (NCAH 2045 through 2100)
#'2006','2030','2045','2060','2070','2080','2090','2100'

#,'2030','2045','2060','2070','2080','2090','2100'
#,'25','28','33','34','36','42','45','48','51'