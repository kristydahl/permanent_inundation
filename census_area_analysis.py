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

def census_area_analysis(years, projections, region):

    arcpy.env.workspace =  'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    for projection in projections:

        for year in years:

            print 'Year is: ' + 'and projection is: ' + projection

            csv_filename = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/inundated_tract_area_' .format(region) + region + '_' + year + '_' + projection + '.csv'


            with open(csv_filename,'wb') as csvfile:

                inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}_{1}*' .format(year, projection))[0]

                print inundation_surface

                inundation_surface_layer = arcpy.MakeFeatureLayer_management(inundation_surface, 'Inundation Surface')  # this makes it a layer
                census_tracts = 'C:/Users/kristydahl/Desktop/GIS_data/SoVI_2010_AllCoastalStates/SoVI_2010_AllCoastalStates/Spatial/SoVI0610NOAA_CSC.gdb/SoVI0610_FL' # Do I want this in gdb?

                census_tracts_layer = arcpy.MakeFeatureLayer_management(census_tracts,'Census tracts')

                print 'Made census tracts layer'

                arcpy.AddField_management(census_tracts_layer,"Pct_inun_{0}_{1}" .format(year, projection),"FLOAT")

                #census_tracts_layer.save()
                # ADD AWATER10 to FIELDS

                arcpy.SelectLayerByLocation_management('Census tracts', "CONTAINS", 'Inundation Surface', "","NEW_SELECTION")
                arcpy.SelectLayerByLocation_management('Census tracts', "CROSSED_BY_THE_OUTLINE_OF",'Inundation Surface',"","ADD_TO_SELECTION")

                fields = ["SHAPE@","ALAND10","STATEFP10","COUNTYFP10","NAME10","AWATER10","Pct_inun_{0}_{1}" .format(year, projection)]


                with arcpy.da.UpdateCursor(census_tracts_layer,fields) as cursor:

                # This is written thinking we'd be using the NOAA SoVI data. If going with EPA SoVI, would need to specify fields differently and use more of a row[0] formulation in the four lines below

                # NEED TO ALSO GRAB THE WATER AREA (AWATER10)
                    for row in cursor:
                        census_tract_land_area = row[1]
                        census_tract_state = row[2]
                        census_tract_county = row[3]
                        census_tract_name = row[4]
                        census_tract_water_area = row[5]

                        tract = row[0]

                        csv_filename = 'test_output_area_to_csv.csv'

                        print(csv_filename)


                        outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_tract'


                        print "outname is: " + outname

                        if census_tract_land_area > 0:
                            arcpy.Clip_analysis('Inundation Surface', tract, outname)
                            print 'Clipped inundation surface layer to tract'

                            fc = arcpy.MakeFeatureLayer_management(outname, 'clipped_inundation_surface_layer')
                            print 'Created clipped_inundation_surface_layer'

                            # create new Area_acres field and calculate it

                            arcpy.AddField_management(fc, "Area_sqm", "FLOAT")
                            arcpy.CalculateField_management(fc, "Area_sqm", "!shape.area@squaremeters!", "PYTHON_9.3")
                            #result = arcpy.GetCount_management(fc)

                            result = int(arcpy.GetCount_management(fc).getOutput(0))

                            print result

                            if result == 0:
                                print 'Table is empty'
                                writer = csv.writer(csvfile)
                                writer.writerow([census_tract_state, census_tract_county, census_tract_name, "%.2f" % census_tract_land_area, year, projection, 0, 0])
                                print 'Wrote to csv'

                            else:

                                # get sum of all rows in Area_acres
                                output_table_name = 'output_sum_area'
                                print 'Output table name is: ' + output_table_name
                                arcpy.Statistics_analysis(fc, output_table_name,
                                                          [["Area_sqm", 'SUM']])  # this outputs a table with the summary statistics.
                                print 'Calculated stats'

                                arr = arcpy.da.TableToNumPyArray(output_table_name, 'Sum_Area_sqm')[0]
                                print arr
                                sum_area = arr[0] - census_tract_water_area
                                print sum_area

                                writer = csv.writer(csvfile)

                                # NEED TO SUBTRACT WATER AREA FROM SUM_AREA!!
                                writer.writerow([census_tract_state, census_tract_county, census_tract_name, "%.2f" % census_tract_land_area, year, projection,year, projection, "%.2f" % sum_area, "%.2f" % ((sum_area / census_tract_land_area) * 100)])
                                print 'Wrote to csv'

                                row[6] = sum_area/census_tract_land_area * 100

                            # Update the census tracts layer with the % inundation for that tract for the year-projection field
                                cursor.updateRow(row)

                            del fc

                        else:
                            print 'Land area is 0.'

census_area_analysis(['MHHW'], ['__ft_N_test'],'east_coast')