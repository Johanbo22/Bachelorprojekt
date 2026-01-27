import arcpy

with arcpy.da.SearchCursor(fc, ["SHAPE@"]) as cur:
  for row in cur:
    geom = row[0]
    for part in geom:
      for p in part:
        print(p.X, p.Y)
