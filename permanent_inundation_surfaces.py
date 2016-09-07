import arcpy
import os
import glob
arcpy.CheckOutExtension("Spatial")


# def prep_gauge_data_for_interpolation():

arcpy.env.workspace = ## PATH TO GDB HERE

arcpy.MakeXYEventLayer_management(
    "C:/Users/kristydahl/Desktop/GIS_Data/permanent_inundation/scratch/long_lat_mhhw_ft_above_navd88 - east_gulf.csv",
    "Longitude", "Latitude", "gauges_points", "") ## CHANGE PATH SO READING FROM GDB; NEED TO PREP DATA FILE STILL, WITH WATER LEVELS WRT MHHW

arcpy.FeatureClassToFeatureClass_conversion("gauges_points","C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch", "test_fc_to_fc_conversion.shp") ## CHANGE PATH SO READING FROM GDB

# Make Layer from empty transect points file

transect_points_layer = arcpy.MakeFeatureLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/empty_points.shp",'transect_points_layer') ## CHANGE PATH SO READING FROM GDB

# Join empty points and gauges file (Should this be done once, then loop through fields to interpolate? I think so)
AddJoin_management('transect_points_layer','Near_FID',output_from_fc_to_fc_conversion above, 'FID','KEEP_COMMON')

return transect_points_layer


# def interpolate_and_create_water_level_surfaces(years, projections): parameters: [years as list], [projections as list]
    # will the join created above still apply? Yes if I call that method within this one (I think):

    prep_gauge_data_for_interpolation(params?)

    mhhw_layer = arcpy.MakeRasterLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/all_noaa_mhhw_mosaic",'mhhw_layer') # CHANGE PATH SO READING FROM GDB

    # Set interpolation limit as polygon created from coastal counties
    arcpy.env.mask = arcpy.MakeFeatureLayer_management("C:/Users/kristydahl/Desktop/GIS_data/permanent_inundation/scratch/all_noaa_mhhw_mosaic_polygon") # CHANGE PATH SO READING FROM GDB

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


# For each year/proj horizon (as fields in the joined points file), interpolate empty points file based on field from joined table (gauges water level
    for projection in projections:

        for year in years:

            # interpolate between points
            interpolated_surface_wrt_mhhw = arcpy.idw(transect_points_layer,str(year + '_' + proj), cellsize)

            arcpy.MakeRasterLayer_management(interpolated_surface_wrt_mhhw, 'interpolated_surface_wrt_mhhw')

            # add to mhhw surface     # Make sure resolutions of two raster are the same
            # There may be issues with coordinate systems/projections. Be aware.

            water_level_surface = Raster(mhhw_layer) + Raster(interpolated_surface_wrt_mhhw)

            # Save WLS with some format that includes year and projection
            outname = 'water_level_surface_wrt_navd_' + year + '_' + proj

            water_level_surface.save(outname)



# def subtract_dems_from_wls_and_finalize_each_chunk(): parameters: [years as list], [projections as list]

    for projection in projections:

        for year in years:

            # get the specific WLS from the gdb
            water_level_surface = arcpy.ListRasters('water_level_surface_wrt_navd_%s_%s' %(year, projection))[0]
            outname_resampled_water_level_surface = 'water_level_surface_wrt_navd_%s_%s_resampled' %(year, projection)

            # get DEMS from gdb

            dems = arcpy.ListRasters('*final_DEM*')

            # Loop through DEMs in a database (get all rasters with final_DEM in name)

            for dem in dems:

                # set mask to dem extent
                arcpy.env.mask = dem

                # Get resolution of DEM

                cellsize_properties = ["CELLSIZEX"]
                cellsizes = []

                for cellsize_property in cellsize_properties:
                    size_tmp = arcpy.GetRasterProperties_management(dem, cellsize_property)
                    size = size_tmp.getOutput(0)
                    cellsizes.append(size)
                    cellsizes = [float(item) for item in cellsizes]

                    cellsize = cellsizes[0]
                    print 'Cell size of DEM is: ' + str(cellsize)

                # Resample WLS to resolution of DEM (don't want to have to save this...how to avoid?
                arcpy.Resample_management(water_level_surface,outname_resampled_water_level_surface, cellsize, "BILINEAR")

                # Compare DEM and water level surface. Where WLS >= DEM, set value of 1
                inundated_area_surface = Con(Raster(outname_water_level_surface)>= Raster(dem), 1)

                outname_inundated_area_surface = 'inundated_area_surface_%s_%s_' %(year, projection) + dem[:-10]

                inundated_area_surface.save(outname_inundated_area_surface)



    # Region group/extract, convert to polygon (here? later?)
    # Save the region group/extract chunk
    # Merge the chunks either using merge (for polygons) or mosaic to new raster (for raster)


# def region_group_extract(location, dem_file,slr_file):
#     paths = set_file_paths(location, dem_file,slr_file)
#     surfaces = water_surfaces(location, dem_file,slr_file)
#
#     region_grouped_files = []
#     extracted_files = []
#     final_polygons = []
#
#     for surface in surfaces:
#         fullname = str(surface)
#         print('surface name is ' + fullname)
#         filename = os.path.basename(fullname)
#
#         # Perform region group
#         print('Region grouping' + filename)
#         outRegionGrp = RegionGroup(fullname, "EIGHT", "WITHIN",'NO_LINK')
#         outname_rg = (paths['results'] + str("/rg_" + filename))
#         outRegionGrp.save(outname_rg)
#
#         print("Region grouped" + filename)
#
#         # Extract connected areas
#
#         fullname = str(outname_rg)
#         print('File to extract is ' + fullname)
#         filename = os.path.basename(fullname)
#         outname_extract = (paths['results'] +  str('/extract_' + filename))
#
#         print('Extracting' + filename)
#         arr = arcpy.da.FeatureClassToNumPyArray(outname_rg, ('Value', 'Count'))
#         count = arr['Count']
#         value = arr['Value']
#         index_to_extract = numpy.argmax(count)
#         value_to_extract = str(value[index_to_extract])
#
#         inSQLClause = 'Value =' + value_to_extract
#         print('Extracting ' + value_to_extract + 'from ' + filename)
#
#         attExtract = ExtractByAttributes(fullname, inSQLClause)
#         attExtract.save(outname_extract)
#         extracted_files.append(attExtract)
#         print('Extracted connected areas from' + outname_rg)
#
#         # create polygon
#         fullname = str(outname_extract)
#         filename = os.path.basename(fullname)
#         outname_polygon = str(paths['results'] + '/final_polygon_' + filename )
#
#
#         arcpy.RasterToPolygon_conversion(fullname, outname_polygon,"SIMPLIFY", "VALUE")
#         final_polygons.append(outname_polygon)
#
#         print('Converted ' + outname_extract + ' to polygon')
#     return {'final_polygons': final_polygons}


# def combine_chunks