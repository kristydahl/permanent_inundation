import arcpy

arcpy.env.overwriteOutput = True

def identify_inundated_tracts(region, years, projections, state_numbers, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    high_vulnerability_tracts = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/national.gdb/all_coastal_census_tracts_high_vulnerability'

    arcpy.MakeFeatureLayer_management(high_vulnerability_tracts, 'tracts')

    for projection in projections:

        for year in years:

            for state_number in state_numbers:

                print 'Year is {0}, state number is {1}' .format(year, state_number)

                inundated_area = arcpy.ListFeatureClasses('final_polygon*{0}x_{1}_{2}*clip_to_{3}' .format(flood_frequency, year, projection, state_number))[0] #JUST FOR TX

                #inundated_area = 'final_polygon_{0}x_{1}_{2}_merged_clip_to_{3}' .format(flood_frequency, year, projection, state_number) #UNCOMMENT FOR STATES OTHER THAN TX

                inundated_tracts = arcpy.SelectLayerByLocation_management('tracts','INTERSECT', inundated_area)

                print 'Selected tracts within inundated area'

                outname = 'inundated_high_vulnerability_tracts_{0}x_{1}_{2}_state{3}' .format(flood_frequency, year, projection, state_number)

                arcpy.CopyFeatures_management(inundated_tracts, outname)

def merge_tracts_from_all_states(region, years, projections, state_numbers, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            list_to_merge = arcpy.ListFeatureClasses('inundated_high_vulnerability_tracts_{0}x_{1}_{2}_state*' .format(flood_frequency, year, projection))

            outname = 'all_states_inundated_high_vulnerability_tracts_{0}x_{1}_{2}' .format(flood_frequency, year, projection)

            arcpy.Merge_management(list_to_merge, outname)

            print 'Merged tracts for {0} {1}' .format(year, projection)

def remove_leveed_area_and_aland0_from_merged_fc(region, years, projections, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    for projection in projections:

        for year in years:

            original_file = 'all_states_inundated_high_vulnerability_tracts_{0}x_{1}_{2}' .format(flood_frequency, year, projection)

            arcpy.MakeFeatureLayer_management(original_file, 'original_file')

            area_to_erase = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results/munis_with_leveed_area.shp'

            outname = original_file + '_erase_nola'

            print 'Using this original file: ' + original_file

            arcpy.Erase_analysis(original_file, area_to_erase, outname)

            print 'Erased NOLA area'


# identify_inundated_tracts('west_coast', ['2006','2030', '2045', '2060', '2070', '2080', '2090', '2100'], ['NCAH'],['06','41','53'], '26')
# identify_inundated_tracts('west_coast', ['2035', '2060', '2080', '2100'], ['NCAI'], ['06','41','53'], '26')
# identify_inundated_tracts('west_coast', ['2060', '2100'], ['NCAL'], ['06','41','53'], '26')

# identify_inundated_tracts('east_coast', ['2030','2045','2060','2070','2080','2090','2100'], ['NCAH'], ['48'], '26')
# identify_inundated_tracts('east_coast', ['2035','2060','2080','2100'], ['NCAI'], ['48'], '26')
# identify_inundated_tracts('east_coast', ['2060','2100'], ['NCAL'], ['48'], '26')


# merge_tracts_from_all_states('east_coast', ['2006','2030', '2045', '2060', '2070', '2080', '2090', '2100'], ['NCAH'], ['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','51'], '26')
#
# merge_tracts_from_all_states('east_coast', ['2035', '2060', '2080', '2100'], ['NCAI'], ['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','51'], '26')
#
# merge_tracts_from_all_states('east_coast', ['2060', '2100'], ['NCAL'], ['01','09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','51'], '26')
#
# merge_tracts_from_all_states('west_coast', ['2006','2030', '2045', '2060', '2070', '2080', '2090', '2100'], ['NCAH'], ['06','41','53'], '26')
#
# merge_tracts_from_all_states('west_coast', ['2035', '2060', '2080', '2100'], ['NCAI'], ['06','41','53'], '26')
#
# merge_tracts_from_all_states('west_coast', ['2060', '2100'], ['NCAL'], ['06','41','53'], '26')

remove_leveed_area_and_aland0_from_merged_fc('east_coast', ['2006','2030', '2045', '2060', '2070', '2080', '2090', '2100'], ['NCAH'], '26')
remove_leveed_area_and_aland0_from_merged_fc('east_coast', ['2035', '2060','2080',  '2100'], ['NCAI'], '26')
remove_leveed_area_and_aland0_from_merged_fc('east_coast', ['2060', '2100'], ['NCAL'], '26')




# need to do TX








