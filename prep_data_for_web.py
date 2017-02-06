import arcpy

arcpy.env.overwriteOutput = True

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


create_tile_packages(['NCAH'],['2006'])





