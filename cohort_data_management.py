import csv
import pandas
import os
import arcpy
import glob

arcpy.env.overwriteOutput = True

def reorg_cohort_files(region, projection, years, state_numbers, area_threshold):

    path_to_data = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}' .format(region)

    state_codes = pandas.read_csv('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/state_numbers.csv', dtype={'Number': str})

    for year in years:

        csv_filename_results = path_to_data + '/cohort_municipalities_nowetlands_{0}_{1}percent_{2}_{3}_all_states.csv' .format(region, area_threshold, year, projection)

        with open(csv_filename_results, 'ab') as csvfile:

            for state_number in state_numbers:

                file_to_check = path_to_data + '/cohort_municipalities_nowetlands_by_year_{0}_{1}percent_{2}_state{3}.csv'.format(region, area_threshold, projection, state_number)

                if os.stat(file_to_check).st_size == 0:

                    print 'No inundated municipalities'

                else:

                    file_to_read = pandas.read_csv(file_to_check, header=None)

                    for index, row in state_codes.iterrows():

                        #print row[0]

                        if str(row[0]) == state_number:
                            state_abbr = row[1]

                    for index, row in file_to_read.iterrows():

                        #print row[0]

                        if str(row[0]) == year:

                            if row[2] == 'County subdivisions not defined':
                                print 'skipping'

                            else:

                                writer = csv.writer(csvfile)

                                writer.writerow([state_abbr, row[0], row[1],row[2], row[3]])

        print 'wrote file for year ' + year

def remove_leveed_area_and_aland0_from_merged_fc(gdb):

    arcpy.env.workspace = gdb

    #original_file =  gdb + 'all_states_nowetlands_10percent_cohort_{0}_{1}.shp' .format(year, projection)

    original_file = 'merge_tl_2016_all_states_for_wetlands'

    arcpy.MakeFeatureLayer_management(original_file, 'original_file')

    area_to_erase = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/munis_with_leveed_area.shp'

    outname_1 = 'merge_tl_2016_all_states_for_wetlands_erase_nola'

    print 'Using this original file: ' + original_file

    arcpy.Erase_analysis(original_file, area_to_erase, outname_1)

    print 'Erased NOLA area'

    arcpy.SelectLayerByAttribute_management('original_file', "NEW_SELECTION", ' "ALAND" = 0 ')

    arcpy.MakeFeatureLayer_management('original_file', 'tracts_with_aland0')

    outname_2 = 'merge_tl_2016_all_states_for_wetlands_erase_nola_and_aland0'

    arcpy.Erase_analysis(outname_1, 'tracts_with_aland0', outname_2)

    print 'Erased tracts with aland0'

def write_csv_from_shp(region, year, projection):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb'.format(region)

    state_codes = pandas.read_csv('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/state_numbers.csv',
                                  dtype={'Number': str})

    file_to_read = 'cohort_municipalities_nowetlands_{0}_10percent_NCAI_erase_NCAL' .format(year)

    print 'file to read is: ' + file_to_read

    csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/cohort_municipalities_nowetlands_10percent_in_NCAI_not_in_NCAL_{1}_{0}.csv' .format(region,year)

    with open(csv_filename, 'ab') as csvfile:

        fields = ["STATEFP", "COUNTYFP", "GEOID", "NAME", "Pct_inun_{0}_{1}".format(year, projection)]

        with arcpy.da.UpdateCursor(file_to_read, fields) as cursor:

            for shp_row in cursor:

                muni_state = shp_row[0]
                muni_county = shp_row[1]
                muni_geoid = shp_row[2]
                muni_name = shp_row[3]

                inundated_area = shp_row[4]

                for index, row in state_codes.iterrows():

                    # print row[0]

                    if str(row[0]) == muni_state:
                        state_abbr = row[1]

                writer = csv.writer(csvfile)

                writer.writerow([year, 'NCAI vs NCAL', state_abbr, muni_county, muni_name, "%.1f" % inundated_area])

                print 'Wrote to csv'

def cohort_id_csv(years, projections, region, area_threshold):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb'.format(region)

    state_codes = pandas.read_csv('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/state_numbers.csv',
                                  dtype={'Number': str})

    for projection in projections:

        for year in years:

            file_to_analyze = 'tl_2016_all_states_cousub_clip_for_wetlands_remove_levees_and_aland0'

            print file_to_analyze

            csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/all_states_cohort_municipalities_nowetlands_nolevees_{1}_{2}_{3}percent'.format(region, year, projection, str(area_threshold)) + '.csv'

            with open(csv_filename, 'ab') as csvfile:

                fields = ["STATEFP", "COUNTYFP", "GEOID", "NAME","Pct_inun_{0}_{1}".format(year, projection)]

                with arcpy.da.UpdateCursor(file_to_analyze, fields) as cursor:

                    for shp_row in cursor:

                        muni_state = shp_row[0]
                        muni_county = shp_row[1]
                        muni_geoid = shp_row[2]
                        muni_name = shp_row[3]

                        inundated_area = shp_row[4]

                        for index, row in state_codes.iterrows():

                            # print row[0]

                            if str(row[0]) == muni_state:

                                state_abbr = row[1]

                        if inundated_area >= area_threshold:

                            print str(muni_name) + ' is in cohort'

                            writer = csv.writer(csvfile)

                            writer.writerow([year, projection, state_abbr, muni_county, muni_name, "%.1f" % inundated_area])

                            print 'Wrote to csv'

def cohort_id_shp(years, projections, region, area_threshold):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb'.format(region)

    municipalities = 'merge_tl_2016_all_states_for_wetlands_erase_nola_and_aland0'

    arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

    for projection in projections:

        for year in years:

            field = 'Pct_inun_' + year + '_' + projection

            print field

            exp = ' "{0}" > {1} ' .format(field, area_threshold)

            print exp
            cohort_munis = arcpy.SelectLayerByAttribute_management('municipalities','NEW_SELECTION',' "{0}" > {1} ' .format(field, area_threshold) )

            outname = 'cohort_municipalities_nowetlands_{0}_{1}_{2}percent_erase_nola_and_aland0'.format(year, projection, str(area_threshold))

            arcpy.CopyFeatures_management(cohort_munis, outname)

def export_cohort_to_shapefile(years, projections, region, area_threshold):
    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb'.format(
        region)

    output_folder = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/cohort_shapefiles'.format(
        region)

    for projection in projections:

        for year in years:

            #to_export = arcpy.ListFeatureClasses('cohort_municipalities_nowetlands_{0}_{1}_{2}percent_erase_nola_and_aland0'.format(year, projection, area_threshold))

            to_export = arcpy.ListFeatureClasses('cohort_municipalities_nowetlands_{0}_{1}percent_NCAH_erase_NCA*' .format(year, area_threshold))

            print to_export

            for item in to_export:
                arcpy.FeatureClassToShapefile_conversion(item, output_folder)

                print 'Exported {0} {1} to shapefile'.format(year, projection)

def cohort_id_shp_non_levee(years, projections, region, area_threshold):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb'.format(
        region)

    municipalities = 'tl_2016_all_states_cousub_clip_for_wetlands_remove_levees_and_aland0'

    municipalities_layer = arcpy.MakeFeatureLayer_management(municipalities, 'municipalities')

    for projection in projections:

        for year in years:
            field = 'Pct_inun_' + year + '_' + projection

            print field

            exp = ' "{0}" > {1} '.format(field, area_threshold)

            print exp
            cohort_munis = arcpy.SelectLayerByAttribute_management('municipalities', 'NEW_SELECTION',
                                                                   ' "{0}" > {1} '.format(field,
                                                                                          area_threshold))

            outname = 'cohort_municipalities_nowetlands_nolevees_{0}_{1}_{2}percent'.format(year, projection, str(area_threshold))

            arcpy.CopyFeatures_management(cohort_munis, outname)

            output_folder = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/cohort_shapefiles'.format(
            region)

            arcpy.FeatureClassToShapefile_conversion(outname, output_folder)


cohort_id_csv(['2006','2030','2045','2060','2070','2080','2090','2100'],['NCAH'],'national',10)
cohort_id_csv(['2035','2060','2080','2100'], ['NCAI'], 'national', 10)
cohort_id_csv(['2060','2100'], ['NCAL'], 'national', 10)


#export_cohort_to_shapefile(['2060','2100'], ['NCAH'], 'national', 10)
# export_cohort_to_shapefile(['2035','2060','2080','2100'], ['NCAI'], 'national', 10)
# export_cohort_to_shapefile(['2060','2100'], ['NCAL'], 'national', 10)

#write_csv_from_shp('national','2060','NCAI')

# cohort_id_csv(['2030','2045','2060','2070','2080','2090','2100'], ['NCAH'], 'national', 10)
# cohort_id_csv(['2035','2060','2080','2100'], ['NCAI'], 'national', 10)
# cohort_id_csv(['2060','2100'], ['NCAL'], 'national', 10)

#cohort_id_shp(['2030','2045','2060','2070','2080','2090','2100'], ['NCAH'], 'national', 10)
#cohort_id_shp(['2035','2060','2080','2100'], ['NCAI'], 'national', 10)
#cohort_id_shp(['2060','2100'], ['NCAL'], 'national', 10)







