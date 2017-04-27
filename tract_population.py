# Calculate_pop... script calculates the sum of population in tracts with any amount of inundation and, ultimately, was not used.

# Oceanfront_cohort... script identifies how many cohort communities are directly on the oceanfront and returns the values in the console window.

import arcpy
import numpy

arcpy.env.overwriteOutput = True

def calculate_pop_of_inundated_tracts(region, projections, years):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    tracts_with_pop_data = '{0}_census_tracts_with_pop_clip' .format(region)
    arcpy.MakeFeatureLayer_management(tracts_with_pop_data, 'tracts_layer')

    for projection in projections:

        for year in years:

            print 'Year is ' + year
            #arcpy.env.extent = 'tl_2016_10_cousub_clip_diss'

            inundated_area = 'final_polygon_26x_{0}_{1}_merged_clip_to_22' .format(year, projection)

            arcpy.MakeFeatureLayer_management(inundated_area, 'inundated_area_layer')

            # print 'Selecting tracts'
            #
            # selected_tracts = arcpy.SelectLayerByLocation_management('tracts_layer', "INTERSECT", 'inundated_area_layer', '-100 Meters')
            #
            # print 'Selected tracts'

            #selected_tracts.save('test_selecting_tracts')

            print 'clipping'
            arcpy.Clip_analysis('tracts_layer','inundated_area_layer', 'test_clipping_tracts_to_inundation_layer')

            print 'clipped'

            result = int(arcpy.GetCount_management('test_clipping_tracts_to_inundation_layer').getOutput(0))

            print result

            if result == 0:
                print 'Table is empty'

            else:

                # get sum of population in all tracts
                output_table_name = 'output_sum_population'

                arcpy.Statistics_analysis('test_clipping_tracts_to_inundation_layer', output_table_name, [["DP0010001", "SUM"]])

                print 'Calculated stats'

                sum_pop = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_DP0010001')[0]

                print 'population is ' + str(sum_pop[0])

#calculate_pop_of_inundated_tracts('east_coast',['NCAH'],['2006'])

def oceanfront_cohort_communities(region, projections, years):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}_results/{0}.gdb' .format(region)

    all_oceanfront_cousubs = 'all_oceanfront_cousub'

    arcpy.MakeFeatureLayer_management(all_oceanfront_cousubs, 'all_oceanfront_cousubs')

    for projection in projections:

        for year in years:

            total_cohort = 'cohort_municipalities_nowetlands_nolevees_{0}_{1}_10percent' .format(year, projection)
            arcpy.MakeFeatureLayer_management(total_cohort, 'total_cohort')

            outname = 'cohort_municipalities_nowetlands_nolevees_{0}_{1}_10percent_oceanfront_only' .format(year, projection)
            arcpy.Clip_analysis('total_cohort','all_oceanfront_cousubs',outname)

            national_result = int(arcpy.GetCount_management(outname).getOutput(0))

            #print str(national_result)

            arcpy.MakeFeatureLayer_management(outname, 'oceanfront_cohort')

            exp = """ "STATEFP" IN ('06','41','53') """

            #print exp

            arcpy.SelectLayerByAttribute_management('oceanfront_cohort', "NEW_SELECTION", '{0}' .format(exp))

            west_coast_result = int(arcpy.GetCount_management('oceanfront_cohort').getOutput(0))

            print 'For {0} {1}, oceanfront total: {2} and west coast total: {3}' .format(year, projection, national_result, west_coast_result)

oceanfront_cohort_communities('national', ['NCAL'], ['2060','2100'])
oceanfront_cohort_communities('national', ['NCAI'], ['2060','2100'])
oceanfront_cohort_communities('national', ['NCAH'], ['2060','2100'])









