from archicad import ACConnection
# https://github.com/nortikin/sverchok/issues/4058 issue of this


"""
in  PropertyID s   d=1 n=2
out GUIDS  s
out IDs s
out GUIDwalls s
out GUIDslabs s
out GUIDroofs s
out GUIDwindows s
out GUIDdoors s
out BOUNDSwalls v
out BOUNDSslabs v
out BOUNDSroofs v
out BOUNDSwindows v
out BOUNDSdoors v
"""

conn = ACConnection.connect()
assert conn
acc = conn.commands
act = conn.types

elementIds = acc.GetAllElements()

# get GUID - senceless
for element in elementIds:
    el = element.elementId.guid
    if str(PropertyID) in el.hex:
        info = conn.types.ElementClassification(element.elementId, conn.types.ClassificationId(conn.types.ClassificationSystemId(element.elementId.guid)))
        GUIDS.append([el.hex,info])

# get by types
def bboxes(objs):
    points = []
    for i in acc.Get3DBoundingBoxes(objs):
        m = list(i.boundingBox3D.to_dict().values())
        x,y,z,x1,y1,z1 = m
        point = [[x,y,z],[x,y1,z],[x1,y1,z],[x1,y,z]],[[x,y,z1],[x,y1,z1],[x1,y1,z1],[x1,y,z1]]
        #point = [mima[3]-mima[0],mima[4]-mima[1],mima[5]-mima[2]]
        points.append(point)
    return points

walls = conn.commands.GetElementsByType('Wall')
GUIDwalls.append(walls)
BOUNDSwalls.extend(bboxes(walls))

slabs = conn.commands.GetElementsByType('Slab')
GUIDslabs.append(slabs)
BOUNDSslabs.extend(bboxes(slabs))

roofs = conn.commands.GetElementsByType('Roof')
GUIDroofs.append(roofs)
BOUNDSroofs.extend(bboxes(roofs))

windows = conn.commands.GetElementsByType('Window')
GUIDwindows.append(windows)
BOUNDSwindows.extend(bboxes(windows))

doors = conn.commands.GetElementsByType('Door')
GUIDdoors.append(doors)
BOUNDSdoors.extend(bboxes(doors))

def ByProp(propID):
    # get element IDs as in ArchiCAD usually used
    elementIdBuiltInPropertyUserId = act.BuiltInPropertyUserId(propID)
    elementIdPropertyId = acc.GetPropertyIds([elementIdBuiltInPropertyUserId])[0].propertyId

    propertyValuesForElements = acc.GetPropertyValuesOfElements(elementIds, [elementIdPropertyId])

    elementIdPropertyValues = [] #set()
    for propertyValuesForElement in propertyValuesForElements:
        if propertyValuesForElement.propertyValues[0].propertyValue.status == 'normal':
            elementIdPropertyValue = propertyValuesForElement.propertyValues[0].propertyValue.value
            elementIdPropertyValues.append(elementIdPropertyValue) # add(elementIdPropertyValue)

        #if elementIdPropertyValue in elementIdPropertyValues:
            #print(f"Conflict: multiple elements have '{elementIdPropertyValue}' as element ID.")
    return [list(elementIdPropertyValues)]
IDs = ByProp('Wall_OutsideLength')#'General_ElementID')