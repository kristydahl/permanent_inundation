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

def clip_to_tracts_then_mhhw_polygon(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    file_with_projection = 'all_noaa_mhhw_mosaic_polygon'

    desc = arcpy.Describe(file_with_projection)
    SR = desc.SpatialReference

    print SR

    state_numbers = ['51']

    for state_number in state_numbers:
        municipalities = 'tl_2016_{0}_cousub'.format(state_number)

        municipalities_proj = arcpy.Project_management(municipalities, str(municipalities + '_proj'), SR) # Test this

        municipalities_clipped_to_mhhw = arcpy.Clip_analysis(municipalities_proj,'all_noaa_mhhw_mosaic_polygon',str(municipalities + '_clip'))

        print 'Clipped state municipalities to NOAA mhhw polygon for state number: ' + state_number

        municipalities_dissolved = arcpy.Dissolve_management(municipalities_clipped_to_mhhw, str(municipalities + '_clip_diss') .format(state_number))

        print 'Dissolved municipalities'

def clip_mhhw_layer_to_states(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['51']

    for state_number in state_numbers:

        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        municipalities_outline = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities_outline, 'municipalities_outline')

        mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon_mhhw_merged')[0]

        outname_mhhw = str(mhhw_inundation_surface + '_clip_to_{0}' .format(state_number))

        arcpy.Clip_analysis(mhhw_inundation_surface, 'municipalities_outline', outname_mhhw)

        print 'Clipped MHHW surface to state: ' + state_number

        municipalities = 'tl_2016_{0}_cousub_clip' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

        arcpy.AddField_management('clipped_municipalities', "Area_MHHW", "FLOAT")

        print 'Added Area_MHHW fields'

def municipality_analysis_mhhw(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['51']

    for state_number in state_numbers:

        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        municipalities = 'tl_2016_{0}_cousub_clip' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

        state_mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon*mhhw_clip_to_{0}' .format(state_number))[0]

        arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", state_mhhw_inundation_surface, "","NEW_SELECTION")

        print 'Selected layer'

        fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Shape_Area", "Area_MHHW"]

        with arcpy.da.UpdateCursor('clipped_municipalities',fields) as cursor:

            for row in cursor:

                muni = row[0]
                muni_land_area = row[1]
                muni_state = row[2]
                muni_county = row[3]
                muni_name = row[4]
                muni_water_area = row[5]
                total_muni_area = row[6]

                print 'total muni area is: ' + str(total_muni_area)

                outname = 'clip_mhhw_inundation_surface_to_muni'

                if total_muni_area is None:

                    print 'Municipality area is None'

                elif total_muni_area > 0:

                    arcpy.Clip_analysis(str(state_mhhw_inundation_surface), muni, outname)

                    print 'Clipped inundation surface layer to tract'

                    fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                    print 'Created clipped_mhhw_inundation_surface_layer to municipality'

                    result = int(arcpy.GetCount_management(fc).getOutput(0))

                    print result


                    if result == 0:
                        print 'Table is empty'

                    else:

                        # get sum of all rows in Area_acres
                        output_table_name = 'output_sum_area'

                        arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                        print 'Calculated stats'

                        sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                        print 'State: ' + str(state_number) + '; Inundated area is: ' + str(sum_area[0]) + ' and municipality area is: ' + str(total_muni_area)

                        #row[7] = (sum_area[0]/total_muni_area) * 100
                        row[7] = sum_area[0]

                    # Update the census tracts layer with the % inundation for that tract for the year-projection field
                        cursor.updateRow(row)

                    del fc

                else:
                    print 'Land area is 0.'


def clip_inundation_layers_to_states(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['51']

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

                municipalities_outline = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities_outline, 'municipalities_outline')

                inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}_{1}_{2}_clip_to_{0}' .format(flood_frequency, year, projection, state_number))[0]

                outname_inundation_surface = str(inundation_surface + '_clip_to_{0}'.format(state_number))

                arcpy.Clip_analysis(inundation_surface, 'municipalities_outline', outname_inundation_surface)

                print 'Clipped {0} {1} inundation surface to state {2}' .format(year, projection, state_number)


def municipality_analysis_year(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)

    state_numbers = ['48']

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                print 'Year is: ' + year + ' and projection is: ' + projection

                municipalities = 'tl_2016_{0}_cousub3_clip_proj'.format(state_number)

                municipalities_layer = arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_area_'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:

                    #inundation_surface = arcpy.ListFeatureClasses('final_polygon_{0}x_{1}_{2}_merged'.format(flood_frequency, year, projection))[0] # need to get this into parameters

                    state_inundation_surface = arcpy.ListFeatureClasses(
                        'final_polygon*{0}x_{1}_{2}_gulf_to_tx_clip_to_48'.format(flood_frequency, year, projection))[0]  # need to get this into parameters
                    #inundation_surface = 'final_polygon_extract_rg_merged_raw_raster_surface_26x_2045_NCAH_me_to_nj_clip_to_36'  # need to get this into parameters

                    #outname = str(inundation_surface + '_clip_to_{0}'.format(state_number))

                    #state_inundation_surface = arcpy.Clip_analysis(inundation_surface,'clipped_municipalities', outname)

                    #print 'Clipped inundation surface to state'

                    arcpy.AddField_management('clipped_municipalities', "Area_inun_{0}_{1}".format(year, projection), "FLOAT")

                    arcpy.AddField_management('clipped_municipalities',"Pct_inun_{0}_{1}".format(year, projection), "FLOAT")

                    print 'Added Area and Percent inundation fields'

                    arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", state_inundation_surface, "", "NEW_SELECTION")

                    #fields = ["SHAPE@","ALAND","STATEFP","COUNTYFP","NAME","AWATER","Tot_area","Pct_inun_MHHW","Pct_inun_{0}_{1}" .format(year, projection)]

                    fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Shape_Area", "Area_MHHW", "Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

                    with arcpy.da.UpdateCursor(municipalities_layer, fields) as cursor:
                        for row in cursor:

                            muni = row[0]
                            muni_land_area = row[1]
                            muni_state = row[2]
                            muni_county = row[3]
                            muni_name = row[4]
                            muni_water_area = row[5]
                            total_muni_area = row[6]
                            mhhw_area = row[7]

                            outname_2 = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni'

                            print 'Municipality is: ' + muni_name

                            print 'Total muni area is: ' + str(total_muni_area)

                            print 'MHHW area is: ' + str(mhhw_area)


                            if total_muni_area is None:

                                print 'Municipality area is None'

                            elif total_muni_area > 0:

                                arcpy.Clip_analysis(str(state_inundation_surface), muni, outname_2)

                                print 'Clipped inundation surface layer to tract'

                                fc = arcpy.MakeFeatureLayer_management(outname_2, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                print result

                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, "%.2f" % muni_water_area, year, projection, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows in Area_acres
                                    output_table_name = 'output_sum_area'

                                    arcpy.Statistics_analysis(fc, output_table_name,
                                                              [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    print 'Inundated area is: ' + str(sum_area[0]) + ', and mhhw_area is: ' + str(mhhw_area) + ', and municipality area is: ' + str(total_muni_area)


                                    if mhhw_area is None:

                                        #percent_inundated_area_minus_mhhw = (sum_area[0]/total_muni_area)*100

                                        current_dry_area = total_muni_area

                                        newly_inundated_area = sum_area[0]

                                        percent_inundated_area_minus_mhhw = (newly_inundated_area/current_dry_area)*100

                                        writer = csv.writer(csvfile)

                                        writer.writerow(
                                            [muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year,
                                             projection, "%.2f" % sum_area[0],
                                             "%.2f" % percent_inundated_area_minus_mhhw])

                                        print 'Wrote to csv'

                                        row[8] = newly_inundated_area
                                        row[9] = percent_inundated_area_minus_mhhw

                                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                        cursor.updateRow(row)

                                    else:
                                        #percent_inundated_area_minus_mhhw = (sum_area[0]/total_muni_area)*100 - mhhw_percent_area

                                        current_dry_area = total_muni_area - mhhw_area

                                        total_inundated_area = sum_area[0]
                                        newly_inundated_area = sum_area[0] - mhhw_area

                                        percent_inundated_area_minus_mhhw = (newly_inundated_area/current_dry_area)*100

                                        writer = csv.writer(csvfile)


                                        writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, year, projection, "%.2f" % sum_area[0], "%.2f" % percent_inundated_area_minus_mhhw])
                                        print 'Wrote to csv'

                                        row[8] = total_inundated_area
                                        row[9] = percent_inundated_area_minus_mhhw

                                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                        cursor.updateRow(row)

                                del fc

                            else:
                                print 'Land area is 0.'

                # census_area_analysis(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast','26')

def cohort_id_csv(years, projections, region, state_numbers, area_threshold):

    path = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/'.format(region)

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                file_to_analyze = glob.glob1(path,'inundated_muni_area*{0}_{1}_{2}*' .format(year, projection, state_number))[0]

                file_with_path = str(path + file_to_analyze)

                print file_to_analyze

                inundated_area_data = numpy.genfromtxt(file_with_path, dtype=None, delimiter=',', skip_header=0)

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/cohort_municipalities_by_year_{0}_{1}_state{2}' .format(region, projection, state_number) + '.csv'

                with open(csv_filename, 'ab') as csvfile:

                    for row in inundated_area_data:

                        muni_name = row[2]

                        inundated_area = row[7]

                        if inundated_area >= area_threshold:

                            print muni_name + ' is in cohort'

                            writer = csv.writer(csvfile)

                            writer.writerow([year, projection, muni_name, "%.1f" % inundated_area])

                            print 'Wrote to csv'

def cohort_id_shp(years, projections, region, state_numbers, area_threshold):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)

    for state_number in state_numbers:

        municipalities = 'tl_2016_{0}_cousub2_clip' .format(state_number)

        municipalities_layer = arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

        for projection in projections:

            for year in years:

                field = 'Pct_inun_' + year + '_' + projection

                print field

                exp = ' "{0}" > {1} ' .format(field, area_threshold)

                print exp
                cohort_munis = arcpy.SelectLayerByAttribute_management('municipalities','NEW_SELECTION',' "{0}" > {1} ' .format(field, area_threshold) )

                outname = 'cohort_municipalities_{0}_{1}_{2}percent_state{3}' .format(year, projection, str(area_threshold), state_number)

                arcpy.CopyFeatures_management(cohort_munis, outname)

                #output_folder = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/cohort_shapefiles' .format(region)

                #arcpy.FeatureClassToShapefile_conversion(outname, output_folder)

def export_to_shapefile(years, projections, region, state_numbers):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)

    output_folder = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundation_surfaces_by_state_shapefiles'.format(region)

    for state_number in state_numbers:
        to_export = arcpy.ListFeatureClasses('final_polygon*clip_to_{0}' .format(state_number))

        print to_export

        for item in to_export:

            arcpy.FeatureClassToShapefile_conversion(item, output_folder)

def zip(years, projections, region, state_numbers):


    path = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundation_surfaces_by_state_shapefiles'.format(
        region)

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcname = os.path.join(path, 'final_polygon_{0}_{1}_state{2}' .format(year, projection, state_number))

                print arcname

                files_to_archive = glob.glob1(path, 'final_polygon*{0}_{1}*clip_to_{2}*' .format(year, projection, state_number))

                print files_to_archive

                zf = zipfile.ZipFile('{0}.zip' .format(arcname),'w',zipfile.ZIP_DEFLATED)

                for file in files_to_archive:

                    zf.write(os.path.join(path, file), arcname)

                    print 'Wrote ' + file + ' to archive'

                zf.close()








#clip_to_tracts_then_mhhw_polygon('east_coast')
clip_mhhw_layer_to_states('east_coast')

#municipality_analysis_mhhw('east_coast')
#municipality_analysis_year(['2060','2070','2080','2090'], ['NCAH'], 'east_coast', '26')

#cohort_id_shp(['2006','2030','2045','2060','2070','2080','2090','2100'],['NCAH'],'east_coast',['36'], 20)
#zip(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast',['48'])

#,'09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'