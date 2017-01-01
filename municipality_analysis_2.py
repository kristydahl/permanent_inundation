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

    state_numbers = ['48']

    for state_number in state_numbers:
        municipalities = 'tl_2016_{0}_cousub'.format(state_number)

        municipalities_proj = arcpy.Project_management(municipalities, str(municipalities + '_proj'), SR) # Test this

        municipalities_clipped_to_mhhw = arcpy.Clip_analysis(municipalities_proj,'all_noaa_mhhw_mosaic_polygon',str(municipalities + '_clip'))

        print 'Clipped state municipalities to NOAA mhhw polygon for state number: ' + state_number

        municipalities_dissolved = arcpy.Dissolve_management(municipalities_clipped_to_mhhw, str(municipalities + '_clip_diss') .format(state_number))

        print 'Dissolved municipalities'

def clip_mhhw_layer_to_states(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['12']
    #'13', '22', '23', '24', '25', '28', '33', '34', '36', '37', '42', '44', '45'

    for state_number in state_numbers:

        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        municipalities_outline = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities_outline, 'municipalities_outline')

        #mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon_mhhw_merged')[0]

        mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon*mhhw*fl_gulf')[0] #use this for FL and gulf_to_tx for LA

        print 'mhhw surface is ' + mhhw_inundation_surface

        #outname_mhhw = str(mhhw_inundation_surface + '_clip_to_{0}' .format(state_number))

        outname_mhhw = 'final_polygon_mhhw_merged_clip_to_{0}' .format(state_number) # change back to be more general

        arcpy.Clip_analysis(mhhw_inundation_surface, 'municipalities_outline', outname_mhhw)

        print 'Clipped MHHW surface to state: ' + state_number

        municipalities = 'tl_2016_{0}_cousub_clip' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

        arcpy.AddField_management('clipped_municipalities', "Area_MHHW", "FLOAT")

        print 'Added Area_MHHW fields'

def municipality_analysis_mhhw(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['22']

    for state_number in state_numbers:

        print 'State number is: ' + state_number
        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

        municipalities = 'tl_2016_{0}_cousub_clip' .format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

        state_mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon*mhhw_merged_clip_to_{0}' .format(state_number))[0]

        arcpy.RepairGeometry_management(state_mhhw_inundation_surface)

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

        print 'Finished municipality analysis for state number ' + state_number

def clip_extract_and_convert_to_polygon(years, projections, region, subregion, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['22']

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                print 'Year is ' + year+ ', state number is ' + state_number
                extract = arcpy.ListRasters('extract*{0}x_{1}_{2}_{3}' .format(flood_frequency, year, projection, subregion))[0] #UNCOMMENT FOR YEARS
                #extract = 'extract_{0}_{1}_{2}_{3}_mosaic' .format(flood_frequency, year, projection, subregion)

                #extract = arcpy.ListRasters('extract*mhhw_{0}_mosaic' .format(subregion))[0] # COMMENT FOR YEARS

                extract = 'extract_mhhw_clip_to_22'

                print 'File to clip is: ' + extract

                Xmin = str(arcpy.GetRasterProperties_management(extract, "LEFT").getOutput(0))

                Ymin = str(arcpy.GetRasterProperties_management(extract, "BOTTOM").getOutput(0))

                Xmax = str(arcpy.GetRasterProperties_management(extract, "RIGHT").getOutput(0))

                Ymax = str(arcpy.GetRasterProperties_management(extract, "TOP").getOutput(0))

                extents = '{0} {1} {2} {3}' .format(Xmin, Ymin, Xmax, Ymax)

                print extents

                outname = 'extract_{0}x_{1}_{2}_clip_to_{3}' .format(flood_frequency, year, projection, state_number) #UNCOMMENT FOR YEARS

                #outname = 'extract_mhhw_clip_to_{0}' .format(state_number) # COMMENT FOR YEARS
                arcpy.Clip_management(extract, "{0}" .format(extents), outname, 'tl_2016_{0}_cousub_clip_diss' .format(state_number), "#", "ClippingGeometry", "#")

                print 'Clipped extract to state number ' + state_number

                #extract_to_convert = Con(Raster(extract)>0, 1) # COMMENT OUT!!!
                extract_to_convert = Con(Raster(outname)>0, 1) # UNCOMMENT

                arcpy.RasterToPolygon_conversion(extract_to_convert, 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}' .format(flood_frequency, year, projection, state_number)) #UNCOMMENT FOR YEARS

                #arcpy.RasterToPolygon_conversion(extract_to_convert,'final_polygon_mhhw_merged_clip_to_{0}'.format(state_number)) # COMMENT FOR YEARS

                print 'Converted state {0} {1} {2} to polygon' .format(state_number, year, projection)

def clip_inundation_layers_to_states(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    #state_numbers left to do: 12, 22, 28
    #state_numbers = ['01', '09', '10', '11', '13', '23', '24', '25', '33', '34', '36', '37', '42', '44', '45']
    state_numbers = ['09']
    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

                municipalities_outline = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities_outline, 'municipalities_outline')

                inundation_surface = 'final_polygon_{0}x_{1}_{2}_merged' .format(flood_frequency, year, projection)

                #inundation_surface = 'final_polygon*{0}x_{1}_{2}_fl_gulf'.format(flood_frequency, year, projection)

                outname_inundation_surface = str(inundation_surface + '_clip_to_{0}'.format(state_number))

                arcpy.Clip_analysis(inundation_surface, 'municipalities_outline', outname_inundation_surface)

                print 'Clipped {0} {1} inundation surface to state {2}' .format(year, projection, state_number)


def municipality_analysis_year(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['22']
    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss' .format(state_number)

                print 'Year is: ' + year + ' and projection is: ' + projection

                municipalities = 'tl_2016_{0}_cousub_clip'.format(state_number)

                arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_area_'.format(region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename, 'wb') as csvfile:

                    state_inundation_surface = arcpy.ListFeatureClasses(
                        'final_polygon*{0}x_{1}_{2}_merged_clip_to_{3}'.format(flood_frequency, year, projection, state_number))[0]

                    arcpy.RepairGeometry_management(state_inundation_surface)

                    print 'Repaired geometry of inundation layer'

                    arcpy.AddField_management('clipped_municipalities', "Area_inun_{0}_{1}".format(year, projection), "FLOAT")

                    arcpy.AddField_management('clipped_municipalities',"Pct_inun_{0}_{1}".format(year, projection), "FLOAT")

                    print 'Added Area and Percent inundation fields'

                    arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", state_inundation_surface, "", "NEW_SELECTION")

                    fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Shape_Area", "Area_MHHW", "Area_inun_{0}_{1}" .format(year, projection), "Pct_inun_{0}_{1}".format(year, projection)]

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

                            outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni_' + str(count)

                            print 'Year is: ' + year + ' and state number is ' + state_number

                            print 'Municipality is: ' + muni_name

                            print 'Total muni area is: ' + str(total_muni_area)

                            print 'MHHW area is: ' + str(mhhw_area)


                            if total_muni_area is None:

                                print 'Municipality area is None'

                            elif total_muni_area > 0:

                                arcpy.Clip_analysis(str(state_inundation_surface), muni, outname)

                                print 'Clipped inundation surface layer to tract'

                                fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                #print result

                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, "%.2f" % muni_water_area, year, projection, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows in Area_acres
                                    output_table_name = 'output_sum_area_{0}' .format(str(count))

                                    arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    print 'Inundated area is: ' + str(sum_area[0]) + ', mhhw_area is: ' + str(mhhw_area) + ', and municipality area is: ' + str(total_muni_area)


                                    if mhhw_area is None:

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

        print 'Finished municipality analysis for state number ' + state_number + ' for {0} {1}' .format(year, projection)

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


def mosaic_extracts(years, projections, region, flood_frequency, state_center):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            print 'Year is ' + year + ' and projection is ' + projection
            to_mosaic = arcpy.ListRasters('extract*{0}_{1}*{2}*' .format(year, projection, state_center))

            #to_mosaic = arcpy.ListRasters('extract*mhhw*{0}*'.format(state_center))

            print to_mosaic

            arcpy.MosaicToNewRaster_management(to_mosaic, workspace, 'extract_{0}_{1}_{2}_{3}_mosaic' .format(flood_frequency, year, projection, state_center), '#',"32_BIT_FLOAT","#",'1')

            #arcpy.MosaicToNewRaster_management(to_mosaic, workspace,'extract_mhhw_{0}_mosaic'.format(state_center), '#', "32_BIT_FLOAT", "#", '1')

            print 'Mosaic done'

def municipality_analysis_mhhw_la(region):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    state_numbers = ['22']

    for state_number in state_numbers:

        print 'State number is: ' + state_number
        arcpy.env.extent = 'tl_2016_{0}_cousub_clip_diss'.format(state_number)

        municipalities = 'tl_2016_{0}_cousub_clip'.format(state_number)

        arcpy.MakeFeatureLayer_management(municipalities, 'clipped_municipalities')

        state_mhhw_inundation_surface = arcpy.ListRasters('extract_mhhw_clip_to_{0}' .format(state_number))[0]

        polygon_layer = arcpy.ListFeatureClasses('final_polygon_*mhhw_merged_clip_to_{0}'.format(state_number))[0]

        arcpy.SelectLayerByLocation_management('clipped_municipalities', "INTERSECT", polygon_layer, "",
                                               "NEW_SELECTION")


        Xmin = str(arcpy.GetRasterProperties_management(state_mhhw_inundation_surface, "LEFT").getOutput(0))

        Ymin = str(arcpy.GetRasterProperties_management(state_mhhw_inundation_surface, "BOTTOM").getOutput(0))

        Xmax = str(arcpy.GetRasterProperties_management(state_mhhw_inundation_surface, "RIGHT").getOutput(0))

        Ymax = str(arcpy.GetRasterProperties_management(state_mhhw_inundation_surface, "TOP").getOutput(0))

        extents = '{0} {1} {2} {3}'.format(Xmin, Ymin, Xmax, Ymax)

        print extents

        fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Shape_Area", "Area_MHHW"]

        count = 0

        with arcpy.da.UpdateCursor('clipped_municipalities', fields) as cursor:

            for row in cursor:

                count = count + 1
                muni = row[0]
                muni_land_area = row[1]
                muni_state = row[2]
                muni_county = row[3]
                muni_name = row[4]
                muni_water_area = row[5]
                total_muni_area = row[6]

                #print 'total muni area is: ' + str(total_muni_area)

                outname = 'clip_mhhw_inundation_surface_to_muni_' + str(count)

                if total_muni_area is None:

                    print 'Municipality area is None'

                elif total_muni_area > 0:

                    arcpy.Clip_management(state_mhhw_inundation_surface, "{0}".format(extents), outname, muni, "#", "ClippingGeometry", "#")

                    print 'Clipped inundation surface layer to tract'

                    extract_to_convert = Con(Raster(outname) > 0, 1)

                    arcpy.RasterToPolygon_conversion(extract_to_convert, 'clipped_inundation_surface_layer')

                    fc = arcpy.MakeFeatureLayer_management('clipped_inundation_surface_layer', 'clipped_inundation_surface_layer')

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

                        print 'State: ' + str(state_number) + '; Inundated area is: ' + str(
                            sum_area[0]) + ' and municipality area is: ' + str(total_muni_area)

                        # row[7] = (sum_area[0]/total_muni_area) * 100
                        row[7] = sum_area[0]

                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                        cursor.updateRow(row)

                    del fc

                else:
                    print 'Land area is 0.'

        print 'Finished municipality analysis for state number ' + state_number
#mosaic_extracts(['2006'], ['NCAH'], 'east_coast','26','nc')


# run in this order:

#clip_to_tracts_then_mhhw_polygon('east_coast')
#clip_mhhw_layer_to_states('east_coast')

#municipality_analysis_mhhw_la('east_coast')
#clip_inundation_layers_to_states(['2100'],['NCAI'],'east_coast','26')

#clip_extract_and_convert_to_polygon(['2006'], ['NCAH'], 'east_coast', 'fl_gulf', '26')

municipality_analysis_year(['2006','2030'], ['NCAH'], 'east_coast', '26')
#municipality_analysis_year(['2035'], ['NCAI'], 'east_coast', '26')
#municipality_analysis_year(['2035','2060','2080','2100'], ['NCAI'], 'east_coast', '26')
#municipality_analysis_year(['2035','2060','2080','2100'], ['NCAI'], 'east_coast', '26')
#cohort_id_shp(['2006','2030','2045','2060','2070','2080','2090','2100'],['NCAH'],'east_coast',['36'], 20)
#zip(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast',['48'])

#,'09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'