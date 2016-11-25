import arcpy
from arcpy import env
from arcpy.sa import *
import os
import glob
import numpy
from numpy import genfromtxt
arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def region_group(years, projections,region,subregions, flood_frequency):
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

                for subregion in subregions:

                # Perform region group

                    arcpy.env.extent = subregion
                    print 'Region grouping ' + fullname + ' to ' + subregion
                    outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN",'NO_LINK')
                    outname_rg = 'rg_' + fullname + '_' + subregion
                    outRegionGrp.save(outname_rg)

                    print "Region grouped " + surface + ' to ' + subregion


def extract(years, projections, region, subregions, flood_frequency):
    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)  # Change for west coast

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            for subregion in subregions:

                print 'Year is: ' + year + ', projection is: ' + projection + ', and subregion is: ' + subregion

                rg_surface = arcpy.ListRasters('rg_merged_raw_raster_surface_{0}x_{1}_{2}_{3}' .format(flood_frequency, year, projection, subregion))[0]

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

def raster_to_polygon(years, projections,region, subregions, flood_frequency):

    gdb = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb' .format(region)

    arcpy.env.workspace = gdb

    for projection in projections:

        for year in years:

            if region == 'east_coast':

                polygons_of_subregions = []

                for subregion in subregions:

                    to_convert = arcpy.ListRasters('extract_rg_merged*{0}x_{1}_{2}_{3}' .format(flood_frequency, year, projection, subregion))[0]

                    print 'File to convert is: ' + str(to_convert)

                    outname_polygon = 'final_polygon_' + str(to_convert)

                    arcpy.RasterToPolygon_conversion(to_convert, str(outname_polygon), "SIMPLIFY", "VALUE")

                    print 'Converted' + to_convert + ' to polygon'

                    polygons_of_subregions.append(outname_polygon)

                outname_union = 'final_polygon_{0}x_{1}_{2}_union' .format(flood_frequency, year, projection)

                # print polygons_of_subregions
                #
                # arcpy.Union_analysis(polygons_of_subregions, outname_union)
                #
                #
                # print 'United polygon_subregion chunks'


            else:

                print 'File to convert is: ' + str(to_convert)
                outname_polygon = 'final_polygon_' + str(to_convert)

                arcpy.RasterToPolygon_conversion(to_convert, outname_polygon, "SIMPLIFY", "VALUE")

                print 'Converted ' + to_convert + ' to polygon'

#interpolate_and_create_water_level_surfaces(['2035','2060','2080','2100'],['NCAI'],'west_coast','26')
#subtract_dems_from_wls(['2035','2060','2080','2100'],['NCAI'],'west_coast','26')
#combine_chunks(['2035','2060','2080','2100'],['NCAI'],'west_coast','26')
region_group(['2006','2030','2045','2060','2070','2080','2090'],['NCAH'],'east_coast',['me_to_nj','nj_to_nc','nc_to_fl','fl_gulf','gulf_to_tx'],'26')
extract(['2006','2030','2045','2060','2070','2080','2090'], ['NCAH'], 'east_coast', ['me_to_nj','nj_to_nc','nc_to_fl','fl_gulf','gulf_to_tx'], '26')
raster_to_polygon(['2006','2030','2045','2060','2070','2080','2090'], ['NCAH'], 'east_coast', ['me_to_nj','nj_to_nc','nc_to_fl','fl_gulf','gulf_to_tx'], '26')
#raster_to_polygon(['2006','2035','2060','2080','2100'],['NCAIH'], 'east_coast','26')
