#__________________________________________________________________________________________________
# DOCUMENTATION:
# NAME: QGIS Vector Tracing Tool
# DESCRIPTION: Extracts a line segment between one or two points. Uses a general index based approach 
#              to define tracing directions. Supports Polyline and Polygon features as input
# AUTHOR: Johan Bo Kjær
# LAST EDITED: 2026-02-23
# REFERENCES TO QGIS PYTHON API: 
# core module: https://qgis.org/pyqgis/3.40/core/index.html, 
# utils module: https://qgis.org/pyqgis/3.40/gui/QgisInterface.html
# 
# PYTHON OS module: https://docs.python.org/3/library/os.html
# TESTED ON: QGIS v3.36.3 and QGIS v3.40.15
#__________________________________________________________________________________________________

from qgis.core import QgsProject, QgsGeometry, QgsPointXY,QgsFeature, QgsVectorLayer, QgsCoordinateTransform, QgsRectangle, QgsWkbTypes, Qgis,QgsVectorFileWriter, QgsUnitTypes
from qgis.utils import iface
import os

# Config
# Setup of layer names
# Names must match layer name in current map/folder
# Just copy from mapNames

# TARGET_LAYER_NAME is the feature that needs to be traced
# can be off polygon or multipolylinestring feature 
TARGET_LAYER_NAME = "kystlinje"   

# START_POINT_LAYER is the name of the initial starting point
# this is a pointXY feature
START_POINT_LAYER = "trace_start"     

# END_POINT_LAYER is the name of the end point for the calc
# this is pointXY feature.
# if set to None or empty string, the tool will calculate from
# start point to end vertex for lines and loop back to the start point  if polygon
END_POINT_LAYER = "trace_end"    

# OUTPUT_FILE_PATH is the path to where the result is stored
# can be in the formats: .gpkg, .shp or .geojson
OUTPUT_FILE = r"C:\Users\joha4\Desktop\test_folder\tracetest.gpkg" 

# OUTPUT_LAYER_NAME is the name of feature as it appears in the map
# this is also the name of the table in the gpkg if that format is chosen
OUTPUT_LAYER_NAME = "Traced_Feature4" 

# POLYGON_TRACE_MODE is a bool for determining the direction of calc
# This is only used when the TARGET_LAYER_NAME is of type Polygon
# "Shortest" means the shortest distance between end and start point
# "Longest" means the longest distance between end and start point
POLYGON_TRACE_MODE = "Shortest" 

# If no end point is given, TRACE_DIRECTION sets which direction the calculation should go
# "Backwards" is going down the vertex indicies ex 6 to 5 to 4 etc
# "Forwards" is going up the vertex indicies ex 4 to 5 to 6 etc
DEFAULT_TRACE_DIRECTION = "Forward"

def log_msg(title, text, level=Qgis.Info):
    print(f"[{title}] {text}")
    iface.messageBar().pushMessage(title, text, level=level, duration=5)

def vector_trace():
    try:
        log_msg("Tracing started", f"Extracting to {os.path.basename(OUTPUT_FILE)}...", Qgis.Info)
        print("hehheheheheh")
        
        # has end point been given or empty stringg
        has_end_point = END_POINT_LAYER is not None and END_POINT_LAYER != ""
        
        # Setup and fetch layers from the map
        target_layer = QgsProject.instance().mapLayersByName(TARGET_LAYER_NAME)[0]
        start_layer = QgsProject.instance().mapLayersByName(START_POINT_LAYER)[0]
        # grabs crs from layer to be traced
        dest_crs = target_layer.crs()
        
        # grab map units for output
        map_unit_str = QgsUnitTypes.toString(dest_crs.mapUnits())
        if not map_unit_str or map_unit_str.lower() == "unknown":
            map_unit_str = "units" 
        
        # transform points crs to target_crs and convert them to
        # pointxy if not already a pointxy feature
        xform_start = QgsCoordinateTransform(start_layer.crs(), dest_crs, QgsProject.instance())
        start_pt_xy = xform_start.transform(QgsPointXY(next(start_layer.getFeatures()).geometry().asPoint()))
        
        end_pt_xy = None
        if has_end_point:
            end_layer = QgsProject.instance().mapLayersByName(END_POINT_LAYER)[0]
            xform_end = QgsCoordinateTransform(end_layer.crs(), dest_crs, QgsProject.instance())
            end_pt_xy = xform_end.transform(QgsPointXY(next(end_layer.getFeatures()).geometry().asPoint()))

        # We do a search box to find features
        # near start and end point
        # using bbox
        from qgis.core import QgsFeatureRequest
        request = QgsFeatureRequest()
        
        if has_end_point:
            bbox = QgsRectangle(start_pt_xy, end_pt_xy)
            bbox.grow(bbox.width() * 0.5) 
            request.setFilterRect(bbox)
        else:
            # If no end point
            # fetch features near the start point
            # to avoid processing whole map
            # by 10km radius bbox
            bbox = QgsRectangle(start_pt_xy, start_pt_xy)
            bbox.grow(10000)
            request.setFilterRect(bbox)
        
        print("Normalising vector segments of multiline/multipolygon strings into single geometry thingie")
        print("ding")
        geometries = []
        for f in target_layer.getFeatures(request):
            # Get the features geometry
            geom = f.geometry()
            # If geometry is a polygon
            # we convert into separate lines
            if geom.type() == QgsWkbTypes.PolygonGeometry:
                rings = []
                # check for multipart polygons
                if geom.isMultipart():
                    # For each polygon part extract the boundary
                    # and convert it to a polyline
                    for poly in geom.asMultiPolygon():
                        for ring in poly: rings.append(QgsGeometry.fromPolylineXY(ring))
                # else a single polygon, extract boundary
                # and convert to polyline
                else:
                    for ring in geom.asPolygon(): rings.append(QgsGeometry.fromPolylineXY(ring))
                if rings: geom = QgsGeometry.collectGeometry(rings)
            geometries.append(geom)
        # if no geometry is near start point
        # raise exception 
        # otherwise we combine them into one feature
        if not geometries:
            raise Exception("No features found near start point")

        combined_geom = QgsGeometry.unaryUnion(geometries)
        merged_geom = combined_geom.mergeLines()
        
        # isolation of the wanted line
        target_line = None
        target_nodes = []
        # Turn the merged line feature into 
        # one or more polylines
        # as some of them could still be multilinestrings
        candidate_lines = merged_geom.asMultiPolyline() if QgsWkbTypes.isMultiType(merged_geom.wkbType()) else [merged_geom.asPolyline()]
            
        for line_pts in candidate_lines:
            # create a temp geometry layer from the lines points
            temp_geom = QgsGeometry.fromPolylineXY(line_pts)
            #Measure the distance to the start point
            #closestSegmentWithContext [https://api.qgis.org/api/classQgsGeometry.html#a068daf775571b13b26837798b6eeae1a] ; Searches for the closest segment of geometry to the given point.
            dist_start = temp_geom.closestSegmentWithContext(start_pt_xy)[0]
            # if an end point is given
            # measure the distance to the line as well
            if has_end_point:
                dist_end = temp_geom.closestSegmentWithContext(end_pt_xy)[0]
                # if both end and start point lie close to same featureID 
                # we have found the line
                if dist_start < 2500 and dist_end < 2500:
                    target_line = temp_geom
                    target_nodes = line_pts
                    break
            else:
                ## only care about the start points distance
                # pick the line that is closest
                if dist_start < 2500:
                    target_line = temp_geom
                    target_nodes = line_pts
                    break
        
        if not target_line:
            raise Exception("Could not identify a path.")

        # Do some snapping
        # if point not on line
        print("oh snap snap")
        res_start = target_line.closestSegmentWithContext(start_pt_xy)
        snap_start, idx_start = res_start[1], res_start[2]
        
        snap_end, idx_end = None, -1
        if has_end_point:
            res_end = target_line.closestSegmentWithContext(end_pt_xy)
            snap_end, idx_end = res_end[1], res_end[2]

        # Define variable for is_closed or not
        #big number to encapsulate all nodes possible
        is_closed = target_nodes[0].sqrDist(target_nodes[-1]) < 1e-6

        def build_trace(direction):
            path = [snap_start]
            # Nodes is the last node if a closed loop else all nodes in target
            nodes = target_nodes[:-1] if is_closed else target_nodes
            N = len(nodes)
            
            if direction == "Forward":
                # get current index and target index based on trace type
                # and if has_end_point
                curr = idx_start % N if is_closed else idx_start
                target = idx_end % N if (is_closed and has_end_point) else (idx_end if has_end_point else -1)
                
                for _ in range(N + 2):
                    if has_end_point and curr == target:
                        path.append(snap_end)
                        break
                    #if there is no end point
                    # close the loop at start point
                    if not has_end_point and is_closed and len(path) > 1 and curr == (idx_start % N):
                        path.append(snap_start)
                        break
                    # if there is no end point and
                    # line is not a closed loop
                    # and break when reaching end of line
                    if not is_closed and curr >= N: 
                        break
                        
                    path.append(nodes[curr])
                    # get next index
                    curr = (curr + 1) % N if is_closed else curr + 1
            else: # Backward direction
                curr = (idx_start - 1) % N if is_closed else idx_start - 1
                stop_node = -1
                if has_end_point:
                    target = idx_end % N if is_closed else idx_end
                    stop_node = (target - 1) % N if is_closed else target - 1
                
                for _ in range(N + 2):
                    if has_end_point and curr == stop_node:
                        path.append(snap_end)
                        break
                    
                    if not has_end_point and is_closed and len(path) > 1 and curr == ((idx_start - 1) % N):
                        path.append(snap_start)
                        break
                        
                    if not is_closed and curr < 0: 
                        break
                        
                    path.append(nodes[curr])
                    curr = (curr - 1) % N if is_closed else curr - 1
            return path

        # If and and end point and a start point
        # is given determine the direction based
        # on index values
        if not is_closed:
            if has_end_point:
                if idx_end > idx_start: val_dir = "Forward"
                elif idx_end < idx_start: val_dir = "Backward"
                else:
                    v_prev = target_nodes[idx_start - 1]
                    val_dir = "Forward" if v_prev.sqrDist(snap_end) >= v_prev.sqrDist(snap_start) else "Backward"
            else:
                # no end point given
                # here can assume a polygon shape
                val_dir = DEFAULT_TRACE_DIRECTION
                
            path = build_trace(val_dir)
            print(f"Tracing along with direction: {val_dir} for open polyline")
        else:
            if has_end_point:
                path_fwd = build_trace("Forward")
                path_bwd = build_trace("Backward")
                
                if POLYGON_TRACE_MODE == "Forward": 
                    path = path_fwd
                elif POLYGON_TRACE_MODE == "Backward": 
                    path = path_bwd
                else:
                    # get length of both path optios
                    len_fwd = QgsGeometry.fromPolylineXY(path_fwd).length()
                    len_bwd = QgsGeometry.fromPolylineXY(path_bwd).length()
                    # determine path from trace mode
                    # this is done when there is_closed and has_end_point
                    # essentially a polygon or a closed-loop polyline?
                    path = path_fwd if (len_fwd <= len_bwd and POLYGON_TRACE_MODE == "Shortest") or (len_fwd > len_bwd and POLYGON_TRACE_MODE == "Longest") else path_bwd
                print("yoink")
                print(f"Tracing along a closed loop using: {POLYGON_TRACE_MODE}")
            else:
                # tracing a polygon with no end point
                # is an entire loop of polygon edge
                path = build_trace(DEFAULT_TRACE_DIRECTION)
                print("-> Closed loop geometry detected. No end point provided; extracting full loop.")

        # Creating new feature layer and setup attribute table
        print("ATTTTTRIBUUTTTEEEEEEE")
        uri = f"LineString?crs={dest_crs.authid()}&field=id:integer&field=shape_len:double"
        temp_layer = QgsVectorLayer(uri, "temp", "memory")
        pr = temp_layer.dataProvider()
        
        new_geom = QgsGeometry.fromPolylineXY(path)
        new_feat = QgsFeature(temp_layer.fields())
        new_feat.setGeometry(new_geom)
        
        # Get the length of the traced line
        # and paste it into the attribute field
        feature_length = new_geom.length()
        new_feat.setAttributes([1, feature_length]) 
        
        pr.addFeatures([new_feat])
        temp_layer.updateExtents()

        #Write to disk
        ext = os.path.splitext(OUTPUT_FILE)[1].lower()
        driver_map = {".gpkg": "GPKG", ".shp": "ESRI Shapefile", ".geojson": "GeoJSON"}
        
        #Raise exception if given file extension
        # is not vsalid
        if ext not in driver_map:
            raise Exception(f" output format {ext} no good.  use .gpkg, .shp, or .geojson.")

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driver_map[ext]
        options.layerName = OUTPUT_LAYER_NAME
        
        # check for existing files or same path
        # if exists and is gpkg overwrite layer in gpkg
        # if not gpkg overwrite file with new file
        if os.path.exists(OUTPUT_FILE):
            if ext == ".gpkg":
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer 
            else:
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        #transformContext stores information about datum transformations when transforming points from a source to a target CRS
        # https://qgis.org/pyqgis/3.40/core/QgsProject.html#qgis.core.QgsProject.transformContext
        save_result = QgsVectorFileWriter.writeAsVectorFormatV3(
            temp_layer, OUTPUT_FILE, QgsProject.instance().transformContext(), options
        )

        if save_result[0] != QgsVectorFileWriter.NoError:
            raise Exception(f"Failed to save vector file: {save_result[1]}")

        # smack the new layer back into map view
        print("return to sender")
        saved_layer_uri = f"{OUTPUT_FILE}|layername={OUTPUT_LAYER_NAME}" if ext == ".gpkg" else OUTPUT_FILE
        final_layer = QgsVectorLayer(saved_layer_uri, OUTPUT_LAYER_NAME, "ogr")
        
        if final_layer.isValid():
            QgsProject.instance().addMapLayer(final_layer)
            # zoom to it
            iface.mapCanvas().setExtent(new_geom.boundingBox())
            iface.mapCanvas().refresh()
            log_msg("Tracing complete", f"Traced {len(path)} vertices. Length: {feature_length:.2f} {map_unit_str}.", Qgis.Success)
        else:
            raise Exception("Tracing complete and saved to disk. but failed to load into curretn map")

    except Exception as rip:
        log_msg("Tracing failed", str(rip), Qgis.Critical)

# runnnnnn ittt
vector_trace()
