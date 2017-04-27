# Extract by mask extracts the inundated area over land for visualization online.

# Create_tile_packages preps tile packages for ArcGIS online

import arcpy
import datetime

from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def extract_by_mask_over_land(region, projections, years):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    land_polygon = 'land_polygons_clipped_to_{0}_proj' .format(region)

    for projection in projections:

        for year in years:

            file_to_extract = 'extract_rg_merged_raw_raster_surface_26x_{0}_{1}' .format(year, projection)


            #file_to_extract = 'final_polygon_26x_{0}_{1}_merged_clip_to_'
            print 'Extracting ' + file_to_extract + 'at time: {:%Y-%m-%d %H:%M:%S}' .format(datetime.datetime.now())

            out_extract_by_mask = arcpy.sa.ExtractByMask(file_to_extract, land_polygon)

            print 'Extracted ' + file_to_extract + 'at time: {:%Y-%m-%d %H:%M:%S}' .format(datetime.datetime.now())

            out_extract_by_mask.save('{0}_inundated_area_over_land_only_{1}_{2}' .format(region, year, projection))

            print 'Saved'


def create_tile_packages(projections, years):

    path_to_mxds = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/national_results'

    for projection in projections:

        for year in years:

            mxd = path_to_mxds + '/inundated_areas_{0}_' .format(year) + projection + '.mxd'

            print 'MXD is: ' + mxd

            output_file = path_to_mxds + '/inundated_areas_{0}_' .format(year) + projection + '.tpk'

            level = "12"

            print 'Outputting to: ' + output_file

            arcpy.CreateMapTilePackage_management(mxd, "ONLINE", output_file, "PNG", level)

            print 'Created tpk for: {0} {1} level {2}' .format(projection, year, level)


extract_by_mask_over_land('east_coast',['NCAH'],['2030','2060'])
#extract_by_mask_over_land('east_coast',['NCAI'],['2035','2060','2100'])

#create_tile_packages(['NCAH'],['2006'])





