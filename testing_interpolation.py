import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def interpolate_and_create_water_level_surfaces(years, projections):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/permanent_inundation.gdb'

    #will the join created above still apply? Yes if I call that method within this one (I think):

    #transect_points_layer = prep_gauge_data_for_interpolation() # add parameters or not?
    transect_points_layer = arcpy.MakeFeatureLayer_management('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/empty_points_near_join_mhhw_projected.shp')

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

                water_level_surface.save(outname + '_test')

interpolate_and_create_water_level_surfaces(['MHHW_'],['ft_N'])