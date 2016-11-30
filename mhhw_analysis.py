import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def subtract_dems_from_wls(region):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    water_level_surface = arcpy.ListRasters('all_noaa_mhhw_west')[0]
    print water_level_surface

    dems = arcpy.ListRasters('*final_DEM*')

    for dem in dems:

        # set mask to dem extent
        arcpy.env.mask = dem
        arcpy.env.cellSize = "MINOF"

        # Compare DEM and water level surface. Where WLS >= DEM, set value of 1

        print 'DEM is: ' + dem
        print 'Creating inundated area surface'
        inundated_area_surface = Con(Raster(water_level_surface) >= Raster(dem), 1)

        print 'Created inundated area surface for ' + dem
        outname_inundated_area_surface = 'inundated_area_surface_mhhw' + '_' + dem[:-10]

        inundated_area_surface.save(outname_inundated_area_surface)



def combine_chunks (region):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb


    raw_raster_set = arcpy.ListRasters('inundated_area_surface_mhhw*')

    #raw_raster_set_depth = arcpy.ListRasters('depth_inundated_area_surface*{0}_{1}*' .format(year, projection))

    outname = 'merged_raw_raster_surface_mhhw'

    print 'Outname is: ' + outname

    arcpy.MosaicToNewRaster_management(raw_raster_set, gdb, outname,"","","10","1")

    print 'Created mosaic for mhhw'


# Would need to add code to convert depth to polygons if/when we want that info.

def region_group(region, subregions):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    arcpy.env.workspace = gdb


    merged_raw_surface = arcpy.ListRasters('merged_raw_raster_surface_mhhw')[0]

    fullname = str(merged_raw_surface)
    print('Raw surface name is ' + fullname)
    filename = os.path.basename(fullname)

    if region == 'east_coast':
        for subregion in subregions:

            arcpy.env.extent = subregion
            print 'Region grouping ' + fullname + ' to ' + subregion
            outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN",'NO_LINK')
            outname_rg = 'rg_' + fullname + '_' + subregion
            outRegionGrp.save(outname_rg)

            print "Region grouped " + merged_raw_surface + ' to ' + subregion

    else:
        print 'Region grouping ' + fullname
        outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN", 'NO_LINK')
        outname_rg = 'rg_' + fullname
        outRegionGrp.save(outname_rg)

        print "Region grouped " + merged_raw_surface


def extract(region, subregions):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)  # Change for west coast

    arcpy.env.workspace = gdb

    if region == 'east_coast':

        for subregion in subregions:

            rg_surface = arcpy.ListRasters('rg_merged_raw_raster_surface_mhhw_{0}' .format(subregion))[0]

            print('File to extract is ' + rg_surface)

            outname_extract = 'extract_' + rg_surface

            print('Extracting ' + rg_surface)
            arr = arcpy.da.FeatureClassToNumPyArray(rg_surface, ('Value', 'Count'))
            count = arr['Count']

            print 'Count is: ' + str(count)

            value = arr['Value']

            print 'Value is: ' + str(value)

            index_to_extract = numpy.argmax(count)
            value_to_extract = str(value[index_to_extract])

            inSQLClause = 'Value =' + value_to_extract
            print('Extracting ' + value_to_extract + ' from ' + rg_surface)

            attExtract = ExtractByAttributes(rg_surface, inSQLClause)
            attExtract.save(outname_extract)

            print('Extracted connected areas from' + rg_surface)

    else:


        rg_surface = arcpy.ListRasters('rg_merged_raw_raster_surface_mhhw')[0]

        print('File to extract is ' + rg_surface)

        outname_extract = 'extract_' + rg_surface

        print('Extracting ' + rg_surface)
        arr = arcpy.da.FeatureClassToNumPyArray(rg_surface, ('Value', 'Count'))
        count = arr['Count']

        print 'Count is: ' + str(count)

        value = arr['Value']

        print 'Value is: ' + str(value)

        index_to_extract = numpy.argmax(count)
        value_to_extract = str(value[index_to_extract])

        inSQLClause = 'Value =' + value_to_extract
        print('Extracting ' + value_to_extract + ' from ' + rg_surface)

        attExtract = ExtractByAttributes(rg_surface, inSQLClause)
        attExtract.save(outname_extract)

        print('Extracted connected areas from' + rg_surface)


def raster_to_polygon(region, subregions):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb
    arcpy.env.extent = 'all_noaa_mhhw_mosaic_polygon'

    if region == 'east_coast':

        polygons_of_subregions = []

        for subregion in subregions:

            to_convert = arcpy.ListRasters('extract_rg_merged*mhhw_{0}' .format(subregion))[0]

            print 'File to convert is: ' + str(to_convert)

            outname_polygon = 'final_polygon_' + str(to_convert)

            arcpy.RasterToPolygon_conversion(to_convert, str(outname_polygon), "SIMPLIFY", "VALUE")

            print 'Converted ' + to_convert + ' to polygon'

    else:

        to_convert = arcpy.ListRasters('extract_rg_merged*mhhw')[0]
        print 'File to convert is: ' + str(to_convert)
        outname_polygon = 'final_polygon_' + str(to_convert)

        arcpy.RasterToPolygon_conversion(to_convert, outname_polygon, "SIMPLIFY", "VALUE")

        print 'Converted ' + to_convert + ' to polygon'


#subtract_dems_from_wls('west_coast')
#combine_chunks('west_coast')
#region_group('west_coast',[])
#extract('west_coast',[])
#extract(['2035','2060','2080','2100'],['NCAI'],'west_coast','26')
#raster_to_polygon(['2035','2060','2080','2100'],['NCAI'],'west_coast','26')

raster_to_polygon('west_coast',[])



