'''
Name: Create Inundation QGIS Plugin tool
Purpose: Used with DTM to create flooding extents of coastal storm surges to a given level or model different scenarios.
Features: User inputted values for a sea_level, increments and number of scenarios. Exports to a .tif raster format and a .gpkg vector format for later use
Author: Johan Bo Kjær (2025)
Note: Translated from original model built by Thomas Balstrøm (2022) and implemented into QGIS

Version: 1.0.1
Bugs: The console will scream a bunch of errors and will tell the user that the algorithm failed. However all tests yield results.
      Line At Sea implementation not working properly. Uses vertex[0]
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

def create_inundation(input_dtm_raster, line_at_sea, initial_sea_level_meters, sea_level_increment_meters, number_of_iterations, output_folder, context, feedback):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    feedback.pushInfo("Converting values from meter to centimeter")
    initial_cm = int(initial_sea_level_meters * 100)
    increment_cm = int(sea_level_increment_meters * 100)
    end_cm = initial_cm + ((number_of_iterations) - 1) * increment_cm

    feedback.pushInfo(f"Processing from {initial_cm} cm to {end_cm} cm with an increment of: {increment_cm} cm")

    for cm in range(initial_cm, end_cm + 1, increment_cm):
        feedback.pushInfo("Converting back to meters")
        m = cm / 100.0
        feedback.pushInfo("Converted")
        feedback.pushInfo(f"Processing: {m} meters ({cm} cenitmeters)")

        try:
            feedback.pushInfo("Creating setNull raster")
            temp_setnull = os.path.join(output_folder, f"Temp_SetNull_{cm}.tif")

            if hasattr(input_dtm_raster, "source"):
                dtm_layer = input_dtm_raster
            else:
                dtm_layer = QgsRasterLayer(input_dtm_raster, "dtm")
            
            expression = f'if("{dtm_layer.name()}@1" <= {m}, 1, 0/0)'
            feedback.pushInfo(f"Expression used to calculate: {expression}")

            feedback.pushInfo(f"Identifying cells in DTM below or equal to: {m} meters...")
            try:
                processing.run("native:rastercalc", {
                    'EXPRESSION': expression,
                    'LAYERS': [dtm_layer],
                    'OUTPUT': temp_setnull
                }, context=context, feedback=feedback)
                feedback.pushInfo(f"Raster calculation complete.\nIdentification of NODATA cells for {m} meters is completed")
            except Exception as e:
                feedback.reportError(f"Raster calculation failed: {str(e)}")
            
            feedback.pushInfo("Starting Distance Accumulation through cells")
            feedback.pushInfo("Creating temporary DA raster...")
            temp_da = os.path.join(output_folder, f"DA_{cm}.tif")

            feedback.pushInfo("Getting source for LineAtSea...")
            if hasattr(line_at_sea, "source"):
                sea_line_layer = line_at_sea.source()
            else:
                sea_line_layer = QgsVectorLayer(line_at_sea, "LineAtSea", "ogr")

            raster_layer = QgsRasterLayer(temp_setnull, "TempSetNull")
            if not raster_layer.isValid():
                raise ValueError("Raster TempSetNull is not valid")
            
            stats = raster_layer.dataProvider().bandStatistics(1)
            feedback.pushInfo(f"Raster Min/Max values: {stats.minimumValue} / {stats.maximumValue}")

            try:
                feedback.pushInfo("Executing a DA through cells, using GRASS cost algorithm...")

                result_DA = processing.run("grass7:r.cost", {
                    'input': temp_setnull,
                    'start_points': sea_line_layer,
                    'output': temp_da,
                    'max_cost': 10000,
                    'null_cost': -1,
                    'memory': 500,
                    'flags': 'k'
                }, context=context, feedback=feedback)
                feedback.pushInfo("Distance Accumulation completed")
                feedback.pushInfo(f"Result object: {result_DA}")
                out_layer = QgsRasterLayer(result_DA, ['output'], "DA_Result")
                feedback.pushInfo(f"Is output layer valid: {out_layer.isValid()}")
            except Exception as e:
                feedback.reportError(f"Cost distance algorithm failed: {str(e)}")
        
            feedback.pushInfo("Creating inundation rasters...")
            inundated = os.path.join(output_folder, f"Inundated_{cm}.tif")

            feedback.pushInfo("Combining result with current sea level value...")
            temp_da_layer = QgsRasterLayer(temp_da, "temp_da")

            expression = f'("{temp_da_layer.name()}@1" >= 0) * {cm}'
            feedback.pushInfo(f"Expression used: {expression}")

            try:
                processing.run("native:rastercalc", {
                    'EXPRESSION': expression,
                    'LAYERS': [temp_da_layer],
                    'OUTPUT': inundated
                }, context=context, feedback=feedback)
                feedback.pushInfo("Combination completed")
                feedback.pushInfo(f"Inundated_{cm} completed")
            except Exception as e:
                feedback.reportError(f"Failed to combine results: {str(e)}")
            
            feedback.pushInfo("Converting raster to polygons")
            inundated_poly = os.path.join(output_folder, f"InundatedPoly_{cm}.gpkg")

            try:
                processing.run("gdal:polygonize", {
                    'INPUT': inundated,
                    'BAND': 1,
                    'FIELD': 'value',
                    'EIGHT_CONNECTEDNESS': True,
                    'EXTRA': '',
                    'OUTPUT': inundated_poly
                }, context=context, feedback=feedback)
                feedback.pushInfo("Conversion from raster to polygon completed")
            except Exception as e:
                feedback.reportError(f"Failed to convert to polygon: {str(e)}")
            
            feedback.pushInfo("Clean up time.sjsajdsda")
            try:
                if os.path.exists(temp_setnull):
                    os.remove(temp_setnull)
                    feedback.pushInfo("Temp files removed")
            except:
                feedback.pushInfo(f"Cannot remoe temp files. non necessary files are: {temp_setnull}.\nContinuing...")
                pass
        
        except Exception as e:
            feedback.reportError(f"Error in processing: {m} meters: {str(e)}")
    
    feedback.pushInfo("Process is complete")


###plugin
class InundationAlgorithm(QgsProcessingAlgorithm):
    INPUT_DTM = 'INPUT_DTM'
    INPUT_SEA_LINE = 'INPUT_SEA_LINE'
    INITIAL_SEA_LEVEL = 'INITIAL_SEA_LEVEL'
    SEA_LEVEL_INCREMENT = 'SEA_LEVEL_INCREMENT'
    NUMBER_ITERATIONS = 'NUMBER_ITERATIONS'
    OUTPUT_WORKSPACE = 'OUTPUT_WORKSPACE'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.INPUT_DTM,
            "Input DTM Raster",
            defaultValue=None
        ))

        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_SEA_LINE,
            "Line At Sea",
            [QgsWkbTypes.LineGeometry],
            defaultValue=None
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.INITIAL_SEA_LEVEL,
            "Initial Sea level in meters",
            QgsProcessingParameterNumber.Double,
            defaultValue=1.0,
            minValue=0.0
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.SEA_LEVEL_INCREMENT,
            "Sea level increments in meters",
            QgsProcessingParameterNumber.Double,
            defaultValue=0.2,
            minValue=0.0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.NUMBER_ITERATIONS,
            "Number of iterations",
            QgsProcessingParameterNumber.Integer,
            defaultValue=16,
            minValue=1
        ))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_WORKSPACE,
            "Output Workspace"
        ))
    
    def processAlgorithm(self, parameters, context, feedback):
        try:
            dtm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DTM, context)
            sea_line_layer = self.parameterAsVectorLayer(parameters, self.INPUT_SEA_LINE, context)
            initial_sea_level = self.parameterAsDouble(parameters, self.INITIAL_SEA_LEVEL, context)
            sea_level_increment = self.parameterAsDouble(parameters, self.SEA_LEVEL_INCREMENT, context)
            number_iterations = self.parameterAsInt(parameters, self.NUMBER_ITERATIONS, context)
            output_workspace = self.parameterAsString(parameters, self.OUTPUT_WORKSPACE, context)

            if not dtm_layer or not dtm_layer.isValid():
                raise QgsProcessingException("Invalid DTM raster")
            
            if not sea_line_layer or not sea_line_layer.isValid():
                raise QgsProcessingException("Invalid Line at Sea Layer")
            
            if not output_workspace:
                raise QgsProcessingException("Invalid output workspace")
            
            feedback.pushInfo(f"DTM Layer: {dtm_layer.source()}")
            feedback.pushInfo(f"Sea Line Layer: {sea_line_layer.source()}")
            feedback.pushInfo(f"Output Workspace: {output_workspace}")
            feedback.pushInfo(f"Initial Sea Level: {initial_sea_level}m")
            feedback.pushInfo(f"Sea Level Increment: {sea_level_increment}m")
            feedback.pushInfo(f"Number of Iterations: {number_iterations}")

            result = create_inundation(
                input_dtm_raster=dtm_layer,
                line_at_sea=sea_line_layer,
                initial_sea_level_meters=initial_sea_level,
                sea_level_increment_meters=sea_level_increment,
                number_of_iterations=number_iterations,
                output_folder=output_workspace,
                context=context,
                feedback=feedback
            )

            return result
        
        except Exception as e:
            feedback.reportError(f"Algorithm failed: {str(e)}")
            raise QgsProcessingException(f"Failure in execution: {str(e)}")
    
    def name(self):
        return "createinundation"
    
    def displayName(self):
        return "Create Inundation"
    
    def group(self):
        return "Hydrology"
    
    def groupId(self):
        return "hydrology"
    
    def createInstance(self):
        return InundationAlgorithm()



