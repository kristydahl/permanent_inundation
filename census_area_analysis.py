import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

arcpy.env.workspace = # specify here

# Use version of tracts file that's clipped to NOAA MHHW polygon

# NOT SURE THIS IS NECESSARY OR WOULD WORK WITH THE WAY UPDATE CURSOR IS SET UP, but...create selection of census tracts: NEW_SELECTION of tracts that CONTAINS the WLS; ADD_TO_SELECTION tracts that area CROSSED_BY_THE_OUTLINE_OF

---------------------
def census_area_analysis(years, projections, region):

    for projection in projections:

        for year in years:

            print 'Year is: ' + 'and projection is: ' + projection

            csv_filename = 'inundated_tract_area_' + region + '_' + year + '_' + projection + '.csv'


            with open(csv_filename,'wb') as csvfile:

                inundation_surface = arcpy.ListFeatureClasses('final_polygon*{0}_{1}*' .format(year, projection))[0]

                print inundation_surface

                inundation_surface_layer = arcpy.MakeFeatureLayer_management(inundation_surface[0],
                                                                             'Inundation Surface')  # this makes it a layer
                census_tracts = path to sovi data # Do I want this in gdb?

                census_tracts_layer = arcpy.MakeFeatureLayer_management(census_tracts,'Census tracts')

                arcpy.AddField_management(census_tracts_layer,"Pct_inun_{0}_{1}" .format(year, projection),"FLOAT")

                fields = ["ALAND10","STATEFP10","COUNTYFP10","NAME10","Pct_inun{0}_{1}" .format(year, projection)]

                with arcpy.da.UpdateCursor(census_tracts_layer,fields) as cursor:

                # This is written thinking we'd be using the NOAA SoVI data. If going with EPA SoVI, would need to specify fields differently and use more of a row[0] formulation in the four lines below
                    for row in cursor:
                        census_tract_area = row.getValue("ALAND10")
                        census_tract_state = row.getValue("STATEFP10")
                        census_tract_county = row.getValue("COUNTYFP10")
                        census_tract_name = row.getValue("NAME10")

                        tract_layer = arcpy.MakeFeatureLayer_management(row, 'tract')

                        csv_filename = # specify csv filename here

                        print(csv_filename)


                        outname = 'clip_inundation_surface_' + year + '_' + projection + '_to_tract'


                        print "outname is: " + outname

                        arcpy.Clip_analysis('Inundation Surface', 'tract', outname)
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
                            writer.writerow([census_tract_state, census_tract_county, census_tract_name, "%.2f" % census_tract_area, year, projection, 0, 0])
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
                            sum_area = arr[0]
                            print sum_area

                            writer = csv.writer(csvfile)

                            writer.writerow([census_tract_state, census_tract_county, census_tract_name, "%.2f" % census_tract_area, year, projection,year, projection, "%.2f" % sum_area, "%.2f" % ((sum_area / census_tract_area) * 100)])
                            print 'Wrote to csv'

                        row[4] = sum_area/census_tract_area * 100

                        # Update the census tracts layer with the % inundation for that tract for the year-projection field
                        cursor.updateRow(row)

                        del fc

