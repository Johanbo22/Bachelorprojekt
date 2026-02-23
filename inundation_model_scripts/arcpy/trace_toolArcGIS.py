#__________________________________________________________________________________________________
# DOCUMENTATION:
# NAME: ArcGIS Pro Vector Tracing Tool
# DESCRIPTION: Extracts a line segment between one or two points. Uses a general index based approach 
#              to define tracing directions. Supports Polyline and Polygon features as input for 
#              feature to be traced. Point features for start/end point inputs
#              Writes output to a GeoDatabase (.gdb)
# AUTHOR: Johan Bo Kjær
# LAST EDITED: 2026-02-24
# REFERENCES TO arcpy docs: https://pro.arcgis.com/en/pro-app/3.4/arcpy/main/arcgis-pro-arcpy-reference.htm
# 
# PYTHON OS module: https://docs.python.org/3/library/os.html
# PYTHON math module: https://docs.python.org/3/library/math.html#module-math
# TESTED ON: ArcGIS Pro v.3.6.0
#__________________________________________________________________________________________________

import arcpy
import os
import math

# Config
# Setup of layer names
# Names must match layer name in current map/folder
# Just copy from mapNames

# TARGET_LAYER_NAME is the feature that needs to be traced
# can be off polygon or polyline feature 
TARGET_LAYER = "main_landpolygon_10"   

# START_POINT_LAYER is the name of the initial starting point
# this is a type of point feature
START_POINT = "start_point_poly"      

# END_POINT_LAYER is the name of the end point for the calc
# this is a point feature.
# if set to None or empty string, the tool will calculate from
# start point to end vertex for lines and loop back to the start point  if polygon
END_POINT = "end_point_poly"          

# OUTPUT_FC is the path to the geodatabase to store the result
OUTPUT_FC = r"C:\Users\joha4\Desktop\test_folder\trace_test.gdb" 

# POLYGON_TRACE_MODE is a bool for determining the direction of calc
# This is only used when the TARGET_LAYER_NAME is of type Polygon
# "Shortest" means the shortest distance between end and start point
# "Longest" means the longest distance between end and start point
POLYGON_TRACE_MODE = "Longest" 

# If no end point is given, TRACE_DIRECTION sets which direction the calculation should go
# "Backwards" is going down the vertex indicies ex 6 to 5 to 4 etc
# "Forwards" is going up the vertex indicies ex 4 to 5 to 6 etc
DEFAULT_TRACE_DIRECTION = "Forward"

def merge_polylines(geom1, geom2, spatial_ref) -> arcpy.Polyline:
    """Merges two arcpy line geometries into a single multipart Polyline."""
    arr = arcpy.Array()
    if geom1 is not None:
        for part in geom1: arr.add(part)
    if geom2 is not None:
        for part in geom2: arr.add(part)
    return arcpy.Polyline(arr, spatial_ref)

def vector_trace() -> None:
    try:
        print(f"\n Tracing started.  Output workspace: {os.path.basename(OUTPUT_FC)}")
        
        # Basic environment settings updates
        # overwriteOutput set to True to allow iterations
        # addOutputsToMap is disabled here to avoid adding the in-memory fc used later. 
        # these fcs are deleted and would break upon adding to map
        arcpy.env.overwriteOutput = True 
        arcpy.env.outputMFlag = "Disabled"
        arcpy.env.outputZFlag = "Disabled"
        arcpy.env.addOutputsToMap = False 
        
        has_end_point = END_POINT is not None and END_POINT != ""
        
        #_make sure that the given workspace existss
        out_ws, out_name = os.path.split(OUTPUT_FC)
        if not arcpy.Exists(out_ws):
            raise Exception(f"The workspace {out_ws} does not exist.")
        
        # fetch spatial reference from the target polygon/polyline layer
        desc_target = arcpy.Describe(TARGET_LAYER)
        sr = desc_target.spatialReference
        
        # Get the coordinates of the point layers
        print("Extracting coordinates...")
        print("Badabing badadum")
        start_geom = [row[0] for row in arcpy.da.SearchCursor(START_POINT, ["SHAPE@"], spatial_reference=sr)][0]
        end_geom = None
        if has_end_point:
            end_geom = [row[0] for row in arcpy.da.SearchCursor(END_POINT, ["SHAPE@"], spatial_reference=sr)][0]

        # search through area near points to find feature
        # 
        print("Searcing for target feature...")
        # uses end point as distance before 
        # regular search radius
        if has_end_point:
            search_dist = f"{start_geom.distanceTo(end_geom) * 1.5} Meters"
        else:
            search_dist = "10000 Meters"
            
        arcpy.management.MakeFeatureLayer(TARGET_LAYER, "temp_filter_lyr")
        arcpy.management.SelectLayerByLocation("temp_filter_lyr", "WITHIN_A_DISTANCE", start_geom, search_dist)

        # get the geometry from the newly created layer
        # to determine ...
        filtered_geoms = []
        with arcpy.da.SearchCursor("temp_filter_lyr", ["SHAPE@"]) as cursor:
            for row in cursor:
                geom = row[0]
                if geom is not None:
                    if desc_target.shapeType == "Polygon":
                        filtered_geoms.append(geom.boundary())
                    else:
                        filtered_geoms.append(geom)

        if len(filtered_geoms) == 0:
            raise Exception("No target features found near the start point.")

        print("Combining multipart polylines...")
        # create a feature class in memory 
        # that combines split line features into one
        arcpy.management.CreateFeatureclass("memory", "mem_raw", "POLYLINE", spatial_reference=sr)
        with arcpy.da.InsertCursor(r"memory\mem_raw", ["SHAPE@"]) as icur:
            for g in filtered_geoms:
                icur.insertRow([g])
        
        # Combining using unsplitline 
        arcpy.management.UnsplitLine(r"memory\mem_raw", r"memory\mem_stitched")

        
        print("Finding target path...")
        target_line = None
        min_start_dist = float('inf')
        
        with arcpy.da.SearchCursor(r"memory\mem_stitched", ["SHAPE@"]) as cursor:
            for row in cursor:
                line = row[0]
                _, start_meas, start_dist, _ = line.queryPointAndDistance(start_geom)
                
                if has_end_point:
                    _, _, end_dist, _ = line.queryPointAndDistance(end_geom)
                    # if both end and start point lie close to same featureID 
                    # we have found the line
                    if start_dist < 2500 and end_dist < 2500:
                        target_line = line
                        break
                else:
                    ## only care about the start points distance
                    # pick the line that is closest
                    if start_dist < min_start_dist:
                        min_start_dist = start_dist
                        target_line = line

        if target_line is None:
            raise Exception("Could not isolate a continuous connected path. Are there physical gaps in the line?")

        # Calculate the distance
        print("Calculating routing...")
        total_length = target_line.length
        
        _, start_meas, _, _ = target_line.queryPointAndDistance(start_geom)
        start_pct = start_meas / total_length
        
        end_pct = -1
        if has_end_point:
            _, end_meas, _, _ = target_line.queryPointAndDistance(end_geom)
            end_pct = end_meas / total_length

        # Determine whether line is a closed loop
        # or has end vertex != start vertex
        # math.isclose finds determines the value of each point index and if they are the same or very close (1e-5) to each other. Assume its the same point
        # (1e-5) = 0.00001, should catch any floating point error in coordinates
        first_pt, last_pt = target_line.firstPoint, target_line.lastPoint
        is_closed = (math.isclose(first_pt.X, last_pt.X, abs_tol=1e-5) and math.isclose(first_pt.Y, last_pt.Y, abs_tol=1e-5))

        traced_geom = None

        # segment the line along verticies
        # helps determine final extracted feature
        # and if there are any mistakes 
        print("Extracting geometry...")
        if not is_closed:
            if has_end_point:
                # When start and end point are known 
                # get only sections between
                if start_pct <= end_pct:
                    traced_geom = target_line.segmentAlongLine(start_pct, end_pct, True)
                else:
                    traced_geom = target_line.segmentAlongLine(end_pct, start_pct, True)
            else:
                # if only start point is given
                # use trace direction to extract line
                if DEFAULT_TRACE_DIRECTION == "Forward":
                    traced_geom = target_line.segmentAlongLine(start_pct, 1.0, True)
                else:
                    traced_geom = target_line.segmentAlongLine(0.0, start_pct, True)
            print("   (open line extracted)")
            
        else:
            if has_end_point:
                # When a polygon or a closed loop line
                # two paths, 
                # compute both paths
                if end_pct >= start_pct:
                    fwd_geom = target_line.segmentAlongLine(start_pct, end_pct, True)
                    g1 = target_line.segmentAlongLine(end_pct, 1.0, True)
                    g2 = target_line.segmentAlongLine(0.0, start_pct, True)
                    bwd_geom = merge_polylines(g1, g2, sr)
                else:
                    g1 = target_line.segmentAlongLine(start_pct, 1.0, True)
                    g2 = target_line.segmentAlongLine(0.0, end_pct, True)
                    fwd_geom = merge_polylines(g1, g2, sr)
                    bwd_geom = target_line.segmentAlongLine(end_pct, start_pct, True)
                
                # Determine the calculation
                if POLYGON_TRACE_MODE == "Shortest":
                    traced_geom = fwd_geom if fwd_geom.length <= bwd_geom.length else bwd_geom
                elif POLYGON_TRACE_MODE == "Longest":
                    traced_geom = fwd_geom if fwd_geom.length > bwd_geom.length else bwd_geom
                elif POLYGON_TRACE_MODE == "Forward":
                    traced_geom = fwd_geom
                else:
                    traced_geom = bwd_geom
                print(f"   (Closed loop extracted using {POLYGON_TRACE_MODE})")
            else:
                # if no end point is given
                # extract segment for entire line 
                traced_geom = target_line.segmentAlongLine(0.0, 1.0, True)
                print("   (Full closed loop extracted)")

        print("Writing output to Geodatabase...")
        
        # If the result is empty
        # avoid writing to gdb 
        if traced_geom is None or traced_geom.length == 0:
            raise Exception("The tracing returned an empty geometry.")

        # We can add to map now
        # avoids memory data being added to map
        arcpy.env.addOutputsToMap = True 
        arcpy.management.CopyFeatures([traced_geom], OUTPUT_FC)
        
        # add Shape_len to feature class and calculate the shape_length
        arcpy.management.AddField(OUTPUT_FC, "shape_len", "DOUBLE")
        arcpy.management.CalculateField(OUTPUT_FC, "shape_len", "!shape.length!", "PYTHON3")

        # get the map units from spatial ref if possible
        # if it is empty write units
        unit_str = sr.linearUnitName if sr.linearUnitName else "units"
        print(f"\n Tracing complete. Length: {traced_geom.length:.2f} {unit_str}.")

    except Exception as e:
        print(f"\nTrace Failed: {str(e)}")
        
    finally:
        # Do a bit of sunday cleaning
        # its important that the memory fc 
        # are removed
        # many iterations with different names
        # could lead to large RAM usage
        print("Removing background files...")
        arcpy.management.Delete("memory")
        # Delete temporary layer if it didnt get removed in mem
        if arcpy.Exists("temp_filter_lyr"):
            arcpy.management.Delete("temp_filter_lyr")
        # Toggle this again just to be on the safe side.
        arcpy.env.addOutputsToMap = True 
        print("bye bye")

vector_trace()
