import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

# This requires the near table to be generated before running; should be in projected coordinate system
def prep_gauge_data_for_interpolation(region, projections):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    # Make layers from empty transect points file and file with gauges and water levels for each year/projection

    gauges_layer = arcpy.MakeFeatureLayer_management("all_{0}_stations_26x_{1}_proj" .format(region, projections[0]))

    transect_points_layer = arcpy.MakeFeatureLayer_management('{0}_empty_points_proj' .format(region),'transect_points_layer')

    # Join empty points and gauges file
    arcpy.AddJoin_management('transect_points_layer','Near_FID',gauges_layer, 'OBJECTID','KEEP_COMMON')

    print 'Joined data'

    return transect_points_layer


def interpolate_and_create_water_level_surfaces(years, projections,region,flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    transect_points_layer = prep_gauge_data_for_interpolation(region, projections) # add parameters or not?


    fields = arcpy.ListFields(transect_points_layer)

    # Comment out lines 48-50
    # number_of_points = arcpy.GetCount_management('transect_points_layer')
    # count = int(number_of_points.getOutput(0))
    # print(count)

    for field in fields:
        print field.name

    mhhw_data = arcpy.ListRasters("all_noaa_mhhw*")[0] # Put in config file for west and east

    mhhw_layer = arcpy.MakeRasterLayer_management(mhhw_data,'mhhw_layer')

    # Set interpolation limit as polygon created from coastal counties
    arcpy.env.mask = 'all_noaa_mhhw_mosaic_polygon.shp'

    #  Get cell size properties of mhhw_layer to use in interpolation between transect points

    cellsizes = []


    #for cellsize_property in cellsize_properties:
    # these lines should likely be a function
    size_tmp = arcpy.GetRasterProperties_management(mhhw_layer, "CELLSIZEX")
    size = size_tmp.getOutput(0)
    cellsizes.append(size)
    cellsizes = [float(item) for item in cellsizes]

    cellsize = cellsizes[0]
    print 'Cell size of mhhw layer is: ' + str(cellsize)

        #cellsize = cellsize*4

    # For each year/proj horizon, interpolate empty points file based on field from joined table
    for projection in projections:

        for year in years:

            print 'Projection is: ' + projection + ' and year is: ' + year

            # interpolate between points
            interpolated_surface_wrt_mhhw = NaturalNeighbor(transect_points_layer,str('all_{0}_stations_{1}x_' .format(region, flood_frequency) + projection + '_proj.F' + year + '_' + projection), cellsize)

            print 'Created interpolated_surface'
            arcpy.MakeRasterLayer_management(interpolated_surface_wrt_mhhw, 'interpolated_surface_wrt_mhhw')

            print 'Ran Make raster layer'

            # This version converts mhhw layer to feet, then adds
            water_level_surface =  Raster('mhhw_layer')/.3048 + Raster('interpolated_surface_wrt_mhhw')

            outname = 'water_level_surface_wrt_navd_' + flood_frequency + 'x' + '_' + year + '_' + projection

            water_level_surface.save(outname)

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

            dems = arcpy.ListRasters('*final_DEM*')
            #dems = ['VA_Northern_final_DEM']

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

def combine_chunks (years, projections,region, flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            print 'Year is: ' + year
            raw_raster_set = arcpy.ListRasters('inundated_area_surface_{0}x_{1}_{2}*' .format(flood_frequency, year, projection))
            print raw_raster_set

            #raw_raster_set_depth = arcpy.ListRasters('depth_inundated_area_surface*{0}_{1}*' .format(year, projection))

            outname = 'merged_raw_raster_surface_%sx_%s_%s' %(flood_frequency, year, projection)

            print 'Outname is: ' + outname

            arcpy.MosaicToNewRaster_management(raw_raster_set, gdb, outname,"","","10","1")

            print 'Created mosaic for ' + year


# Would need to add code to convert depth to polygons if/when we want that info.
def region_group(years, projections,region, flood_frequency):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            merged_raw_surfaces = arcpy.ListRasters('merged_raw_raster_surface_%sx_%s_%s' % (flood_frequency, year, projection))

            for surface in merged_raw_surfaces:
                fullname = str(surface)
                print('Raw surface name is ' + fullname)
                filename = os.path.basename(fullname)

                # If retaining depth information, would need to flatten all values to 1 here before region grouping (see slr_surge_analysis rg script)

                # Perform region group
                print('Region grouping ' + fullname)
                outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN",'NO_LINK')
                outname_rg = 'rg_' + fullname
                outRegionGrp.save(outname_rg)

                print("Region grouped " + surface)


def extract(years, projections, region, flood_frequency):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)  # Change for west coast

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            rg_surface = arcpy.ListRasters('rg_merged_raw_raster_surface_{0}x_{1}_{2}' .format(flood_frequency, year, projection))[0]

            print('File to extract is ' + rg_surface)

            outname_extract = 'extract_' + rg_surface

            print('Extracting ' + rg_surface)
            arr = arcpy.da.FeatureClassToNumPyArray(rg_surface, ('Value', 'Count'))
            count = arr['Count']
            value = arr['Value']
            index_to_extract = numpy.argmax(count)
            value_to_extract = str(value[index_to_extract])

            inSQLClause = 'Value =' + value_to_extract
            print('Extracting ' + value_to_extract + 'from ' + rg_surface)

            attExtract = ExtractByAttributes(rg_surface, inSQLClause)
            attExtract.save(outname_extract)

            print('Extracted connected areas from' + rg_surface)

def raster_to_polygon(years, projections,region, flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            to_convert = arcpy.ListRasters('extract_rg_merged*{0}x_{1}_{2}' .format(flood_frequency, year, projection))[0]

            if region == 'east_coast':

                print 'File to convert is: ' + str(to_convert)

                to_convert_north = arcpy.sa.ExtractByMask(to_convert, 'northern_third')

                print 'Created northern third'

                to_convert_middle = arcpy.sa.ExtractByMask(to_convert, 'middle_third')

                print 'Created middle third'

                to_convert_south = arcpy.sa.ExtractByMask(to_convert, 'southern_half')

                print 'Created southern half'

                outname_polygon = 'final_polygon_' + str(to_convert)

                arcpy.RasterToPolygon_conversion(to_convert_north, str(outname_polygon + '_north'), "SIMPLIFY", "VALUE")

                print 'Converted northern third to polygon'

                arcpy.RasterToPolygon_conversion(to_convert_middle, str(outname_polygon + '_middle'), "SIMPLIFY", "VALUE")

                print 'Converted middle third to polygon'

                arcpy.RasterToPolygon_conversion(to_convert_south, str(outname_polygon + '_south'), "SIMPLIFY", "VALUE")

                print 'Converted southern half to polygon'

                #union_north_south = 'final_polygon_' + str(to_convert) + '_union'
                #arcpy.Union_analysis([str(outname_polygon + '_north'), str(outname_polygon + '_middle'), str(outname_polygon + '_south')], union_north_south)

                #print 'United northern, middle, and southern chunks'


            else:

                print 'File to convert is: ' + str(to_convert)
                outname_polygon = 'final_polygon_' + str(to_convert)

                arcpy.RasterToPolygon_conversion(to_convert, outname_polygon, "SIMPLIFY", "VALUE")

                print 'Converted ' + to_convert + ' to polygon'

#prep_gauge_data_for_interpolation('west_coast',['NCAL'])
#interpolate_and_create_water_level_surfaces(['2060','2100'],['NCAL'],'west_coast','26')
#subtract_dems_from_wls(['2060','2100'],['NCAL'],'west_coast','26')
#combine_chunks(['2060','2100'],['NCAL'],'west_coast','26')
region_group(['2060','2100'],['NCAL'],'west_coast','26')
extract(['2060','2100'],['NCAL'],'west_coast','26')
raster_to_polygon(['2100'],['NCAL'],'west_coast','26')



