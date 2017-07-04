# Extract by mask extracts the inundated area over land for visualization online.

# Create_tile_packages preps tile packages for ArcGIS online

import arcpy
import datetime
import pandas
import zipfile
from arcpy.sa import *
import glob
import os

arcpy.CheckOutExtension("Spatial")

arcpy.env.overwriteOutput = True

def extract_by_mask_over_land(region, projections, years):

    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(region)

    land_polygon = 'land_polygons_clipped_to_{0}_proj' .format(region)

    for projection in projections:

        for year in years:

            #file_to_extract = 'extract_rg_merged_raw_raster_surface_26x_{0}_{1}' .format(year, projection)


            file_to_extract = 'extract_rg_merged_raw_raster_surface_26x_{0}_{1}_all_redo_2' .format(year, projection)

            print 'Extracting ' + file_to_extract + 'at time: {:%Y-%m-%d %H:%M:%S}' .format(datetime.datetime.now())

            out_extract_by_mask = arcpy.sa.ExtractByMask(file_to_extract, land_polygon)

            print 'Extracted ' + file_to_extract + 'at time: {:%Y-%m-%d %H:%M:%S}' .format(datetime.datetime.now())

            out_extract_by_mask.save('{0}_inundated_area_over_land_only_{1}_{2}' .format(region, year, projection))

            print 'Saved'


def create_tile_packages(projections, years, region):

    path_to_mxds = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/' .format(region)

    for projection in projections:

        for year in years:

            mxd = region + '_inundated_areas_over_land_only_{0}_' .format(year) + projection + '.mxd'

            print 'MXD is: ' + mxd

            output_file = path_to_mxds + '{0}_inundated_areas_over_land_only_{1}_' .format(region, year) + projection + '_062517.tpk'

            # level = "12" This was what I did originally.

            level = "14"

            print 'Outputting to: ' + output_file

            print 'Creating tile package for ' + mxd + ' at time: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

            arcpy.CreateMapTilePackage_management(mxd, "ONLINE", output_file, "PNG", level)

            print 'Created tile package for ' + output_file + ' at time: {:%Y-%m-%d %H:%M:%S}'.format(
                datetime.datetime.now())

            print 'Created tpk for: {0} {1} level {2}' .format(projection, year, level)

# This preps inundated area shapefiles for public use

def export_cohort_to_shapefile(years, projection, region, states):
    arcpy.env.workspace = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/{0}/{0}.gdb'.format(
        region)

    output_folder = 'C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/inundated_area_shapefiles_for_dropbox/'

    state_codes = pandas.read_csv('C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/state_numbers.csv',
                                  dtype={'Number': str})

    for state in states:

        for index, row in state_codes.iterrows():

            if str(row[0]) == state:
                state_abbr = row[1]

        for year in years:

            original = 'final_polygon_26x_{0}_{1}_merged_clip_to_{2}'.format(year, projection, state)

            #new_name = '{0}_{1}_{2}_chronically_inundated_area' .format(state_abbr.strip(), year, projection)

            new_name = '{0}_today_chronically_inundated_area'.format(state_abbr.strip()) # For present day

            #print new_name

            arcpy.CopyFeatures_management(original, new_name)

            print 'Copied to new file'

            arcpy.FeatureClassToShapefile_conversion(new_name, output_folder)

            print 'Exported state {0} {1} {2} to shapefile'.format(state, year, projection)

            os.chdir(output_folder)

            print 'creating archive'

            files_to_add = glob.glob('{0}*' .format(new_name))

            #print files_to_add

            output_zipfile = '{0}.zip' .format(new_name)

            zf = zipfile.ZipFile(output_zipfile, mode='w')

            print 'created archive'

            for file in files_to_add:

                #print file

                zf.write(file)

                print 'added ' + file + ' to archive'

            zf.write('README.txt')

            print 'added README to archive'

            zf.close()







#extract_by_mask_over_land('east_coast',['NCAI'],['2080'])
#extract_by_mask_over_land('east_coast',['NCAI'],['2035','2060','2080','2100'])
#extract_by_mask_over_land('east_coast',['NCAL'],['2060','2100'])


#create_tile_packages(['NCAH'],['2060'],'west_coast')

export_cohort_to_shapefile(['2006'],'NCAH','east_coast',['13','09','12'])
export_cohort_to_shapefile(['2006'],'NCAH','west_coast',['06'])
# export_cohort_to_shapefile(['2035','2060','2100'],'NCAI','east_coast',['13','09','12'])
# export_cohort_to_shapefile(['2030','2060','2100'],'NCAH','east_coast',['13','09','12'])
# export_cohort_to_shapefile(['2035','2060','2100'],'NCAI','west_coast',['06'])
# export_cohort_to_shapefile(['2030','2060','2100'],'NCAH','west_coast',['06'])





