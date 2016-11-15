import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

# This requires the near table to be generated before running; should be in projected coordinate system (Tested 10/12/16 and is working)
def prep_gauge_data_for_interpolation(region):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    # Make layers from empty transect points file and file with gauges and water levels for each year/projection

    gauges_layer = arcpy.MakeFeatureLayer_management("all_east_coast_stations_26x_ncah_proj" .format(region)) # 11/4/16: NEED TO UPDATE FILE NAME AND PATH

    transect_points_layer = arcpy.MakeFeatureLayer_management('{0}_empty_points_proj' .format(region),'transect_points_layer') # CHANGE PATH

    # Join empty points and gauges file
    arcpy.AddJoin_management('transect_points_layer','Near_FID',gauges_layer, 'OBJECTID','KEEP_COMMON')

    print 'Joined data'

    return transect_points_layer


# This method has been tested and is working.
def interpolate_and_create_water_level_surfaces(years, projections,region,flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    #will the join created above still apply? Yes if I call that method within this one (I think):

    transect_points_layer = prep_gauge_data_for_interpolation(region) # add parameters or not?


    fields = arcpy.ListFields(transect_points_layer)

    for field in fields:
        print field.name

    mhhw_data = arcpy.ListRasters("all_noaa_mhhw_mosaic")[0]
    mhhw_layer = arcpy.MakeRasterLayer_management(mhhw_data,'mhhw_layer')# CHANGED PATH SO READING FROM GDB 11/6/16

    # Set interpolation limit as polygon created from coastal counties
    arcpy.env.mask = 'all_noaa_mhhw_mosaic_polygon.shp' # CHANGED PATH SO READING FROM GDB 11/6/16; Not sure about projection here...

    #  Get cell size properties of mhhw_layer to use in interpolation between transect points

    cellsize_properties = ["CELLSIZEX"]
    cellsizes = []

    for cellsize_property in cellsize_properties:
        size_tmp = arcpy.GetRasterProperties_management(mhhw_layer, cellsize_property)
        size = size_tmp.getOutput(0)
        cellsizes.append(size)
        cellsizes = [float(item) for item in cellsizes]

        cellsize = cellsizes[0]
        print 'Cell size of mhhw layer is: ' + str(cellsize)

        #cellsize = cellsize*4

    # For each year/proj horizon (as fields in the joined points file), interpolate empty points file based on field from joined table (gauges water level
        for projection in projections:

            for year in years:

                print 'Projection is: ' + projection + ' and year is: ' + year

                # interpolate between points
                interpolated_surface_wrt_mhhw = NaturalNeighbor(transect_points_layer,str('all_{0}_stations_{1}x_' .format(region, flood_frequency) + projection.lower() + '_proj.F' + year + '_' + projection), cellsize)

                print 'Created interpolated_surface'
                arcpy.MakeRasterLayer_management(interpolated_surface_wrt_mhhw, 'interpolated_surface_wrt_mhhw')

                interpolated_surface_wrt_mhhw.save('is_this_interpolated_surface_empty')
                # add to mhhw surface
                # There may be issues with coordinate systems/projections. Be aware.
                print 'Ran Make raster layer'

                # Careful here!! MHHW Layer has units of meters! This version converts mhhw layer to feet, then adds
                water_level_surface =  Raster('mhhw_layer')/.3048 + Raster('interpolated_surface_wrt_mhhw')

                # Save WLS with some format that includes year and projection
                outname = 'water_level_surface_wrt_navd_' + flood_frequency + 'x' + '_' + year + '_' + projection

                water_level_surface.save(outname)


# Tested and working as of 10/12/16!
def subtract_dems_from_wls(years, projections,region,flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)  # Change for west coast

    arcpy.env.workspace = gdb

    inundated_area_surfaces_raw = []

    for projection in projections:

        for year in years:
            print 'Year is: ' + year
            print 'Projection is: ' + projection
            # get the specific WLS from the gdb

            water_level_surface = arcpy.ListRasters('water_level_surface_wrt_navd_*{0}*{1}'.format(year,projection))[0]
            print water_level_surface
            outname_resampled_water_level_surface = 'water_level_surface_wrt_navd_{0}x_{1}_{2}_resampled'.format(flood_frequency, year, projection)
            print "Output name is: " + outname_resampled_water_level_surface

            # get DEMS from gdb

            #dems = arcpy.ListRasters('*final_DEM*')
            dems = ['NJ_Middle_final_DEM']

            # Loop through DEMs in a database (get all rasters with final_DEM in name)

            for dem in dems:

                # set mask to dem extent
                arcpy.env.mask = dem
                arcpy.env.cellSize = "MINOF"

                # Compare DEM and water level surface. Where WLS >= DEM, set value of 1

                print 'DEM is: ' + dem
                print 'Creating inundated area surface'
                inundated_area_surface = Con(Raster(water_level_surface)*.3048 >= Raster(dem), 1) # creates flat inundation area raster

                #inundated_area_surface_depth = Con(Raster(water_level_surface)* .3048 >= Raster(dem), Raster(water_level_surface) - Raster(dem)) # creates depth raster

                print 'Created inundated area surface for ' + dem
                outname_inundated_area_surface = 'inundated_area_surface_%sx_%s_%s' %(flood_frequency, year, projection) + '_' + dem[:-10]

                #outname_inundated_area_surface_depth = 'depth_inundated_area_surface_%sx_%s_%s_' %(flood_frequency, year, projection) + '_' + dem[:-10]

                inundated_area_surface.save(outname_inundated_area_surface)

                #inundated_area_surface_depth.save(outname_inundated_area_surface_depth)

                inundated_area_surfaces_raw.append(outname_inundated_area_surface)

    return inundated_area_surfaces_raw


# Tested and working as of 10/13/16
def combine_chunks (years, projections,region, flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)  # Change for west coast

    arcpy.env.workspace = gdb
    #inundated_area_surfaces_raw = subtract_dems_from_wls(years, projections)
    for projection in projections:

        for year in years:

            print 'Year is: ' + year
            raw_raster_set = arcpy.ListRasters('inundated_area_surface_{0}x_{1}_{2}*' .format(flood_frequency, year, projection))
            print raw_raster_set

            #raw_raster_set_depth = arcpy.ListRasters('depth_inundated_area_surface*{0}_{1}*' .format(year, projection))

            outname = 'merged_raw_raster_surface_%sx_%s_%s' %(flood_frequency, year, projection)

            print 'Outname is: ' + outname

            arcpy.MosaicToNewRaster_management(raw_raster_set, gdb, outname,"","","30","1")

            print 'Created mosaic for ' + year

            #arcpy.MosaicToNewRaster_management(raw_raster_set_depth, gdb, 'merged_raw_surface_depth_%sx_%s_%s*' %(flood_frequency, year, projection),"","32_BIT_FLOAT","","1")

# Region group/extract, convert to polygon; Tested and working as of 10/13/16; Would need to add code to convert depth to polygons if/when we want that info.
def region_group_extract(years, projections,region, flood_frequency):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)  # Change for west coast

    arcpy.env.workspace = gdb


    #
    region_grouped_files = []
    extracted_files = []
    final_polygons = []

    for projection in projections:

        for year in years:

            merged_raw_surfaces = arcpy.ListRasters('merged_raw_raster_surface_%sx_%s_%s' % (flood_frequency, year, projection))

            for surface in merged_raw_surfaces:
                fullname = str(surface)
                print('Raw surface name is ' + fullname)
                filename = os.path.basename(fullname)

                # If retaining depth information, would need to flatten all values to 1 here before region grouping (see slr_surge_analysis rg script)

                #input_to_rg = Con(Raster(fullname)>0,1)
                #input_to_rg.save('test_input_to_rg')
                #inputs_to_rg.append(input_to_rg)

                # Perform region group
                print('Region grouping ' + fullname)
                outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN",'NO_LINK')
                outname_rg = 'rg_' + fullname
                outRegionGrp.save(outname_rg)

                print("Region grouped " + surface)

                #Extract connected areas

                fullname = str(outname_rg)
                print('File to extract is ' + fullname)
                filename = os.path.basename(fullname)
                outname_extract = 'extract_' + filename

                print('Extracting ' + filename)
                arr = arcpy.da.FeatureClassToNumPyArray(outname_rg, ('Value', 'Count'))
                count = arr['Count']
                value = arr['Value']
                index_to_extract = numpy.argmax(count)
                value_to_extract = str(value[index_to_extract])

                inSQLClause = 'Value =' + value_to_extract
                print('Extracting ' + value_to_extract + 'from ' + filename)

                attExtract = ExtractByAttributes(fullname, inSQLClause)
                attExtract.save(outname_extract)
                extracted_files.append(attExtract)
                print('Extracted connected areas from' + outname_rg)

            #     # create polygon
            #     fullname = str(outname_extract)
            #     filename = os.path.basename(fullname)
            #     outname_polygon = 'final_polygon_' + filename
            #
            #     arcpy.RasterToPolygon_conversion(fullname, outname_polygon,"SIMPLIFY", "VALUE")
            #     final_polygons.append(outname_polygon)
            #
            #     print('Converted ' + outname_extract + ' to polygon')
            # return {'final_polygons': final_polygons}

    # rg_files = arcpy.ListRasters('rg_*')
    #
    # for rg_file in rg_files:
    #
    #     fullname = str(rg_file)
    #     print('File to extract is ' + fullname)
    #     filename = os.path.basename(fullname)
    #     outname_extract = 'extract_' + filename
    #
    #     print('Extracting ' + filename)
    #     arr = arcpy.da.FeatureClassToNumPyArray(rg_file, ('Value', 'Count'))
    #     count = arr['Count']
    #     value = arr['Value']
    #     index_to_extract = numpy.argmax(count)
    #     value_to_extract = str(value[index_to_extract])
    #
    #     inSQLClause = 'Value =' + value_to_extract
    #     print('Extracting ' + value_to_extract + 'from ' + filename)
    #
    #     attExtract = ExtractByAttributes(fullname, inSQLClause)
    #     attExtract.save(outname_extract)
    #     extracted_files.append(attExtract)
    #     print('Extracted connected areas from' + rg_file)

    #     # create polygon
    #     fullname = str(outname_extract)
    #     filename = os.path.basename(fullname)
    #     outname_polygon = 'final_polygon_' + filename
    #
    #     arcpy.RasterToPolygon_conversion(fullname, outname_polygon, "SIMPLIFY", "VALUE")
    #     final_polygons.append(outname_polygon)
    #
    #     print('Converted ' + outname_extract + ' to polygon')
    #
    #
    # return {'final_polygons': final_polygons}

def raster_to_polygon(years, projections,region, flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            to_convert = arcpy.ListRasters('extract_rg_merged*{0}x_{1}_{2}' .format(flood_frequency, year, projection))[0]

            outname_polygon = 'final_polygon_' + str(to_convert)

            arcpy.RasterToPolygon_conversion(to_convert, outname_polygon, "SIMPLIFY", "VALUE")

            print 'Converted ' + to_convert + ' to polygon'

#interpolate_and_create_water_level_surfaces(['2060','2070','2080','2090','2100'],['NCAH'],'east_coast','26')
#subtract_dems_from_wls(['2006','2030','2045','2060','2070','2080','2090','2100'],['NCAH'],'east_coast','26')
combine_chunks(['2060'],['NCAH'],'east_coast','26')
region_group_extract(['2060'],['NCAH'],'east_coast','26')
#combine_chunks(['2030','2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast','26')
#region_group_extract(['2045','2060','2070','2080','2090','2100'], ['NCAH'],'east_coast','26')
#raster_to_polygon(['2006','2030','2045','2060','2070','2080','2090','2100'],['NCAH'],'east_coast','26')




