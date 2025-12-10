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

'''Print statements are for debugging'''

def create_inundation(input_dtm_raster, line_at_sea, initial_sea_level_meters, sea_level_increment_meters, number_of_iterations, output_folder):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    initial_cm = int(initial_sea_level_meters * 100)
    increment_cm = int(sea_level_increment_meters * 100)
    end_cm = initial_cm + ((number_of_iterations) - 1) * increment_cm

    print(f"Processing from {initial_cm}cm to {end_cm}cm with increment: {increment_cm}cm")

    for cm in range(initial_cm, end_cm + 1, increment_cm):
        print("Converting to meters again")
        m = cm / 100.0
        print("Converted")
        print(m)
        print(f"Processing: {m}meters ({cm}cm)")

        try:
            print("Creating setNull raster")
            temp_setnull = os.path.join(output_folder, f"Temp_SetNull_{cm}.tif")

            if hasattr(input_dtm_raster, "source"):
                dtm_layer = input_dtm_raster
            else:
                dtm_layer = QgsRasterLayer(input_dtm_raster, "dtm")

            expression = f'if("{dtm_layer.name()}@1" <= {m}, 1, 0/0)'
            print(f"Expression for the raster calculator is: {expression}")
            print(f"DTM LAYER NAME: {dtm_layer.name()}")

            print(f"Identifying cells that are below or equal to: {m}meters...")
            try:
                processing.run("native:rastercalc", {
                    'EXPRESSION': expression,
                    'LAYERS': [dtm_layer],
                    'OUTPUT': temp_setnull
                })
                print(f"Raster Calculation complete.\nIdentificaton of NoData for {m} meters has been completed")

            except Exception:
                print("Raster calculation failed")
                print(traceback.format_exc())

            print("Starting Distance Accumulation through cells")
            print("Creating temporary DA raster...")
            temp_da = os.path.join(output_folder, f"DA_{cm}.tif")
            print("Done")

            print("Getting source for LineAtSea layer...")

            if hasattr(line_at_sea, "source"):
                sea_line_layer = line_at_sea.source()
            else:
                sea_line_layer = QgsVectorLayer(line_at_sea, "LineAtSea", "ogr")
            print(f"Line at Sea Layer: {sea_line_layer.name()}")
            
            #validation of tempsetnull layer
            raster_layer = QgsRasterLayer(temp_setnull, "TempSetNull")
            if not raster_layer.isValid():
                raise ValueError("Raster is not valid")
            
            #check if raster layer is proper.
            stats = raster_layer.dataProvider().bandStatistics(1)
            print(f"Raster min/max: {stats.minimumValue} / {stats.maximumValue}") # should be 1/1

            try:
                print("Executing DA through cells, using the GRASS r.Cost algorithm...")
                extent = dtm_layer.extent()
                width_mu = extent.width()
                height_mu = extent.height()
                res_x = dtm_layer.rasterUnitsPerPixelX()
                res_y = dtm_layer.rasterUnitsPerPixelY()
                cells_x = width_mu / res_x
                cells_y = height_mu / res_y
                max_cost = int((cells_x**2 + cells_y**2)**0.5) + 10
                print(f"Max Cost: {max_cost}")

                result_DA = processing.run("grass7:r.cost", {
                    'input': temp_setnull,
                    'start_points': sea_line_layer,
                    'output': temp_da,
                    'max_cost': max_cost, # no limitation. need to change it so it is a variable of environment size to start point. 
                    'null_cost': -1, # treat NODATA values as impenetrable barriers
                    'memory': 500,
                    'flags': 'k'
                })
                print("Distance Accumulation completed")
                print(f"Result object: {result_DA}")
                # the result is also made from vertex[0] of the line, not the entire line. hmmm
                out_layer = QgsRasterLayer(result_DA['output'], "DA_Result")
                print(f"Is output layer valid: {out_layer.isValid()}")
            except Exception:
                print("Cost distance algorithm failed")
                print(traceback.format_exc())
            
            print("Creating Inundation rasters...")
            inundated = os.path.join(output_folder, f"Inundated_{cm}.tif")

            print("Combining result with sea level value...")

            # make the DA layer into a raster layer?
            temp_da_layer = QgsRasterLayer(temp_da, "temp_da")
            

            expression = f'("{temp_da_layer.name()}@1" >= 0) * {cm}'
            print(f"Expression for the combination is: {expression}")
            print(f"Raster layer anme is: {temp_da_layer.name()}")
            try:
                processing.run("native:rastercalc", {
                    'EXPRESSION': expression,
                    'LAYERS': [temp_da_layer],
                    'OUTPUT': inundated
                })
                print("Raster calculation complete")
                print(f"Inundated_{cm} completed")
            except Exception:
                print(f"Failed raster calculation")
                print(traceback.format_exc())

            print("Converting raster to polygons...")
            inundated_poly = os.path.join(output_folder, f"InundatedPoly_{cm}.gpkg")
            print(f"Converting...")

            try:
                #conversion tool
                processing.run("gdal:polygonize", {
                    'INPUT': inundated,
                    'BAND': 1,
                    'FIELD': 'value',
                    'EIGHT_CONNECTEDNESS': True,
                    'EXTRA': '',
                    'OUTPUT': inundated_poly
                })
                print("Conversion from raster to polygon completed")
            except Exception:
                print(f"Failed to convert raster to polygon")
                print(traceback.format_exc())

            #clean up
            print("Removing temporary files")
            try:
                if os.path.exists(temp_setnull):
                    os.remove(temp_setnull)
                    print("Temp feiles removed")
            except:
                print(f"Cannot remove temp files. Non necessary files are {temp_setnull}.\n Continuing...")
                pass



        except Exception as e:
            print(f"Error processing: {m} meters: {str(e)}")
    
    print("Process is complete")











### tests
def main():
    create_inundation(
        input_dtm_raster=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\output\DTM_with_hydro_adaptations.tif",
        line_at_sea=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\adaptations\LineAtSeaHesnaes.shp",
        initial_sea_level_meters=2.1,
        sea_level_increment_meters=0.2,
        number_of_iterations=1,
        output_folder=r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\inundation_output"
    )

if __name__ == "__main__":
    main()
