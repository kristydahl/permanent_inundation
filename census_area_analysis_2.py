import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
import csv
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def census_area_analysis(years, projections, region, flood_frequency):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)


    state_numbers = ['01']

    #state_numbers = ['06','41','53']

    for projection in projections:

        for year in years:

            for state_number in state_numbers:


                print 'Year is: ' + year + ' and projection is: ' + projection

                municipalities = 'tl_2016_{0}_cousub' .format(state_number)

                # need to clip municipalities layer to outline of tracts, I think

                census_tracts = 'tl_2016_{0}_tract' .format(state_number)

                municipalities_clip = arcpy.Clip_analysis(municipalities, census_tracts, str(municipalities + '_clip'))

                municipalities_layer = arcpy.MakeFeatureLayer_management(municipalities_clip, 'clipped municipalities')

                csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_muni_area_'.format(
                    region) + '_' + year + '_' + projection + '_' + state_number + '.csv'

                with open(csv_filename,'wb') as csvfile:

                    inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}x_{1}_{2}_fl_gulf' .format(flood_frequency, year, projection))[0]

                    mhhw_inundation_surface = arcpy.ListFeatureClasses('final_polygon*mhhw_fl_gulf')[0]

                    print inundation_surface

                    #inundation_surface_layer = arcpy.MakeFeatureLayer_management(inundation_surface, 'Inundation Surface')  # this makes it a layer

                    # THIS IS NOT WORKING...doing that weird clip thing.

                    outname = str(inundation_surface + '_clip_to_{0}' .format(state_number))

                    outname_mhhw = str(mhhw_inundation_surface + '_clip_to_{0}' .format(state_number))

                    state_inundation_surface = arcpy.Clip_analysis(inundation_surface, 'clipped municipalities', outname)

                    state_mhhw_inundation_surface = arcpy.Clip_analysis(mhhw_inundation_surface, 'clipped_municipalities', outname_mhhw)

                    print 'Clipped inundation and mhhw surfaces to state'

                    arcpy.AddField_management(municipalities_layer,"Pct_inun_{0}_{1}" .format(year, projection),"FLOAT")

                    arcpy.AddField_management(municipalities_layer, "Pct_inun_MHHW","FLOAT")

                    print 'Added Percent inundation field'

                    arcpy.AddField_management(municipalities_layer, "Tot_area", "FLOAT")
                    exp = "!SHAPE.AREA@SQUAREMETERS!"

                    print 'Added Total area field'

                    arcpy.CalculateField_management(municipalities_layer, "Tot_area", exp, "PYTHON_9.3")

                    print 'Calculated total area'

                    arcpy.SelectLayerByLocation_management('clipped municipalities', "INTERSECT", state_inundation_surface, "","NEW_SELECTION")


                    #fields = ["SHAPE@","ALAND","STATEFP","COUNTYFP","NAME","AWATER","Tot_area","Pct_inun_{0}_{1}" .format(year, projection)]

                    fields = ["SHAPE@", "ALAND", "STATEFP", "COUNTYFP", "NAME", "AWATER", "Tot_area", "Pct_inun_MHHW", "Pct_inun_{0}_{1}"]
                    with arcpy.da.UpdateCursor(municipalities_layer,fields) as cursor:
                        for row in cursor:
                            muni = row[0]
                            muni_land_area = row[1]
                            muni_state = row[2]
                            muni_county = row[3]
                            muni_name = row[4]
                            muni_water_area = row[5]
                            total_muni_area = row[6]

                            outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_muni'

                            if total_muni_area is None:

                                print 'Municipality area is None'

                            elif total_muni_area > 0:

                                arcpy.Clip_analysis(str(inundation_surface), muni, outname)

                                print 'Clipped inundation surface layer to tract'

                                fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                print result


                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([muni_state, muni_county, muni_name,
                                                     "%.2f" % total_muni_area, "%.2f" % muni_water_area,
                                                     year, projection, 0, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows in Area_acres
                                    output_table_name = 'output_sum_area'

                                    arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    print 'Inundated area is: ' + str(sum_area[0]) + ' and municipality area is: ' + str(total_muni_area)

                                    writer = csv.writer(csvfile)

                                    # NEED TO SUBTRACT WATER AREA FROM SUM_AREA!!
                                    writer.writerow([muni_state, muni_county, muni_name, "%.2f" % total_muni_area, "%.2f" % muni_water_area, year, projection,"%.2f" % sum_area[0], "%.2f" % ((sum_area[0] / total_muni_area) * 100)])
                                    print 'Wrote to csv'

                                    row[7] = (sum_area[0]/total_muni_area) * 100

                                # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                    cursor.updateRow(row)

                                del fc

                            else:
                                print 'Land area is 0.'

#census_area_analysis(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast','26')
census_area_analysis(['2006'], ['NCAH'], 'east_coast', '26')

# Changes to be made
# Will need to run just for MHHW and make that a field
# Will need to break up inundation polygons by state. This probably means clipping the municipality data by state, then setting each state as the processing extent and looping through.

#,'09','10','11','12','13','22','23','24','25','28','33','34','36','37','42','44','45','48','51'