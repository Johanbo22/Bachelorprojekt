import arcpy
from arcpy import env
from arcpy.sa import *
import os

arcpy.env.overwriteOutput = True

arcpy.CheckOutExtension("spatial")

#Aget params
input_buildings = arcpy.GetParameterAsText(0)
mask = arcpy.GetParameterAsText(1)
dhym_input = arcpy.GetParameterAsText(2)
output_workspace = arcpy.GetParameterAsText(3)

building_height = arcpy.GetParameterAsText(4)
if building_height == "" or building_height == "#":
    building_height = 20
else:
    building_height = float(building_height)

cell_size = arcpy.GetParameterAsText(5)
if cell_size == "" or cell_size == "#":
    cell_size = 0.4
else:
    cell_size = float(cell_size)

delete_intermediate = arcpy.GetParameterAsText(6)
if delete_intermediate == "" or delete_intermediate == "#" or delete_intermediate.upper() == "TRUE":
    delete_intermediate = True
else:
    delete_intermediate = False

#set worksapce
arcpy.env.workspace = output_workspace

#define fc names
OutputDHyMName = "DHyMBuildings"
ClippedBuildingsName = "Buildings_Clipped"
BuildingPolyRasterName = "BuildingPolyRaster"
BuildingRasterName = "BuildingRaster"

arcpy.AddMessage("Process of burning building footprints into DHyM has started")
describ = arcpy.Describe(input_buildings).dataType
arcpy.AddMessage(f"\nInput building is of type: {describ}")


arcpy.AddMessage("Clipping biuildings to mask extent")
clipped_buildings = os.path.join(output_workspace, ClippedBuildingsName)

try:
    arcpy.analysis.Clip(
        in_features=input_buildings,
        clip_features=mask,
        out_feature_class=clipped_buildings
    )
    result = arcpy.GetCount_management(clipped_buildings)
    count = int(result.getOutput(0))
    arcpy.AddMessage(f"{count} buildings in mask")

except Exception as e:
    arcpy.AddError(f"Error clipping features in mask: {str(e)}")
    raise

arcpy.AddMessage(f"\nSetting building height to polygons: Height: {building_height} ")

try:
    field_names = [field.name for field in arcpy.ListFields(clipped_buildings)]
    if "Elevation" not in field_names:
        arcpy.AddField_management(clipped_buildings, "Elevation", "DOUBLE")
        arcpy.AddMessage(" 'Eleveation' was added")
    
    arcpy.CalculateField_management(
        in_table=clipped_buildings,
        field="Elevation",
        expression=building_height
    )
    arcpy.AddMessage("Field calcualted")

except Exception as e:
    arcpy.AddError(f"\nError calculating field: {str(e)}")
    raise

#poly to raster
arcpy.AddMessage(f"\nConverting building polygons to raster with cellsize: {cell_size}m")
building_poly_raster = os.path.join(output_workspace, BuildingPolyRasterName)

try:
    arcpy.conversion.PolygonToRaster(
        in_features=clipped_buildings,
        value_field="Elevation",
        out_rasterdataset=building_poly_raster,
        cellsize=cell_size
    )
    arcpy.AddMessage("Polygons converted to raster format")

except Exception as e:
    arcpy.AddError(f"Failed to convert polygons to raster: {str(e)}")
    raise

arcpy.AddMessage("\nEliminating NODTA from buildingraster")
building_raster = os.path.join(output_workspace, BuildingRasterName)

try:
    building_raster_obj = Con(IsNull(building_poly_raster), 0, building_height)
    building_raster_obj.save(building_raster)
    arcpy.AddMessage("BuildingRaster with Nodata values == 0")

except Exception as e:
    arcpy.AddError(f"Error processing the raster: {str(e)}")

arcpy.AddMessage("\nCombining building raster with DHYM")
output_dtm = os.path.join(output_workspace, OutputDHyMName)

try:
    dtm_buildings = Raster(building_raster) + Raster(dhym_input)
    dtm_buildings.save(output_dtm)
    arcpy.AddMessage("DTM and building raster combined")

    describ_raster = arcpy.Describe(output_dtm)
    arcpy.AddMessage(f"Output raster extent: {describ_raster.extent}")
    arcpy.AddMessage(f"Output cell size: {round(describ_raster.meanCellWidth, 3)} x {round(describ_raster.meanCellHeight, 3)}")

except Exception as e:
    arcpy.AddError(f"Error combinging rasters: {str(e)}")
    raise

if delete_intermediate:
    arcpy.AddMessage("deleting random data")
    intermediate_data = [clipped_buildings, building_poly_raster, building_raster]
    deleted_count = 0

    for data in intermediate_data:
        if arcpy.Exists(data):
            try:
                arcpy.Delete_management(data)
                arcpy.AddMessage(f"Deleted: {os.path.basename(data)}")
                deleted_count += 1
            except Exception as e:
                arcpy.AddWarning(f"not able to delete: {os.path.basename(data)} due to: {str(e)}")
    
    arcpy.AddMessage(f"{deleted_count} datasets deleted")
else:
    arcpy.AddMessage(f"Temporay datasets not removed")

arcpy.AddMessage("\n==0")
arcpy.AddMessage("Process Complete")
arcpy.AddMessage(f"Ouput save to: {output_workspace}'\'{OutputDHyMName}")

arcpy.CheckInExtension("spatial")
arcpy.SetParameterAsText(7, output_dtm)
