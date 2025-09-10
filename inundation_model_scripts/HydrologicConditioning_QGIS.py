'''
Name:      Hydrologic Conditioning

Purpose:   Hydrologically corrects an digital terrain model using hydro adaptation datasets. The script changes the input DTM by burning down the values of interpolated lines in a new raster.
Author:    Johan Bo Kjær (2025). Based on script from Thomas Balstrøm
Version:   1.0.1

Issues:    The counter is buggy in system. When the process for "assigning Z-values to points" the counter stops at 98% before finishing around 10-15 seconds later. I dont know what causes this or if its a "quirk" of QGIS. Also removal of temp_FIles is not very efficient
'''

import os, time, math
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsProcessingFeedback, QgsMessageLog, Qgis, QgsWkbTypes,
    QgsFeatureRequest, QgsExpression, QgsExpressionContext,
    QgsExpressionContextUtils, QgsRasterBandStats, QgsRasterFileWriter,
    QgsRasterPipe, QgsRasterProjector, QgsRasterInterface,
    edit, QgsVectorDataProvider
)
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterVectorLayer, QgsProcessingParameterRasterLayer, QgsProcessingParameterFolderDestination, QgsProcessingParameterFeatureSink, QgsProcessingException
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing
from PyQt5.QtCore import QVariant
import numpy as np
from osgeo import gdal, ogr, osr

def hydro_conditioning(digitized_lines_path, dtm_path, output_workspace_path, feedback=None):

    # start the time counter?
    start_time = time.time()

    if feedback is None:
        feedback = QgsProcessingFeedback()
    
    feedback.pushInfo("Starting the hydrological conditioning of DTM")

    #load initial data
    digit_layer = QgsVectorLayer(digitized_lines_path, "digitized_lines", "ogr")
    if not digit_layer.isValid():
        raise Exception(f"Failed to load the adaptation lines: {digitized_lines_path}")
    
    dtm_layer = QgsRasterLayer(dtm_path, "dtm")
    if not dtm_layer.isValid():
        raise Exception(f"Failed to load DTM: {dtm_path}")
    
    feedback.pushInfo(f"No of polylines to be hydro adapted onto DTM is: {digit_layer.featureCount()}")

    #create outdir
    os.makedirs(output_workspace_path, exist_ok=True)

    #modification
    
    #dissolve the lines
    feedback.pushInfo("Dissolving")
    dissolved_path = os.path.join(output_workspace_path, "dissolve_lines.shp")
    dissolved_result = processing.run("native:dissolve", {
        'INPUT': digit_layer,
        'FIELD': [],
        'SEPARATE_DISJOINT': True,
        'OUTPUT': dissolved_path
    })
    dissolved_layer = QgsVectorLayer(dissolved_result['OUTPUT'], "dissolved", "ogr")

    # extract the start and end points of lines
    feedback.pushInfo("Extracting the start and end points of digitized lines features")
    start_points_path = os.path.join(output_workspace_path, "start_points.shp")
    end_points_path = os.path.join(output_workspace_path, "end_points.shp")

    # extrat start values
    processing.run("native:extractspecificvertices", {
        'INPUT': dissolved_layer,
        'VERTICES': "0", # <- this is the first vertex (-1 is the last)
        'OUTPUT': start_points_path
    })

    # extract end point
    processing.run("native:extractspecificvertices", {
        'INPUT': dissolved_layer,
        'VERTICES': "-1",
        'OUTPUT': end_points_path
    })

    start_points_layer = QgsVectorLayer(start_points_path, "start_points", "ogr")
    end_points_layer = QgsVectorLayer(end_points_path, "end_points", "ogr")

    #sampe raster values at the start end ppooints
    feedback.pushInfo("Getting point Z-values from dtm")

    start_sampled_path = os.path.join(output_workspace_path, "start_sampled.shp")
    processing.run("native:rastersampling", {
        'INPUT': start_points_layer,
        'RASTERCOPY': dtm_layer,
        'COLUMN_PREFIX': 'dtm_',
        'OUTPUT': start_sampled_path
    })

    end_sampled_path = os.path.join(output_workspace_path, "end_sampled.shp")
    processing.run("native:rastersampling", {
        'INPUT': end_points_layer,
        'RASTERCOPY': dtm_layer,
        'COLUMN_PREFIX': 'dtm_',
        'OUTPUT': end_sampled_path
    })

    start_sampled_layer = QgsVectorLayer(start_sampled_path, "start_sampled", "ogr")
    end_sampled_layer = QgsVectorLayer(end_sampled_path, "end_sampled", "ogr")

    # storing Z values in dictorionaru
    start_z = {}
    end_z = {}
    start_xy = {}
    end_xy = {}

    # get dtm column name
    start_fields = start_sampled_layer.fields().names()
    end_fields = end_sampled_layer.fields().names()
    feedback.pushInfo(f"Start fields: {start_fields}")
    feedback.pushInfo(f"End fields: {end_fields}")

    dtm_cols = [f for f in start_fields if f.startswith("dtm_")]
    if not dtm_cols:
        raise Exception(f"no dtm sampling field found in {start_sampled_layer}")
    dtm_col = dtm_cols[0]
    feedback.pushInfo(f"Using DTM sampling: {dtm_col}")

    #dtm_col = f"dtm_{os.path.splitext(os.path.basename(dtm_path))[0]}_1"

    def to_float(val):
        if val is None:
            return None
        if hasattr(val, "value"):
            val = val.value()
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    # start point dicts
    for feature in start_sampled_layer.getFeatures():
        fid = feature['vertex_index'] if 'vertex_index' in start_fields else feature.id()
        geom = feature.geometry()
        if geom.type() == QgsWkbTypes.PointGeometry:
            point = geom.asPoint()
            start_xy[fid] = (point.x(), point.y())

            val = feature[dtm_col]
            start_z[fid] = to_float(val) if val is not None else None
    
    # end point
    for feature in end_sampled_layer.getFeatures():
        fid = feature['vertex_index'] if 'vertex_index' in end_fields else feature.id()
        geom = feature.geometry()
        if geom.type() == QgsWkbTypes.PointGeometry:
            point = geom.asPoint()
            end_xy[fid] = (point.x(), point.y())

            val = feature[dtm_col]
            end_z[fid] = to_float(val) if val is not None else None
    
    # add the StartZ and endZ fields to dissolved lines
    dissolved_layer.dataProvider().addAttributes([
        QgsField("StartZ", QVariant.Double),
        QgsField("EndZ", QVariant.Double)
    ])
    dissolved_layer.updateFields()

    # update the layers with z values
    feedback.pushInfo("Update the lines with z-values")
    with edit(dissolved_layer):
        for feature in dissolved_layer.getFeatures():
            fid = feature.id()
            if fid in start_z and fid in end_z:
                feature['StartZ'] = start_z[fid]
                feature['EndZ'] = end_z[fid]
                dissolved_layer.updateFeature(feature)
    
    #conversion to raster
    feedback.pushInfo("Converting the lines to raster")

    #dtm info
    dtm_provider = dtm_layer.dataProvider()
    dtm_extent = dtm_provider.extent()
    dtm_width = dtm_layer.width()
    dtm_height = dtm_layer.height()
    cell_size_x = dtm_extent.width() / dtm_width
    cell_size_y = dtm_extent.height() / dtm_height
    feedback.pushInfo(f"DTMWIDTH: {dtm_width}, dtmheight: {dtm_height}")

    # rasterise the lines
    rasterised_path = os.path.join(output_workspace_path, "rasterised_lines.tif")

    # try 
    rasterization_complete = False

    try:
        #try Gdal first
        feedback.pushInfo("GDAL rasterisation")

        feature_count = dissolved_layer.featureCount()
        feedback.pushInfo(f"Dissolved layer hsa: {feature_count} features")

        if feature_count == 0:
            feedback.reportError("No features to be rasterised")
            return None
        
        dissolved_layer.dataProvider().addAttributes([QgsField("burn_value", QVariant.Int)])
        dissolved_layer.updateFields()

        with edit(dissolved_layer):
            for feature in dissolved_layer.getFeatures():
                feature['burn_value'] = feature.id() + 1
                dissolved_layer.updateFeature(feature)
        
        temp_dissolved_path = os.path.join(output_workspace_path, "temp_dissolved.shp")
        QgsVectorFileWriter.writeAsVectorFormat(dissolved_layer, temp_dissolved_path, "UTF-8", dissolved_layer.crs(), "ESRI Shapefile")
        temp_dissolved_layer = QgsVectorLayer(temp_dissolved_path, "temp_dissolved", "ogr")

        result = processing.run("gdal:rasterize", {
            'INPUT': temp_dissolved_layer,
            'FIELD': 'burn_value',
            'BURN': 0,
            'USE_Z': False,
            'UNITS': 1,
            'WIDTH': cell_size_x,
            'HEIGHT': cell_size_y,
            'EXTENT': f"{dtm_extent.xMinimum()},{dtm_extent.xMaximum()},{dtm_extent.yMinimum()},{dtm_extent.yMaximum()}",
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': rasterised_path
        }, feedback=feedback)

        if os.path.exists(rasterised_path):
            feedback.pushInfo(f"Rasterisation complete: {rasterised_path}")
            rasterization_complete = True
        else:
            feedback.pushInfo("GDAL rasterisation failed. no file created")
    
    except Exception as e:
        feedback.pushInfo(f"gDAl rasterisation failed with error: {str(e)}")
    
    if not rasterization_complete:
        try:
            feedback.pushInfo("Native rasterisation")

            result = processing.run("qgis:rasterize", {
                'LAYER': temp_dissolved_layer,
                'FIELD': 'burn_value',
                'DIMENSIONS': 1,
                # 'WIDTH': dtm_width,
                # 'HEIGHT': dtm_height,
                'EXTENT': f"{dtm_extent.xMinimum()}, {dtm_extent.xMaximum()}, {dtm_extent.yMinimum()}, {dtm_extent.yMaximum()}",
                # 'TLX': dtm_extent.xMinimum(),
                # 'TLY': dtm_extent.yMaximum(),
                # 'DATA_TYPE': 5,
                'PIXEL_SIZE': cell_size_x,
                'OPTIONS': 'COMPRESS=LZW',
                'OUTPUT': rasterised_path
            }, feedback=feedback)

            if os.path.exists(rasterised_path):
                feedback.pushInfo(F"Native rasterisation complete: {rasterised_path}")
                rasterization_complete = True
            else:
                feedback.pushInfo("Native rasterisation failed: No file created")
        
        except Exception as e:
            feedback.pushInfo(f"native rasterisation failed: Errror: {str(e)}")
    
    #direct GDAL approach
    if not rasterization_complete:
        try:
            feedback.pushInfo("Trying direct GDAL rasterisation")

            source_ds = ogr.Open(temp_dissolved_layer)
            source_layer = source_ds.GetLayer()

            target_ds = gdal.GetDriverByName("GTiff").Create(rasterised_path, dtm_width, dtm_height, 1, gdal.GDT_Float32)

            geotransform = [
                dtm_extent.xMinimum(),
                cell_size_x,
                0,
                dtm_extent.yMaximum(),
                0,
                -cell_size_y
            ]
            target_ds.SetGeoTransform(geotransform)
            target_ds.SetProjection(dtm_layer.crs().toWkt())

            #rasterise
            band = target_ds.GetRasterBand(1)
            band.SetNoDataValue(0)
            gdal.RasterizeLayer(target_ds, [1], source_layer, options=["ATTRIBUTE=burn_value", "ALL_TOUCHED=TRUE"])

            target_ds = None
            source_ds = None

            if os.path.exists(rasterised_path):
                feedback.pushInfo(f"Direct GDAL rasterisation complete {rasterised_path}")
                rasterization_complete = True
            else:
                feedback.pushInfo("Direct rasterisation failed. no file created")
        
        except Exception as e:
            feedback.pushInfo(f"Direct rasterisation failed with error: {str(e)}")
    
    if not rasterization_complete or not os.path.exists(rasterised_path):
        feedback.pushInfo("All rasterisation attempts failed")
        return None
    
    try:
        test_raster = gdal.Open(rasterised_path)
        if test_raster is None:
            feedback.reportError("Rasterised file exists but cannot be opened")
            return None
        
        band = test_raster.GetRasterBand(1)
        stats = band.GetStatistics(False, True)
        if stats[2] == 0 and stats[3] == 0:
            feedback.pushInfo("Warning: Rasterised file contains no data")
        else:
            feedback.pushInfo(f"Rasterised file stats: Min:{stats[0]}, Max:{stats[1]}")
        
        test_raster = None
    
    except Exception as e:
        feedback.pushInfo(f"Could not verifyt raster: {str(e)}")
    
    # convert raster to points
    raster_points_path = os.path.join(output_workspace_path, "raster_points.shp")

    try:
        processing.run("native:pixelstopoints", {
            'INPUT_RASTER': rasterised_path,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'grid_code',
            'OUTPUT': raster_points_path
        }, feedback=feedback)
        feedback.pushInfo(f"Raster to points conversion complete: {raster_points_path}")
    except Exception as e:
        feedback.reportError(f"Failed to convert raster to points: {str(e)}")
        return None

    raster_points_layer = QgsVectorLayer(raster_points_path, "raster_points", "ogr")

    if not raster_points_layer.isValid():
        feedback.reportError(f"Failed to load raster points layer: {raster_points_path}")
        return None

    # Check if we have points
    point_count = raster_points_layer.featureCount()
    feedback.pushInfo(f"Created {point_count} raster points")
    
    if point_count == 0:
        feedback.reportError("No points created from raster conversion")
        return None

    # add dist
    raster_points_layer.dataProvider().addAttributes([
        QgsField("Distance", QVariant.Double),
        QgsField("Zest", QVariant.Double)
    ])
    raster_points_layer.updateFields()

    feedback.pushInfo("Data Ready. INTERPolation starting")


    #calculate the deltaZ value
    delta_z_dict = {}
    for feature in dissolved_layer.getFeatures():
        fid = feature.id()
        start_z_val = feature['StartZ']
        end_z_val = feature['EndZ']

        if start_z_val is not None and end_z_val is not None:
            try:
                start_val = float(start_z_val)
                end_val = float(end_z_val)
                geom = feature.geometry()
                length = geom.length()
                if length > 0:
                    delta_z_dict[fid] = (end_val - start_val) / length
            except (TypeError, ValueError):
                feedback.pushInfo(f"Skipping feature {fid}: invalid Z values ({start_z_val}, {end_z_val})")


    #interpolate the the values along lines
    feedback.pushInfo("Assign zvalues to cells along lines")

    interpolated_count = 0
    attr_distance_idx = raster_points_layer.fields().indexFromName("Distance")
    attr_zest_idx = raster_points_layer.fields().indexFromName("Zest")
    updates = {}
    
    total_points = raster_points_layer.featureCount()
    counter = 0

    for feature in raster_points_layer.getFeatures():
        counter += 1
        if counter % 100 == 0:
            feedback.pushInfo(f"Processing: {counter} / {total_points}")
            if feedback.isCanceled():
                feedback.pushInfo('Processing cancled by user')
                break
        

        grid_code = feature['grid_code']
        if grid_code is None:
            continue

        line_fid = grid_code - 1

        if line_fid in start_xy and line_fid in start_z and line_fid in delta_z_dict:
            geom = feature.geometry()
            if geom.type() == QgsWkbTypes.PointGeometry:
                point = geom.asPoint()

                # calculate distances
                start_point = start_xy[line_fid]
                distance = math.sqrt((start_point[0] - point.x())**2 + (start_point[1] - point.y())**2)

                z_est = start_z[line_fid] + (distance * delta_z_dict[line_fid])

                updates[feature.id()] = {attr_distance_idx: distance, attr_zest_idx: z_est}
                interpolated_count += 1
    
    raster_points_layer.dataProvider().changeAttributeValues(updates)
    # with edit(raster_points_layer):
    #     for feature in raster_points_layer.getFeatures():
    #         grid_code = feature['grid_code']
            
    #         line_fid = grid_code - 1  
            
    #         if line_fid in start_xy and line_fid in start_z and line_fid in delta_z_dict:
    #             geom = feature.geometry()
    #             if geom.type() == QgsWkbTypes.PointGeometry:
    #                 point = geom.asPoint()
                
    #                 #calculate the distances
    #                 start_point = start_xy[line_fid]
    #                 distance = math.sqrt((start_point[0] - point.x())**2 + (start_point[1] - point.y())**2)

    #                 #interpolated zvalues calculation
    #                 z_est = start_z[line_fid] + (distance * delta_z_dict[line_fid])

    #                 feature['Distance'] = distance
    #                 feature['Zest'] = z_est
    #                 raster_points_layer.updateFeature(feature)
    #                 interpolated_count += 1
    
    feedback.pushInfo(f"Interpolated Z values for {interpolated_count} points")
    feedback.pushInfo(f"Converted {len(start_xy)} lines out of {dissolved_layer.featureCount()}")

    #convert points back to raster
    feedback.pushInfo("Hydrocorrecting DTM raster")
    hydro_raster_path = os.path.join(output_workspace_path, "hydro_adapted_DTM.tif")

    processing.run("gdal:rasterize", {
        'INPUT': raster_points_layer,
        'FIELD': 'Zest',
        'BURN': 0,
        'USE_Z': False,
        'UNITS': 1,
        'WIDTH': cell_size_x,
        'HEIGHT': cell_size_y,
        'EXTENT': f"{dtm_extent.xMinimum()},{dtm_extent.xMaximum()},{dtm_extent.yMinimum()},{dtm_extent.yMaximum()}",
        'NODATA': -9999,
        'DATA_TYPE': 6, #Float64
        'OUTPUT': hydro_raster_path
    }, feedback=feedback)

    feedback.pushInfo("Combining hydro raster with original DTM")
    result_path = os.path.join(output_workspace_path, "DTM_with_hydro_adaptations.tif")

    dtm_ds = gdal.Open(dtm_path)
    hydro_ds = gdal.Open(hydro_raster_path)

    # create new raster
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(result_path, dtm_width, dtm_height, 1, gdal.GDT_Float64)
    out_ds.SetGeoTransform(dtm_ds.GetGeoTransform())
    out_ds.SetProjection(dtm_ds.GetProjection())

    dtm_array = dtm_ds.GetRasterBand(1).ReadAsArray()
    hydro_array = hydro_ds.GetRasterBand(1).ReadAsArray()

    #combine
    result_array = np.where((hydro_array != -9999) &(~np.isnan(hydro_array)), hydro_array, dtm_array)

    #write result to raster
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(result_array)
    out_band.SetNoDataValue(-9999)

    #close 
    dtm_ds = None
    hydro_ds = None
    out_ds = None

    #clean up
    feedback.pushInfo("Removing temporary files")
    temp_files = [dissolved_path, start_points_path, end_points_path, start_sampled_path, 
                  end_sampled_path, rasterised_path, raster_points_path, hydro_raster_path, temp_dissolved_path]

    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                    file_with_ext = temp_file.replace('.shp', ext)
                    if os.path.exists(file_with_ext):
                        os.remove(file_with_ext)
                if not temp_file.endswith('.shp'):
                    os.remove(temp_file)
        
        except:
            pass
    
    time_spent_secs = int(time.time() - start_time)
    minutes_spent = time_spent_secs // 60
    seconds_spent = time_spent_secs % 60

    feedback.pushInfo("Complete")
    feedback.pushInfo(f"Execution Time: {minutes_spent} mins. {seconds_spent} seconds.")

    return result_path

### plugin implementation
class HydrologicConditioningAlgorithm(QgsProcessingAlgorithm):

    INPUT_LINES = 'INPUT_LINES'
    INPUT_DTM = 'INPUT_DTM'
    OUTPUT_WORKSPACE = 'OUTPUT_WORKSPACE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LINES, "LinesToBurnOntoDTM", [QgsWkbTypes.LineGeometry]))

        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DTM, "DTM to burn onto"))

        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_WORKSPACE, "Output Workspace"))
    
    def processAlgorithm(self, parameters, context, feedback):
        lines_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINES, context)

        dhm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DTM, context)
        
        output_workspace = self.parameterAsString(parameters, self.OUTPUT_WORKSPACE, context)

        if not lines_layer or not dhm_layer or not output_workspace:
            raise QgsProcessingException("Invalid input parameters")
        
        result_path = hydro_conditioning(digitized_lines_path=lines_layer.source(), dtm_path=dhm_layer.source(), output_workspace_path=output_workspace, feedback=feedback)

        if result_path:
            project = QgsProject.instance()

            path = result_path
            name = "DHyM Corrected"
            print(f" - {name}: {path}")

            layer = QgsRasterLayer(path, name)
            if layer.isValid():
                project.addMapLayer(layer)
            return {self.OUTPUT: result_path}
        else:
            raise QgsProcessingException("Failed to create output")
        
    def name(self):
        return "hydroconditioning"
    
    def displayName(self):
        return "Hydrocorrect a DTM with hydrological adaptations"
    
    def group(self):
        return "Hydrology"
    
    def groupId(self):
        return "hydrology"
    
    def createInstance(self):
        return HydrologicConditioningAlgorithm()
