'''
Name:       Extract Hydroconditioning Inundation in QGIS
Purpose:    Used to filter and clip the relevant hydrological 
            adaptations within a DTM layer. Used for inundation purposes
Author:     Johan Bo Kjær (based on tool from Thomas Balstrøm 2019)   


Bugs:       The function call at the end is sometimes not correctly allocated to memory in python console in QGIS. Usually it works when redoing it.
            Added functionality to use as a tool in QGIS desktop. Also fixed issue with getting data into the project.
'''

import os
import sys
import tempfile
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeatureRequest, QgsExpression, QgsProcessingFeedback, QgsWkbTypes)
import processing
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterVectorLayer, QgsProcessingParameterRasterLayer, QgsProcessingParameterFolderDestination, QgsProcessingParameterFeatureSink, QgsProcessingException

def extract_hydroconditioning_inundation(line_adaptations="", horseshoe_adaptations="", dtm_mask="", output_workspace="", feedback=None):

    if feedback is None:
        feedback = QgsProcessingFeedback()
    feedback.pushInfo("start extraction of features ")

    os.makedirs(output_workspace, exist_ok=True)

    #load data
    try:
        line_layer = QgsVectorLayer(line_adaptations, "line_adaptations", "ogr")
        if not line_layer.isValid(): # check if valid
            raise Exception(f"Failed to load line adaptation layer: {line_adaptations}")
        
        horseshoe_layer = QgsVectorLayer(horseshoe_adaptations, "horseshoe_adaptations", "ogr")
        if not horseshoe_layer.isValid():
            raise Exception(f"Failed to load horseshoe shaped adaptations: {horseshoe_adaptations}")
        
        mask_layer = QgsVectorLayer(dtm_mask, "dtm_mask", "ogr")
        if not mask_layer.isValid():
            raise Exception(f"Failed to load DTM mask layer: {dtm_mask}")
    
    except Exception as error:
        feedback.reportError(f"Error loading input layers: {str(error)}")
        return {}
    
    feedback.pushInfo("input layers loaded")

    outputs = {}

    try:
        #horseshoes
        feedback.pushInfo("Processsing Horseshoes")
        horseshoes_in_mask_path = os.path.join(output_workspace, "horseshoes_in_mask.shp")
        processing.run("native:selectbylocation", {
            'INPUT': horseshoe_layer,
            'PREDICATE': [0], # intersects
            'INTERSECT': mask_layer,
            'METHOD': 0 #creates a new selection
        })

        processing.run("native:saveselectedfeatures", {
            'INPUT': horseshoe_layer,
            'OUTPUT': horseshoes_in_mask_path
        })

        horseshoes_in_mask = QgsVectorLayer(horseshoes_in_mask_path, "horseshoes_in_mask", "ogr")

        # filter for inundation purposes
        feedback.pushInfo("Filtering the horsehoes adaptations for uses in Inundation")
        
        # expression
        horseshoe_expression = QgsExpression("\"brugesher\" = 'Generel' OR \"brugesher\" = 'Havstigning'")
        horseshoes_request = QgsFeatureRequest(horseshoe_expression)

        horseshoe_count = sum(1 for _ in horseshoes_in_mask.getFeatures(horseshoes_request))

        if horseshoe_count > 0:
            feedback.pushInfo(f"Found {horseshoe_count} horseshoe shaped features ")

            #create output
            horseshoe_adaptations_path = os.path.join(output_workspace, "HorseshoesAdaptations.shp")

            processing.run("native:extractbyexpression", {
                'INPUT': horseshoes_in_mask,
                'EXPRESSION': "\"brugesher\" = 'Generel' OR \"brugesher\" = 'Havstigning'",
                'OUTPUT': horseshoe_adaptations_path
            })

            outputs['HorseshoesAdaptations'] = horseshoe_adaptations_path
            feedback.pushInfo("HorseshoesAdaptatons filtered and stored")
        else:
            feedback.pushInfo("No horseshoe adaptations in mask matching criteria")
        
        # line features
        feedback.pushInfo("Processing lines")

        lines_in_mask_path = os.path.join(output_workspace, "lines_in_mask.shp")
        processing.run("native:selectbylocation", {
            'INPUT': line_layer,
            'PREDICATE': [0],
            'INTERSECT': mask_layer,
            'METHOD': 0
        })

        processing.run("native:saveselectedfeatures", {
            'INPUT': line_layer,
            'OUTPUT': lines_in_mask_path
        })

        lines_in_mask = QgsVectorLayer(lines_in_mask_path, "lines_in_mask", "ogr")

        feedback.pushInfo("Filtering line adaptations for inundation purposes")

        line_expr1 = QgsExpression("\"brugesher\" = 'Generel' OR \"brugesher\" = 'Havstigning'")
        line_request1 = QgsFeatureRequest(line_expr1)
        line_count1 = sum(1 for _ in lines_in_mask.getFeatures(line_request1))

        if line_count1 > 0:
            feedback.pushInfo(f"Found {line_count1} line features")

            line_adaptations_path = os.path.join(output_workspace, "LineAdaptations.shp")

            processing.run("native:extractbyexpression", {
                'INPUT': lines_in_mask,
                'EXPRESSION': "\"brugesher\" = 'Generel' OR \"brugesher\" = 'Havstigning'",
                'OUTPUT': line_adaptations_path
            })

            outputs['LineAdaptations'] = line_adaptations_path
            feedback.pushInfo("LineAdaptations created")
        else:
            feedback.pushInfo("No line features found in mask matching criteria")
        
        #TB has this in the original modelbuilder view. i am preserving it because i am uncertain whether it is required for something else
        feedback.pushInfo("Filtering for DTM fix ")
        line_expr2 = QgsExpression("\"brugesHer\" = 'DHMfix'")
        line_request2 = QgsFeatureRequest(line_expr2)
        line_count2 = sum(1 for _ in lines_in_mask.getFeatures(line_request2))

        if line_count2 > 0:
            feedback.pushInfo(f"Found {line_count2} line features with Dhm fixes")

            dhm_fix_path = os.path.join(output_workspace, "DHMFixAdaptations.shp")

            processing.run("native:extractbyexpression", {
                'INPUT': lines_in_mask,
                'EXPRESSION': "\"brugesHer\" = 'DHMfix'",
                'OUTPUT': dhm_fix_path
            })

            outputs['DHMFixAdaptations'] = dhm_fix_path
            feedback.pushInfo("DHMFixAdaptations created")
        else:
            feedback.pushInfo("No line adaptations in mask matching DHM FIX")

        # clean temp files
        feedback.pushInfo("Clean up")
        temp_files = [horseshoes_in_mask_path, lines_in_mask_path]

        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    # remove shp file components
                    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', 'qpj']:
                        file_with_ext = temp_file.replace('.shp', ext)
                        if os.path.exists(file_with_ext):
                            os.remove(file_with_ext)
            except Exception as error:
                feedback.pushInfo(f"Warning: coudl not remove temporary fiel: {temp_file}: Issue: {str(error)}")
        
        feedback.pushInfo("Finished")
        return outputs
    
    except Exception as error:
        feedback.reportError(f"Error during processing: {str(error)}")
        return {}
    
def run_extract_hydroconditioning():
    # this is used if the script is run from the python console
    line_adaptations = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\adaptations\lines_all.shp"
    horseshoe_adaptations = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\adaptations\horseshoes_all.shp" 
    dtm_mask = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\adaptations\mask.shp"
    output_workspace = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\output"
    
    try:
        outputs = extract_hydroconditioning_inundation(
            line_adaptations=line_adaptations,
            horseshoe_adaptations=horseshoe_adaptations,
            dtm_mask=dtm_mask,
            output_workspace=output_workspace
        )
        
        if outputs:
            print("Hydroconditioning extraction completed")
            print("Output files created:")
            
            project = QgsProject.instance()
            
            for name, path in outputs.items():
                print(f"  - {name}: {path}")
                
                # Load layer into qgis project
                layer = QgsVectorLayer(path, name, "ogr")
                if layer.isValid():
                    project.addMapLayer(layer)
                    print(f"    Added {name} to QGIS project")
                else:
                    print(f"    Warning: Could not load {name} into QGIS")
        else:
            print("No output files were created")
            
    except Exception as e:
        print(f"Error during hydroconditioning extraction: {str(e)}")

class ExtractHydroconditioningAlgorithm(QgsProcessingAlgorithm):
    
    INPUT_LINES = 'INPUT_LINES'
    INPUT_HORSESHOES = 'INPUT_HORSESHOES'
    INPUT_DTM_MASK = 'INPUT_DTM_MASK'
    OUTPUT_WORKSPACE = 'OUTPUT_WORKSPACE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LINES, "Line Features", [QgsWkbTypes.LineGeometry]))

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_HORSESHOES, "Horseshoe shaped features", [QgsWkbTypes.LineGeometry]))

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_DTM_MASK, "DTM Masking Layer", [QgsWkbTypes.PolygonGeometry]))

        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_WORKSPACE, "Output Workspace"))
    
    def processAlgorithm(self, parameters, context, feedback):
        lines_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINES, context)
        horseshoe_layer = self.parameterAsVectorLayer(parameters, self.INPUT_HORSESHOES, context)
        dtm_mask_layer = self.parameterAsVectorLayer(parameters, self.INPUT_DTM_MASK, context)
        output_workspace = self.parameterAsString(parameters, self.OUTPUT_WORKSPACE, context)

        if not lines_layer or not horseshoe_layer or not dtm_mask_layer or not output_workspace:
            raise QgsProcessingException("Invalid input parameters")
        
        result_path = extract_hydroconditioning_inundation(line_adaptations=lines_layer.source(), horseshoe_adaptations=horseshoe_layer.source(), dtm_mask=dtm_mask_layer.source(), output_workspace=output_workspace, feedback=feedback)

        if result_path:
            project = QgsProject.instance()

            for name, path in result_path.items():
                print(f"  - {name}: {path}")
                
                # Load layer into qgis project
                layer = QgsVectorLayer(path, name, "ogr")
                if layer.isValid():
                    project.addMapLayer(layer)
                    print(f"    Added {name} to QGIS project")
                else:
                    print(f"    Warning: Could not load {name} into QGIS")
            return {self.OUTPUT: result_path}
            
        else:
            raise QgsProcessingException("Failed to create output")
    
    def name(self):
        return "extract hydroconditioning inundation"
    
    def displayName(self):
        return "Extracts hydroconditioning adaptations for inundation"
    
    def group(self):
        return "Hydrology"  

    def groupId(self):
        return "hydrology"
    
    def createInstance(self):
        return ExtractHydroconditioningAlgorithm()
