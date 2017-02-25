import bpy
import os
import glob
import json
from collections import OrderedDict
from pprint import pprint


def read_icons_info(n=3):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "../../iconList.json")
    print(os.getcwd())

    with open(file_path, encoding='utf-8') as data_file:
        data = json.load(data_file, object_pairs_hook=OrderedDict)

    numCategories = len(data.keys())
    numIconsInCategories = [len(x) for x in data.values()]

    # print("There are %d categories: %s" % (numCategories, list(data.keys())))
    # print("There are these number of icons in categories: ", numIconsInCategories)

    iconLocations = OrderedDict()

    y = 1
    nc = 0
    for category, nodes in data.items():
        nc = nc + 1
        # print("CATEGORY#%d: <%s> has %d nodes" % (nc, category, len(nodes.keys())))
        # print(type(nodes))
        # print("nodes: ", nodes)
        x = 0
        nn = 0
        for node, info in nodes.items():
            nn = nn + 1

            # print("xy: %d x %d" % (x+1, y+1))
            # print("NODE#%d: <%s> has icon ID: %s and rank: %d x %d - xy: %d x
            # %d" %  (nn, node, info, nc, nn, x+1, y+1))

            if x == n:
                x = 1
                y = y + 1
            else:
                x = x + 1

            iconLocations[info] = [x-1, y-1 ]

        print("")
        y = y + 1

    # pprint(iconLocations, indent=2)
    categories = list(data.keys())
    iconNames = list(iconLocations.keys())
    gridLocations = list(iconLocations.values())

    return categories, iconNames, gridLocations


def returnObjectByName(passedName=""):
    r = None
    obs = bpy.data.objects
    for ob in obs:
        if ob.name == passedName:
            r = ob
    return r


def sv_main(n=100, direction=0, scale=1.0):

    in_sockets = [
        ['s', 'N', n],
        ['s', 'Direction', direction],
        ['s', 'Scale', scale]
    ]

    categories, names, locations = read_icons_info(n)

    # create a list of objects in the scene with names matching the icon names
    objects = []
    oLocations = []
    for name, location in zip(names, locations):
        obj = returnObjectByName(name)
        if obj:
            objects.append(obj)
            oLocations.append(location)

    # print(type(names))
    # print(type(xy))
    print(categories)
    print(names)
    print(locations)
    maxX = max(x for x, y in locations) + 1
    maxY = max(y for x, y in locations) + 1
    print("max x: ", maxX)
    print("max y: ", maxY)

    allLocs = [[x+1, y+1] for x in range(maxX) for y in range(maxY)]

    if direction == 0:  # left->right
        vecs = [(x, y, 0) for x, y in locations]
        oVecs = [(x, y, 0) for x, y in oLocations]
        allVecs = [(x, y, 0) for x in range(maxX) for y in range(maxY)]
    elif direction == 1:  # down->up
        vecs = [(y, x, 0) for x, y in locations]
        oVecs = [(y, x, 0) for x, y in oLocations]
        allVecs = [(y, x, 0) for x in range(maxX) for y in range(maxY)]
    elif direction == 2:  # right->left
        vecs = [(maxX - x, y, 0) for x, y in locations]
        oVecs = [(maxX - x, y, 0) for x, y in oLocations]
        allVecs = [(maxX-x, maxY-y, 0) for x in range(maxX) for y in range(maxY)]
    else:  # up->Down
        vecs = [(x, maxY - y, 0) for x, y in locations]
        oVecs = [(x, maxY - y, 0) for x, y in oLocations]
        allVecs = [(x, maxY-y, 0) for x in range(maxX) for y in range(maxY)]

    vecs = [(x*scale, y*scale, z*scale) for x,y,z in vecs]
    oVecs = [(x*scale, y*scale, z*scale) for x,y,z in oVecs]
    allVecs = [(x*scale, y*scale, z*scale) for x,y,z in allVecs]

    out_sockets = [
        ['s', 'categories', categories],
        ['s', 'names', [names]],
        ['s', 'locations', locations],
        ['s', 'allLocs', allLocs],
        ['v', 'vectors', [vecs]],
        ['v', 'allVecs', [allVecs]],
        ['s', 'objects', objects],
        ['v', 'oLocs', [oVecs]],
    ]

    return in_sockets, out_sockets
