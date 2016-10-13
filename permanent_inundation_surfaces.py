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
def prep_gauge_data_for_interpolation():

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_gulf_coast.gdb' # Change for west coast

    arcpy.env.workspace = gdb

    # Make layers from empty transect points file and file with gauges and water levels for each year/projection

    gauges_layer = arcpy.MakeFeatureLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/long_lat_mhhw_ft_above_navd88_testing.shp")

    transect_points_layer = arcpy.MakeFeatureLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/empty_points.shp",'transect_points_layer') # CHANGE PATH

    # Join empty points and gauges file
    arcpy.AddJoin_management('transect_points_layer','Near_FID',gauges_layer, 'FID','KEEP_COMMON')

    return transect_points_layer


# This method has been tested and is working.
def interpolate_and_create_water_level_surfaces(years, projections):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/permanent_inundation.gdb'

    #will the join created above still apply? Yes if I call that method within this one (I think):

    transect_points_layer = prep_gauge_data_for_interpolation() # add parameters or not?


    fields = arcpy.ListFields(transect_points_layer)

    for field in fields:
        print field.name

    mhhw_layer = arcpy.MakeRasterLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/all_noaa_mhhw_mosaic.tif",'mhhw_layer') # CHANGE PATH SO READING FROM GDB

    # Set interpolation limit as polygon created from coastal counties
    arcpy.env.mask = "C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/all_noaa_mhhw_mosaic_polygon.shp" # CHANGE PATH SO READING FROM GDB

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
                interpolated_surface_wrt_mhhw = NaturalNeighbor(transect_points_layer,str(year + '_' + projection), cellsize)

                print 'Created interpolated_surface'
                arcpy.MakeRasterLayer_management(interpolated_surface_wrt_mhhw, 'interpolated_surface_wrt_mhhw')

                #interpolated_surface_wrt_mhhw.save('is_this_interpolated_surface_empty_2')
                # add to mhhw surface
                # There may be issues with coordinate systems/projections. Be aware.
                print 'Ran Make raster layer'

                # Careful here!! MHHW Layer has units of meters! This version converts mhhw layer to feet, then adds
                water_level_surface =  Raster('mhhw_layer')/.3048 + Raster('interpolated_surface_wrt_mhhw')

                # Save WLS with some format that includes year and projection
                outname = 'water_level_surface_wrt_navd_' + year + '_' + projection

                water_level_surface.save(outname)


# Tested and working as of 10/12/16!
def subtract_dems_from_wls(years, projections):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_gulf_coast.gdb'  # Change for west coast

    arcpy.env.workspace = gdb

    inundated_area_surfaces_raw = []

    for projection in projections:

        for year in years:
            print 'Year is: ' + year
            print 'Projection is: ' + projection
            # get the specific WLS from the gdb

            water_level_surface = arcpy.ListRasters('water_level_surface_wrt_navd_{0}{1}'.format(year,projection))[0]
            print water_level_surface
            outname_resampled_water_level_surface = 'water_level_surface_wrt_navd_{0}{1}_resampled'.format(year, projection)
            print outname_resampled_water_level_surface

            # get DEMS from gdb

            dems = arcpy.ListRasters('FL_JAX*final_DEM*')

            # Loop through DEMs in a database (get all rasters with final_DEM in name)

            for dem in dems:

                # set mask to dem extent
                arcpy.env.mask = dem
                arcpy.env.cellSize = "MINOF"

                # Compare DEM and water level surface. Where WLS >= DEM, set value of 1

                print 'Creating inundated area surface'
                inundated_area_surface = Con(Raster(water_level_surface)>= Raster(dem), 1) # If we decide to retain depth, see line 218 of slr_surge_analysis and edit here

                print 'Created inundated area surface for ' + dem
                outname_inundated_area_surface = 'inundated_area_surface_%s_%s_' %(year, projection) + dem[:-10]

                inundated_area_surface.save(outname_inundated_area_surface)

                inundated_area_surfaces_raw.append(outname_inundated_area_surface)

    return inundated_area_surfaces_raw


# Tested and working as of 10/13/16
def combine_chunks (years, projections):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_gulf_coast.gdb'  # Change for west coast

    arcpy.env.workspace = gdb
    #inundated_area_surfaces_raw = subtract_dems_from_wls(years, projections)
    for projection in projections:

        for year in years:

            raw_raster_set = arcpy.ListRasters('inundated_area_surface_{0}_{1}*' .format(year, projection))
            print raw_raster_set

            arcpy.MosaicToNewRaster_management(raw_raster_set, gdb, 'merged_raw_surface_%s_%s*' %(year, projection),"","32_BIT_FLOAT","","1")


# Region group/extract, convert to polygon; Tested and working as of 10/13/16
def region_group_extract(years, projections):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/east_coast/east_gulf_coast.gdb'  # Change for west coast

    arcpy.env.workspace = gdb

    merged_raw_surfaces = arcpy.ListRasters('merged_raw_surface_MHHW*')

    region_grouped_files = []
    extracted_files = []
    final_polygons = []

    for surface in merged_raw_surfaces:
        fullname = str(surface)
        print('Raw surface name is ' + fullname)
        filename = os.path.basename(fullname)

        # If retaining depth information, would need to flatten all values to 1 here before region grouping (see slr_surge_analysis rg script)

        input_to_rg = Con(Raster(fullname)>0,1)
        input_to_rg.save('test_input_to_rg')
        #inputs_to_rg.append(input_to_rg)

        # Perform region group
        print('Region grouping ' + fullname)
        outRegionGrp = RegionGroup(input_to_rg, "EIGHT", "WITHIN",'NO_LINK')
        outname_rg = 'rg_' + fullname
        outRegionGrp.save(outname_rg)

        print("Region grouped" + surface)

        # Extract connected areas

        fullname = str(outname_rg)
        print('File to extract is ' + fullname)
        filename = os.path.basename(fullname)
        outname_extract = 'extract_' + filename

        print('Extracting' + filename)
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

        # create polygon
        fullname = str(outname_extract)
        filename = os.path.basename(fullname)
        outname_polygon = 'final_polygon_' + filename

        arcpy.RasterToPolygon_conversion(fullname, outname_polygon,"SIMPLIFY", "VALUE")
        final_polygons.append(outname_polygon)

        print('Converted ' + outname_extract + ' to polygon')
    return {'final_polygons': final_polygons}


#interpolate_and_create_water_level_surfaces(years, projections)
#subtract_dems_from_wls(years, projections)
#combine_chunks(years, projections)
region_group_extract(['MHHW'], ['__ft_N_test'])





