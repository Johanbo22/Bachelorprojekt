'''
Name: Burn buildings into DTM
Purpose: Burning building footprint into DTM as impermeable barriers. 

Author: Johan Bo Kjær
Version: 1.0

Note: this is currently just script for the python console. a plugin version is not made yet
'''

import os, traceback
import time
from venv import create
import numpy as np
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsProcessingFeedback, QgsMessageLog, Qgis, QgsWkbTypes,
    QgsFeatureRequest, QgsExpression, QgsExpressionContext,
    QgsExpressionContextUtils, QgsRasterBandStats, QgsRasterFileWriter,
    QgsRasterPipe, QgsRasterProjector, QgsRasterInterface,
    edit, QgsVectorDataProvider, QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer, QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber, QgsProcessingParameterFolderDestination,
    QgsProcessingException
)
from qgis.analysis import QgsRasterCalculatorEntry, QgsRasterCalculator
import processing
from PyQt5.QtCore import QVariant
from osgeo import gdal, ogr, osr

def burn_buildings(dtm_raster, building_layer, height_value, output_folder):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print("Loading building layer as vector")
    building_layer = QgsVectorLayer(building_layer, "building_polygons", "ogr")

    if not building_layer.isValid():
        print("Failed to load the building layer")
        print(traceback.format_exc())
        return
    else:
        print("Layer loaded")
    
    try:
        print("Adding a new field to building attribute table...")
        # add new field to temp field
        field_name = "elevation"
        new_field = QgsField(field_name, QVariant.Int)

        print("Starting editing mode")
        building_layer.startEditing()

        # add the new field to the files attribute data
        print("Adding field to file")
        building_layer.dataProvider().addAttributes([new_field])
        building_layer.updateFields()

        print(f"Using height value: {height_value}")
        elevation_value = height_value
        
        # assign it to each feature in the attribute table
        for feature in building_layer.getFeatures():
            feature_id = feature.id()
            building_layer.changeAttributeValue(feature_id, building_layer.fields().indexFromName(field_name), elevation_value)
        
        print("Committing")
        #commit and save changes
        building_layer.commitChanges()
        print(f"Height values for building footprints added to {building_layer}")
    except:
        print("Failed to add a new field to building layer")

    ####### convertd
    print("Converting building polygons to raster")
    building_raster = os.path.join(output_folder, "Building_raster.tif")

    #DTM INFO
    dtm_layer = QgsRasterLayer(dtm_raster, "dtm")
    if not dtm_layer.isValid():
        raise Exception(f"Failed to load DTM: {dtm_raster}")
    
    dtm_provider = dtm_layer.dataProvider()
    dtm_extent = dtm_provider.extent()
    dtm_width = dtm_layer.width()
    dtm_height = dtm_layer.height()
    cell_size_x = dtm_extent.width() / dtm_width
    cell_size_y = dtm_extent.height() / dtm_height
    dtm_extent_str = f"{dtm_extent.xMinimum()},{dtm_extent.xMaximum()},{dtm_extent.yMinimum()},{dtm_extent.yMaximum()}"
    
    print(f"Cell size: {cell_size_x}, {cell_size_y}, Extent_str: {dtm_extent_str}")
    try:
        parameters = {
            'INPUT': building_layer,
            'FIELD': field_name,
            'BURN': 0,
            'UNITS': 1,
            'WIDTH': cell_size_x,
            'HEIGHT': cell_size_y,
            'EXTENT': dtm_extent_str,
            'NODATA': 0,
            'DATA_TYPE': 5, #int32
            'OUTPUT': building_raster
        }
        rasterise_buildings = processing.run("gdal:rasterize", parameters)
        building_raster = rasterise_buildings['OUTPUT']
        print("Rasterisation of buildings complete")

    except:
        print("Rasterisation failed")
        print(traceback.format_exc())
        return
    
    print("Assigning 0 to NoData values")
    try:
        build_raster_new = os.path.join(output_folder, "Building_raster_NONull.tif")

        processing.run("native:fillnodata", {
            'INPUT': building_raster,
            'BAND': 1,
            'FILL_VALUE': 0,
            'OUTPUT': build_raster_new
        })
        print("FillNoData has been completed")
        build_raster = QgsRasterLayer(build_raster_new, "BuildingRaster")
    
    except Exception:
        print("FillNoData failed")
        print(traceback.format_exc())

    print("DTM layer already loaded (line 76)")
    
    try:
        combined_raster_path = os.path.join(output_folder, "DHyM_with_buildings.tif")
        combined_raster = QgsRasterLayer(combined_raster_path, "DHyMBuildingRaster")

        print("Creating expression for combining rasters...")
        expression = f'"{build_raster.name()}@1" + "{dtm_layer.name()}@1"'
        print(f"Expression is: {expression}")

        processing.run("native:rastercalc", {
            'EXPRESSION': expression,
            'LAYERS': [build_raster, dtm_layer],
            'OUTPUT': combined_raster_path
        })
        print("Combining complete")
        print("Buildings added to DTM")
    except Exception:
        print("Raster calculator failed. Combining DTM and buildings not completed")
        print(traceback.format_exc())

#####plugin information





### tests
def main():
    burn_buildings(
        dtm_raster=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\output\DTM_with_hydro_adaptations.tif",
        building_layer=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\buildings_hesnaes.shp",
        height_value=20,
        output_folder=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\test_building_burn"
    )

if __name__ == "__main__":
    main()

    
