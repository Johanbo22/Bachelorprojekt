'''
Name:       Convert Horseshoe Adaptation to Lines
Purpose:    Used to convert horseshoe shaped hydrological adaptation to singular lines for stamping onto a DTM


Author:     Johan Bo Kjær (based on ArcPy script-tool from Thomas Balstrøm 2019)   



'''


import os, os.path, math, processing
from qgis.core import(QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsFeature, QgsGeometry,
    QgsVectorFileWriter, QgsFields, QgsField,
    QgsProcessingFeedback, QgsWkbTypes, QgsPointXY
)
from qgis.core import QgsProcessingAlgorithm, QgsProcessingParameterVectorLayer, QgsProcessingParameterRasterLayer, QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingException
from PyQt5.QtCore import QVariant

def convert_horseshoes_to_lines(horseshoes_path, dhm_path, output_workspace, feedback=None):
    
    if feedback is None:
        feedback = QgsProcessingFeedback()

    feedback.pushInfo("Converting horsehoes to lines")

    # create workspace if not already
    os.makedirs(output_workspace, exist_ok=True)

    # load data
    try:
        horseshoes_layer = QgsVectorLayer(horseshoes_path, "horseshoes", "ogr")
        if not horseshoes_layer.isValid():
            raise Exception(f"Failed to load horseshoe layer: {horseshoes_path}")

        dhm_layer = QgsRasterLayer(dhm_path, "dhm")
        if not dhm_layer.isValid():
            raise Exception(f"Failed to load DHM: {dhm_path}")
    
    except Exception as error:
        if feedback:
            feedback.reportError(f"Error loading input layers: {str(error)}")
        return None
    
    # get the DHM cell size
    dhm_provider = dhm_layer.dataProvider()
    dhm_extent = dhm_provider.extent()
    cell_size_x = dhm_extent.width() / dhm_layer.width()
    cell_size_y = dhm_extent.height() / dhm_layer.height()
    cell_size = min(cell_size_x, cell_size_y)

    feedback.pushInfo(f"DHM cellsize is {round(cell_size, 2)} units. Linespacing is {round(cell_size * 0.7, 2)} units")

    # create output feature 
    output_line_name = "HorseshoeLines.shp"
    output_path = os.path.join(output_workspace, output_line_name)

    # remove if an output already exists
    if os.path.exists(output_path):
        # remove the existing shapefiles
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qpj']:
            file_with_ext = output_path.replace('.shp', ext)
            if os.path.exists(file_with_ext):
                os.remove(file_with_ext)
    
    # get coordinates
    crs = horseshoes_layer.crs()

    # create fielsd in new output layer
    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))

    writer = QgsVectorFileWriter(output_path, "UTF-8", fields, QgsWkbTypes.LineString, crs, "ESRI Shapefile")

    if writer.hasError() != QgsVectorFileWriter.NoError:
        feedback.reportError(f"Error creating output file: {writer.errorMessage}")
        return None
    
    # TB has problematic verticies included in his script. I keep these just in case theyre importantn. 
    count = 0
    problematic_geometries = []

    feedback.pushInfo("Processing the horsesoelayer")

    for feature in horseshoes_layer.getFeatures():
        geom = feature.geometry()

        if not geom or geom.isEmpty():
            continue

        if geom.type() != QgsWkbTypes.LineGeometry:
            feedback.pushInfo(f"Feature {feature.id()} is not a polygon, skipping htat feature")
            continue

        polygon = geom.asMultiPolyline()

        if not polygon:
            continue

        for ring in polygon:
            num_vertices = len(ring)

            # check for more than 4 vertices (the problem)
            if num_vertices > 4:
                feedback.pushInfo(f"feature: {feature.id()} has more than 4 vertices. saved for later")
                problematic_geometries.append(geom)
                continue

            if num_vertices < 4:
                feedback.pushInfo(f"Feature {feature.id()} has less than 4 vertices, skipping that feature")
                continue

            # extract corners
            xy = []
            for i in range(4):
                point = ring[i]
                xy.append((point.x(), point.y()))
            
            # calculate distances to determine line spacing
            dist03 = math.sqrt((xy[0][0] - xy[3][0])**2 + (xy[0][1] - xy[3][1])**2)
            dist12 = math.sqrt((xy[1][0] - xy[2][0])**2 + (xy[1][1] - xy[2][1])**2)
            max_dist = max(dist03, dist12)

            # lines to create between horseshoe opening
            max_line_distance = round(max_dist / (cell_size * 0.7)) + 1

            # create the lines
            for i in range(max_line_distance):
                x1 = xy[0][0] + (xy[3][0] - xy[0][0]) / max_line_distance * i
                y1 = xy[0][1] + (xy[3][1] - xy[0][1]) / max_line_distance * i
                x2 = xy[1][0] + (xy[2][0] - xy[1][0]) / max_line_distance * i
                y2 = xy[1][1] + (xy[2][1] - xy[1][1]) / max_line_distance * i

                line_points = [QgsPointXY(x1, y1), QgsPointXY(x2, y2)]
                line_geom = QgsGeometry.fromPolylineXY(line_points)

                # create and write new featuer
                out_feature = QgsFeature()
                out_feature.setGeometry(line_geom)
                out_feature.setAttributes([count])

                writer.addFeature(out_feature)
                count += 1
    
    first_count = count
    feedback.pushInfo(f"No. of line features created: {first_count}")

    # problematic vertices handling.
    if problematic_geometries:
        feedback.pushInfo("Handling the problematic vertices")

        # create a temporay layer
        temp_problematic_path = os.path.join(output_workspace, "temp_problematic.shp")

        # create
        temp_writer = QgsVectorFileWriter(temp_problematic_path, "UTF-8", horseshoes_layer.fields(), QgsWkbTypes.Polygon, crs, "ESRI Shapefile")

        # add the problematic features to this new layer?
        for i, geom in enumerate(problematic_geometries):
            temp_feature = QgsFeature()
            temp_feature.setGeometry(geom)
            temp_feature.setAttributes([i] + [None] * (horseshoes_layer.fields().count() - 1)) # this is really jank
            temp_writer.addFeature(temp_feature)
        
        del temp_writer # remove the writer

        # load new temporary layer
        temp_layer = QgsVectorLayer(temp_problematic_path, "temp_problematic", "ogr")

        if temp_layer.isValid():
            simplified_path = os.path.join(output_workspace, "temp_simplified.shp")

            try:
                processing.run("native:simplifygeometries", {
                    'INPUT': temp_layer,
                    'METHOD': 0,
                    'TOLERANCE': cell_size,
                    'OUTPUT': simplified_path
                })

                simplified_layer = QgsVectorLayer(simplified_path, "simplified", "ogr")

                if simplified_layer.isValid():
                    # prcess.
                    for feature in simplified_layer.getFeatures():
                        geom = feature.geometry()

                        if not geom or geom.isEmpty():
                            continue

                        if geom.type() != QgsWkbTypes.LineGeometry:
                            continue

                        polygon = geom.asMultiPolyline()

                        for ring in polygon:
                            num_vertices = len(ring)

                            if num_vertices > 4:
                                feedback.pushInfo(f"Simplified horseshoe: {feature.id()} still has more than 4 vertices. Correct the shape manually and rerun")
                                continue

                            if num_vertices < 4:
                                feedback.pushInfo(f"Simplified horseshoe {feature.id()} has less than 4 vertices. HMMMMMMMMMM?????")
                                continue
                            
                            # extracting points and creating the lnies
                            xy = []
                            for i in range(4):
                                point = ring[i]
                                xy.append((point.x(), point.y()))

                            dist03 = math.sqrt((xy[0][0] - xy[3][0])**2 + (xy[0][1] - xy[3][1])**2)
                            dist12 = math.sqrt((xy[1][0] - xy[2][0])**2 + (xy[1][1] - xy[2][1])**2)
                            max_dist = max(dist03, dist12)
                            max_line_distance = round(max_dist / (cell_size * 0.7)) + 1

                            for i in range(max_line_distance):
                                x1 = xy[0][0] + (xy[3][0] - xy[0][0]) / max_line_distance * i
                                y1 = xy[0][1] + (xy[3][1] - xy[0][1]) / max_line_distance * i
                                x2 = xy[1][0] + (xy[2][0] - xy[1][0]) / max_line_distance * i
                                y2 = xy[1][1] + (xy[2][1] - xy[1][1]) / max_line_distance * i

                                line_points = [QgsPointXY(x1, y1), QgsPointXY(x2, y2)]
                                line_geom = QgsGeometry.fromPolylineXY(line_points)

                                out_feature = QgsFeature()
                                out_feature.setGeometry(line_geom)
                                out_feature.setAttributes([count])

                                writer.addFeature(out_feature)
                                count += 1
                
                # clean up the temporary fles
                for temp_file in [temp_problematic_path, simplified_path]:
                    if os.path.exists(temp_file):
                        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qpj']:
                            file_with_ext = temp_file.replace('.shp', ext)
                            if os.path.exists(file_with_ext):
                                try:
                                    os.remove(file_with_ext)
                                except:
                                    pass
            
            except Exception as error:
                feedback.pushInfo(f"Error handlin the problematic horseshoes: {str(error)}")
    
    del writer

    feedback.pushInfo(f"No. of line features created in second round: {count - first_count}")
    feedback.pushInfo(f"Total no of lines created: {count} with a spacing of {round(cell_size * 0.7, 2)} units")
    feedback.pushInfo(f"Done. Lines create from the horseshoes have been saved to: {output_path}")

    return output_path

def run():
    horseshoes_path = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\output\HorseshoesAdaptations.shp"
    dhm_path = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\training data\dtm\aabenraa_dhm_clipped.tif"
    output_workspace = r"C:\Users\joha4\OneDrive\Skrivebord_LapTop\Bsc_artikel\qgis_translated_scripts_tb\output"

    try:
        result_path = convert_horseshoes_to_lines(horseshoes_path=horseshoes_path, dhm_path=dhm_path, output_workspace=output_workspace)

        if result_path:
            print(f"Horseshoes to lines converted d")
            print(f"Result has been saved to {result_path}")

            # load the new data into current project
            result_layer = QgsVectorLayer(result_path, "HorseshoeLines", "ogr")
            if result_layer.isValid():
                QgsProject.instance().addMapLayer(result_layer)
                print("Result added to current map")
            else:
                print("Warning. could not load into current projectr")
        else:
            print("Error: no files created")
    
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

class HorseshoeToLinesAlgorithm(QgsProcessingAlgorithm):
    # this is the class for calling the algorithm in the QGIS desktop GUI environment.
  
    INPUT_HORSESHOES = 'INPUT_HORSESHOES'
    INPUT_DHM = 'INPUT_DHM'
    OUTPUT_WORKSPACE = 'OUTPUT_WORKSPACE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_HORSESHOES, "Horseshoes Featuers", [QgsWkbTypes.LineGeometry]
        ))

        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_DHM, "DHM Raster"))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUTPUT_WORKSPACE, "Output Workspace"))
    
    def processAlgorithm(self, parameters, context, feedback):
        horseshoes_layer = self.parameterAsVectorLayer(parameters, self.INPUT_HORSESHOES, context)
        dhm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DHM, context)
        output_workspace = self.parameterAsString(parameters, self.OUTPUT_WORKSPACE, context)

        if not horseshoes_layer or not dhm_layer or not output_workspace:
            raise QgsProcessingException("Invalid input parameters")
        
        result_path = convert_horseshoes_to_lines(horseshoes_path=horseshoes_layer.source(), dhm_path=dhm_layer.source(), output_workspace=output_workspace, feedback=feedback)

        if result_path:
            project = QgsProject.instance()
            
            path = result_path
            name = "HorseshoeLines"
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
        return "horseshoes to lines"
    
    def displayName(self):
        return "Create lines from horseshoe shaped adaptations"
    
    def group(self):
        return "Hydrology"
    
    def groupId(self):
        return "hydrology"
    
    def createInstance(self):
        return HorseshoeToLinesAlgorithm()
