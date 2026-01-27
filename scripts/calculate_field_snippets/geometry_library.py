def geom_x(shape):
  return shape.centroid.X if shape else None

def geom_y(shape):
  return shape.centroid.Y if shape else None

def geom_area(shape):
  return shape.area if shape else None

def geom_length(shape):
  return shape.length if shape else None

def geom_type(shape):
  return shape.type if shape else None

def geom_part_count(shape):
  return shape.partCount if shape else None

def geom_vertex_count(shape):
  return sum(len(part) for part in shape) if shape else None

def buffer_area(shape, dist):
  return shape.buffer(dist).area if shape else None
