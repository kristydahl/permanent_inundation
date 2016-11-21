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

    arcpy.env.workspace =  'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    for projection in projections:

        for year in years:

            print 'Year is: ' + year + ' and projection is: ' + projection

            csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/fl_inundated_muni_area_'.format(
                region) + region + '_' + year + '_' + projection + '.csv'


            with open(csv_filename,'wb') as csvfile:

                #inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}x_{1}_{2}_fl_2*' .format(flood_frequency, year, projection))[0]

                inundation_surface = arcpy.ListFeatureClasses('fl_final_polygon_{0}x_{1}_{2}' .format(flood_frequency, year, projection))[0]

                print inundation_surface

                inundation_surface_layer = arcpy.MakeFeatureLayer_management(inundation_surface, 'Inundation Surface')  # this makes it a layer

                # NEED TO CHANGE BACK TO GENERAL FORMAT
                #census_tracts = 'all_{0}_noaa_sovi_tracts_clip_fl' .format(region)
                census_tracts = 'fl_cousub_clipped_to_tracts'.format(region)

                census_tracts_layer = arcpy.MakeFeatureLayer_management(census_tracts,'Census tracts')

                # THIS IS NOT WORKING...doing that weird clip thing.
                #state_inundation_surface = arcpy.Clip_analysis('Inundation Surface', census_tracts, str('fl_' + inundation_surface))

                print 'Clipped inundation surface to state'

                arcpy.AddField_management(census_tracts_layer,"Pct_inun_{0}_{1}" .format(year, projection),"FLOAT")


                arcpy.SelectLayerByLocation_management('Census tracts', "INTERSECT", 'Inundation Surface', "","NEW_SELECTION")

                fields = ["SHAPE@","ALAND","STATEFP","COUNTYFP","NAME","AWATER",'Area_sqm',"Pct_inun_{0}_{1}" .format(year, projection)]

                #fields = ["SHAPE@", "ALAND", "STATEFP10", "COUNTYFP10", "NAME10", "AWATER", 'Shape_Area', "Pct_inun_{0}_{1}".format(year, projection)]


                with arcpy.da.UpdateCursor(census_tracts_layer,fields) as cursor:

                # This is written thinking we'd be using the NOAA SoVI data. If going with EPA SoVI, would need to specify fields differently and use more of a row[0] formulation in the four lines below

                # NEED TO ALSO GRAB THE WATER AREA (AWATER10)
                    for row in cursor:
                        census_tract_land_area = row[1]
                        census_tract_state = row[2]
                        census_tract_county = row[3]
                        census_tract_name = row[4]
                        census_tract_water_area = row[5]
                        total_tract_area = row[6]

                        tract = row[0]

                        outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_tract'

                        if total_tract_area is None:

                            print 'Tract area is None'

                        elif total_tract_area > 0:

                            if census_tract_land_area > 0:
                                arcpy.Clip_analysis(str(inundation_surface), tract, outname)
                                print 'Clipped inundation surface layer to tract'

                                fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')

                                print 'Created clipped_inundation_surface_layer to municipality'

                                # create new Area_acres field and calculate it

                                #arcpy.AddField_management(fc, "Area_sqm", "FLOAT")
                                #area_sqm = arcpy.CalculateField_management(fc, "Area_sqm", "!shape.area@squaremeters!", "PYTHON_9.3")

                                #print area_sqm
                                #result = arcpy.GetCount_management(fc)


                                result = int(arcpy.GetCount_management(fc).getOutput(0))

                                print result


                                if result == 0:
                                    print 'Table is empty'
                                    writer = csv.writer(csvfile)

                                    writer.writerow([census_tract_state, census_tract_county, census_tract_name,
                                                     "%.2f" % total_tract_area, "%.2f" % census_tract_water_area,
                                                     year, projection, 0, 0])
                                    print 'Wrote to csv'

                                else:

                                    # get sum of all rows in Area_acres
                                    output_table_name = 'output_sum_area'

                                    arcpy.Statistics_analysis(fc, output_table_name, [["Shape_Area", "SUM"]])

                                    print 'Calculated stats'

                                    sum_area = arcpy.da.TableToNumPyArray(output_table_name, 'SUM_Shape_Area')[0]

                                    print 'Inundated area is: ' + str(sum_area[0]) + ' and municipality area is: ' + str(total_tract_area)

                                    writer = csv.writer(csvfile)

                                    # NEED TO SUBTRACT WATER AREA FROM SUM_AREA!!
                                    writer.writerow([census_tract_state, census_tract_county, census_tract_name, "%.2f" % total_tract_area, "%.2f" % census_tract_water_area, year, projection,"%.2f" % sum_area[0], "%.2f" % ((sum_area[0] / total_tract_area) * 100)])
                                    print 'Wrote to csv'

                                    row[7] = (sum_area[0]/total_tract_area) * 100

                                # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                    cursor.updateRow(row)

                                del fc

                            else:
                                print 'Land area is 0.'

#census_area_analysis(['2006','2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast','26')
census_area_analysis(['2060','2070','2080','2090'], ['NCAH'],'east_coast','26')