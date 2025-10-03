import os, traceback
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
import processing
from PyQt5.QtCore import QVariant
from osgeo import gdal, ogr, osr

def burn_buildings(dtm_raster, building_layer, height_value, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    feedback = QgsProcessingFeedback()

    feedback.pushInfo("Loading building layer...")
    building_layer = QgsVectorLayer(building_layer, "building_polygons", "ogr")

    if not building_layer.isValid():
        feedback.pushInfo("Failed to the load the building layer")
        feedback.reportError(traceback.format_exc())
        return
    else:
        print("Layer loaded")

    try:
        feedback.pushInfo("Adding new field to building attribute table")
        field_name = "elevation"
        new_field = QgsField(field_name, QVariant.Double)

        building_layer.startEditing()
        building_layer.dataProvider().addAttributes([new_field])
        building_layer.updateFields()

        feedback.pushInfo(f"Using height value: {height_value} and assiging it to each feature in {building_layer}")
        elevation_value = height_value

        for feature in building_layer.getFeatures():
            feature_id = feature.id()
            building_layer.changeAttributeValue(feature_id, building_layer.fields().indexFromName(field_name), elevation_value)
        
        feedback.pushInfo("Assigned. Committing")
        building_layer.commitChanges()
        feedback.pushInfo(f"Heigh values for building polygons added to {building_layer}")
    except Exception:
        feedback.reportError(f"Failed to a new field to building layer: {traceback.format_exc()}")

    feedback.pushInfo("Converting building polygons to raster")
    building_raster = os.path.join(output_folder, "Building_raster.tif")

    dtm_layer = QgsRasterLayer(dtm_raster, "dtm")
    if not dtm_layer.isValid():
        feedback.pushInfo(traceback.format_exc())
        raise Exception(f"Failed to load DTM: {dtm_raster}")
    
    dtm_provider = dtm_layer.dataProvider()
    dtm_extent = dtm_provider.extent()
    dtm_width = dtm_layer.width()
    dtm_height = dtm_layer.height()
    cell_size_x = dtm_extent.width() / dtm_width
    cell_size_y = dtm_extent.height() / dtm_height
    dtm_extent_str = f"{dtm_extent.xMinimum()},{dtm_extent.xMaximum()},{dtm_extent.yMinimum()},{dtm_extent.yMaximum()}"
    
    feedback.pushInfo(f"Cell size: {cell_size_x}, {cell_size_y}, Extent_str: {dtm_extent_str}")
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
        feedback.pushInfo("Rasterisation of building polygons ais completed")
    except Exception:
        feedback.pushInfo("Rasterisation failed")
        feedback.reportError(traceback.format_exc())
        return
    
    feedback.pushInfo("Assigning 0 to NODATA Values")
    try:
        build_raster_new = os.path.join(output_folder, "Building_raster_NONull.tif")

        processing.run("native:fillnodata",{
            'INPUT': building_raster,
            'BAND': 1,
            'FILL_VALUE': 0,
            'OUTPUT': build_raster_new
        })
        feedback.pushInfo("FillNoData has completed. All no data values == 0")
        build_raster = QgsRasterLayer(build_raster_new, "BuildingRaster")
    except Exception:
        feedback.pushInfo("FillNoData failed")
        feedback.reportError(traceback.format_exc())
    
    try:
        combined_raster_path = os.path.join(output_folder, "DHyM_with_buildings.tif")
        combined_raster = QgsRasterLayer(combined_raster_path, "DHyMBuildingRaster")

        feedback.pushInfo("Creating expression for combining rasters...")
        expression = f'"{build_raster.name()}@1" + "{dtm_layer.name()}@1"'
        feedback.pushInfo(f"Expression used: {expression}")

        processing.run("native:rastercalc", {
            'EXPRESSION': expression,
            'LAYERS': [build_raster, dtm_layer],
            'OUTPUT': combined_raster_path
        })
        feedback.pushInfo("Combining complete.\nBuildings added to DTM")
    except Exception:
        feedback.pushInfo("Raster calculator failed. Could not combine DTM and buildings")
        feedback.reportError(traceback.format_exc())
    
    feedback.pushInfo("Process is complete")


#### plugin information

class BurningBuildingsIntoDTM(QgsProcessingAlgorithm):
    INPUT_DTM = "INPUT_DTM"
    INPUT_BUILDING_LAYER = "INPUT_BUILDING_LAYER"
    HEIGHT_VALUE_FOR_BUILDINGS = "HEIGHT_VALUE_FOR_BUILDINGS"
    OUTPUT_FOLDER = "OUTPUT_WORKSPACE"

    def initAlgorithm(self):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_DTM,
            "Input DTM / DHyM Raster layer",
            defaultValue=None
        ))

        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_BUILDING_LAYER,
            "Input building polygons to burn",
            [QgsWkbTypes.PolygonGeometry],
            defaultValue=None
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.HEIGHT_VALUE_FOR_BUILDINGS,
            "Height value added to buildings",
            QgsProcessingParameterNumber.Double,
            defaultValue=20.0
        ))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_FOLDER,
            "Output Workspace"
        ))

    def processAlgorithm(self, parameters, context, feedback):
        try:
            dtm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DTM, context)
            building_layer = self.parameterAsVectorLayer(parameters, self.INPUT_BUILDING_LAYER, context)
            height_value = self.parameterAsDouble(parameters, self.HEIGHT_VALUE_FOR_BUILDINGS, context)
            output_workspace = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

            if not dtm_layer or not dtm_layer.isValid():
                raise QgsProcessingException("Invalid DTM Raster")
            
            if not building_layer or not building_layer.isValid():
                raise QgsProcessingException("Invalid building layer")
            
            if not output_workspace:
                raise QgsProcessingException("Invalid output workspace")
            
            feedback.pushInfo(f"DTM layer: {dtm_layer}")
            feedback.pushInfo(f"Building layer: {building_layer}")
            feedback.pushInfo(f"Height value added to buildings: {height_value}")
            
            result = burn_buildings(
                dtm_layer,
                building_layer,
                height_value,
                output_workspace
            )

            return result

        except Exception as e:
            feedback.reportError(f"Algorithm failed: {str(e)}")
            raise QgsProcessingException(f"Failed to execute: {str(e)}")
    
    def name(self):
        return "burnbuildingsontodtm"
    
    def displayName(self):
        return "Burn Buildings onto a DTM/DHyM"
    
    def group(self):
        return "Hydrology"
    
    def groupId(self):
        return "hydrology"
    
    def createInstance(self):
        return BurningBuildingsIntoDTM()

