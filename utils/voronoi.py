#############################################################################
#
# Voronoi diagram calculator/ Delaunay triangulator
# Translated to Python by Bill Simons
# September, 2005
#
# Additional changes by Carson Farmer added November 2010
#
# Calculate Delaunay triangulation or the Voronoi polygons for a set of 
# 2D input points.
#
# Derived from code bearing the following notice:
#
#  The author of this software is Steven Fortune.  Copyright (c) 1994 by AT&T
#  Bell Laboratories.
#  Permission to use, copy, modify, and distribute this software for any
#  purpose without fee is hereby granted, provided that this entire notice
#  is included in all copies of any software which is or includes a copy
#  or modification of this software and in all copies of the supporting
#  documentation for such software.
#  THIS SOFTWARE IS BEING PROVIDED "AS IS", WITHOUT ANY EXPRESS OR IMPLIED
#  WARRANTY.  IN PARTICULAR, NEITHER THE AUTHORS NOR AT&T MAKE ANY
#  REPRESENTATION OR WARRANTY OF ANY KIND CONCERNING THE MERCHANTABILITY
#  OF THIS SOFTWARE OR ITS FITNESS FOR ANY PARTICULAR PURPOSE.
#
# Comments were incorporated from Shane O'Sullivan's translation of the 
# original code into C++ (http://mapviewer.skynet.ie/voronoi.html)
#
# Steve Fortune's homepage: http://netlib.bell-labs.com/cm/cs/who/sjf/index.html
#
#############################################################################
#
# python 2 to conversion 3 using 2to3 by Linus Yng, added Site.__lt__ and cmp,
# modified output,downloaded from:
# http://svn.osgeo.org/qgis/trunk/qgis/python/plugins/fTools/tools/voronoi.py
#
#############################################################################

def usage():
    print("""
voronoi - compute Voronoi diagram or Delaunay triangulation

voronoi [-t -p -d]  [filename]

Voronoi reads from filename (or standard input if no filename given) for a set 
of points in the plane and writes either the Voronoi diagram or the Delaunay 
triangulation to the standard output.  Each input line should consist of two 
real numbers, separated by white space.

If option -t is present, the Delaunay triangulation is produced. 
Each output line is a triple i j k, which are the indices of the three points
in a Delaunay triangle. Points are numbered starting at 0.

If option -t is not present, the Voronoi diagram is produced.  
There are four output record types.

s a b      indicates that an input point at coordinates a b was seen.
l a b c    indicates a line with equation ax + by = c.
v a b      indicates a vertex at a b.
e l v1 v2  indicates a Voronoi segment which is a subsegment of line number l
           with endpoints numbered v1 and v2.  If v1 or v2 is -1, the line 
           extends to infinity.

Other options include:

d    Print debugging info

p    Produce output suitable for input to plot (1), rather than the forms 
     described above.

On unsorted data uniformly distributed in the unit square, voronoi uses about 
20n+140 bytes of storage.

AUTHOR
Steve J. Fortune (1987) A Sweepline Algorithm for Voronoi Diagrams,
Algorithmica 2, 153-174.
""")

#############################################################################
#
# For programmatic use two functions are available:
#
#   computeVoronoiDiagram(points)
#
#        Takes a list of point objects (which must have x and y fields).
#        Returns a 3-tuple of:
#
#           (1) a list of 2-tuples, which are the x,y coordinates of the 
#               Voronoi diagram vertices
#           (2) a list of 3-tuples (a,b,c) which are the equations of the
#               lines in the Voronoi diagram: a*x + b*y = c
#           (3) a list of 3-tuples, (l, v1, v2) representing edges of the 
#               Voronoi diagram.  l is the index of the line, v1 and v2 are
#               the indices of the vetices at the end of the edge.  If 
#               v1 or v2 is -1, the line extends to infinity.
#
#   computeDelaunayTriangulation(points):
#
#        Takes a list of point objects (which must have x and y fields).
#        Returns a list of 3-tuples: the indices of the points that form a
#        Delaunay triangle.
#
#############################################################################
import math
import sys
import getopt
import numpy as np

from math import sqrt, atan2
from collections import defaultdict

import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from sverchok.utils.logging import debug, info, error
from sverchok.utils.geom import center, LineEquation2D, CircleEquation2D
from sverchok.utils.math import weighted_center
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata

TOLERANCE = 1e-9
BIG_FLOAT = 1e38


def cmp(x,y):
    return x.__cmp__(y)
    
#------------------------------------------------------------------
class Context(object):
    def __init__(self):
        self.doPrint = 0
        self.debug   = 0
        self.plot    = 0
        self.triangulate = False
        self.vertices  = []    # list of vertex 2-tuples: (x,y)
        self.lines     = []    # equation of line 3-tuple (a b c), for the equation of the line a*x+b*y = c  
        self.edges     = []    # edge 3-tuple: (line index, vertex 1 index, vertex 2 index)   if either vertex index is -1, the edge extends to infiinity
        self.triangles = []    # 3-tuple of vertex indices
        self.polygons  = {}    # a dict of site:[edges] pairs

    def circle(self,x,y,rad):
        pass

    def clip_line(self,edge):
        pass

    def line(self,x0,y0,x1,y1):
        pass

    def outSite(self,s):
        if(self.debug):
            print("site (%d) at %f %f" % (s.sitenum, s.x, s.y))
        elif(self.triangulate):
            pass
        elif(self.plot):
            self.circle (s.x, s.y, cradius)
        elif(self.doPrint):
            print("s %f %f" % (s.x, s.y))

    def outVertex(self,s):
        self.vertices.append((s.x,s.y))
        if(self.debug):
            print("vertex(%d) at %f %f" % (s.sitenum, s.x, s.y))
        elif(self.triangulate):
            pass
        elif(self.doPrint and not self.plot):
            print("v %f %f" % (s.x,s.y))

    def outTriple(self,s1,s2,s3):
        self.triangles.append((s1.sitenum, s2.sitenum, s3.sitenum))
        if(self.debug):
            print("circle through left=%d right=%d bottom=%d" % (s1.sitenum, s2.sitenum, s3.sitenum))
        elif(self.triangulate and self.doPrint and not self.plot):
            print("%d %d %d" % (s1.sitenum, s2.sitenum, s3.sitenum))

    def outBisector(self,edge):
        self.lines.append((edge.a, edge.b, edge.c))
        if(self.debug):
            print("line(%d) %gx+%gy=%g, bisecting %d %d" % (edge.edgenum, edge.a, edge.b, edge.c, edge.reg[0].sitenum, edge.reg[1].sitenum))
        elif(self.triangulate):
            if(self.plot):
                self.line(edge.reg[0].x, edge.reg[0].y, edge.reg[1].x, edge.reg[1].y)
        elif(self.doPrint and not self.plot):
            print("l %f %f %f" % (edge.a, edge.b, edge.c))

    def outEdge(self,edge):
        sitenumL = -1
        if edge.ep[Edge.LE] is not None:
            sitenumL = edge.ep[Edge.LE].sitenum
        sitenumR = -1
        if edge.ep[Edge.RE] is not None:
            sitenumR = edge.ep[Edge.RE].sitenum
        if edge.reg[0].sitenum not in self.polygons:
            self.polygons[edge.reg[0].sitenum] = []
        if edge.reg[1].sitenum not in self.polygons:
            self.polygons[edge.reg[1].sitenum] = []
        self.polygons[edge.reg[0].sitenum].append((edge.edgenum,sitenumL,sitenumR))
        self.polygons[edge.reg[1].sitenum].append((edge.edgenum,sitenumL,sitenumR))
        self.edges.append((edge.edgenum,sitenumL,sitenumR))
        if(not self.triangulate):
            if self.plot:
                self.clip_line(edge)
            elif(self.doPrint): 
                print("e %d" % edge.edgenum, end=' ')
                print(" %d " % sitenumL, end=' ')
                print("%d" % sitenumR)

#------------------------------------------------------------------
def voronoi(siteList,context, raise_exception=False):
    try:
      edgeList  = EdgeList(siteList.xmin,siteList.xmax,len(siteList))
      priorityQ = PriorityQueue(siteList.ymin,siteList.ymax,len(siteList))
      siteIter = siteList.iterator()
      
      bottomsite = next(siteIter)
      context.outSite(bottomsite)
      newsite = next(siteIter)
      minpt = Site(-BIG_FLOAT,-BIG_FLOAT)
      while True:
          if not priorityQ.isEmpty():
              minpt = priorityQ.getMinPt()

          if (newsite and (priorityQ.isEmpty() or cmp(newsite,minpt) < 0)):
              # newsite is smallest -  this is a site event
              context.outSite(newsite)
              
              # get first Halfedge to the LEFT and RIGHT of the new site 
              lbnd = edgeList.leftbnd(newsite) 
              rbnd = lbnd.right                    
              
              # if this halfedge has no edge, bot = bottom site (whatever that is)
              # create a new edge that bisects
              bot  = lbnd.rightreg(bottomsite)     
              edge = Edge.bisect(bot,newsite)      
              context.outBisector(edge)
              
              # create a new Halfedge, setting its pm field to 0 and insert 
              # this new bisector edge between the left and right vectors in
              # a linked list
              bisector = Halfedge(edge,Edge.LE)    
              edgeList.insert(lbnd,bisector)       

              # if the new bisector intersects with the left edge, remove 
              # the left edge's vertex, and put in the new one
              p = lbnd.intersect(bisector)
              if p is not None:
                  priorityQ.delete(lbnd)
                  priorityQ.insert(lbnd,p,newsite.distance(p))

              # create a new Halfedge, setting its pm field to 1
              # insert the new Halfedge to the right of the original bisector
              lbnd = bisector
              bisector = Halfedge(edge,Edge.RE)     
              edgeList.insert(lbnd,bisector)        

              # if this new bisector intersects with the right Halfedge
              p = bisector.intersect(rbnd)
              if p is not None:
                  # push the Halfedge into the ordered linked list of vertices
                  priorityQ.insert(bisector,p,newsite.distance(p))
              
              newsite = next(siteIter)

          elif not priorityQ.isEmpty():
              # intersection is smallest - this is a vector (circle) event 

              # pop the Halfedge with the lowest vector off the ordered list of 
              # vectors.  Get the Halfedge to the left and right of the above HE
              # and also the Halfedge to the right of the right HE
              lbnd  = priorityQ.popMinHalfedge()      
              llbnd = lbnd.left               
              rbnd  = lbnd.right              
              rrbnd = rbnd.right              
              
              # get the Site to the left of the left HE and to the right of
              # the right HE which it bisects
              bot = lbnd.leftreg(bottomsite)  
              top = rbnd.rightreg(bottomsite) 
              
              # output the triple of sites, stating that a circle goes through them
              mid = lbnd.rightreg(bottomsite)
              context.outTriple(bot,top,mid)          

              # get the vertex that caused this event and set the vertex number
              # couldn't do this earlier since we didn't know when it would be processed
              v = lbnd.vertex                 
              siteList.setSiteNumber(v)
              context.outVertex(v)
              
              # set the endpoint of the left and right Halfedge to be this vector
              if lbnd.edge.setEndpoint(lbnd.pm,v):
                  context.outEdge(lbnd.edge)
              
              if rbnd.edge.setEndpoint(rbnd.pm,v):
                  context.outEdge(rbnd.edge)

              
              # delete the lowest HE, remove all vertex events to do with the 
              # right HE and delete the right HE
              edgeList.delete(lbnd)           
              priorityQ.delete(rbnd)
              edgeList.delete(rbnd)
              
              
              # if the site to the left of the event is higher than the Site
              # to the right of it, then swap them and set 'pm' to RIGHT
              pm = Edge.LE
              if bot.y > top.y:
                  bot,top = top,bot
                  pm = Edge.RE

              # Create an Edge (or line) that is between the two Sites.  This 
              # creates the formula of the line, and assigns a line number to it
              edge = Edge.bisect(bot, top)     
              context.outBisector(edge)

              # create a HE from the edge 
              bisector = Halfedge(edge, pm)    
              
              # insert the new bisector to the right of the left HE
              # set one endpoint to the new edge to be the vector point 'v'
              # If the site to the left of this bisector is higher than the right
              # Site, then this endpoint is put in position 0; otherwise in pos 1
              edgeList.insert(llbnd, bisector) 
              if edge.setEndpoint(Edge.RE - pm, v):
                  context.outEdge(edge)
              
              # if left HE and the new bisector don't intersect, then delete 
              # the left HE, and reinsert it 
              p = llbnd.intersect(bisector)
              if p is not None:
                  priorityQ.delete(llbnd);
                  priorityQ.insert(llbnd, p, bot.distance(p))

              # if right HE and the new bisector don't intersect, then reinsert it 
              p = bisector.intersect(rrbnd)
              if p is not None:
                  priorityQ.insert(bisector, p, bot.distance(p))
          else:
              break

      he = edgeList.leftend.right
      while he is not edgeList.rightend:
          context.outEdge(he.edge)
          he = he.right
      Edge.EDGE_NUM = 0
    except Exception as err:
        if raise_exception:
            raise err
        else:
          print("#Voronoi error#")
          print(str(err))

#------------------------------------------------------------------
def isEqual(a,b,relativeError=TOLERANCE):
    # is nearly equal to within the allowed relative error
    norm = max(abs(a),abs(b))
    return (norm < relativeError) or (abs(a - b) < (relativeError * norm))

#------------------------------------------------------------------
class Site(object):
    def __init__(self,x=0.0,y=0.0,sitenum=0):
        self.x = x
        self.y = y
        self.sitenum = sitenum

    def dump(self):
        print("Site #%d (%g, %g)" % (self.sitenum,self.x,self.y))
    
    
    def __lt__(self, other):
        if self.y < other.y:
            return 1
        elif self.y > other.y:
            return 0
        elif self.x < other.x:
            return 1
        elif self.x > other.x:
            return 0 
                   
    def __str__(self):
        return str((self.x,self.y))
         
    def __cmp__(self,other):
        if self.y < other.y:
            return -1
        elif self.y > other.y:
            return 1
        elif self.x < other.x:
            return -1
        elif self.x > other.x:
            return 1
        else:
            return 0

    def distance(self,other):
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx*dx + dy*dy)

#------------------------------------------------------------------
class Edge(object):
    LE = 0
    RE = 1
    EDGE_NUM = 0
    DELETED = {}   # marker value

    def __init__(self):
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0
        self.ep  = [None,None]
        self.reg = [None,None]
        self.edgenum = 0

    def dump(self):
        print("(#%d a=%g, b=%g, c=%g)" % (self.edgenum,self.a,self.b,self.c))
        print("ep",self.ep)
        print("reg",self.reg)

    def setEndpoint(self, lrFlag, site):
        self.ep[lrFlag] = site
        if self.ep[Edge.RE - lrFlag] is None:
            return False
        return True

    @staticmethod
    def bisect(s1,s2):
        newedge = Edge()
        newedge.reg[0] = s1 # store the sites that this edge is bisecting
        newedge.reg[1] = s2

        # to begin with, there are no endpoints on the bisector - it goes to infinity
        # ep[0] and ep[1] are None

        # get the difference in x dist between the sites
        dx = float(s2.x - s1.x)
        dy = float(s2.y - s1.y)
        adx = abs(dx)  # make sure that the difference in positive
        ady = abs(dy)
        
        # get the slope of the line
        newedge.c = float(s1.x * dx + s1.y * dy + (dx*dx + dy*dy)*0.5)  
        if dx == 0 and dy == 0:
            raise Exception(f"Can't build an edge: two points are coinciding: {s1.sitenum}, {s2.sitenum}")
        if adx > ady :
            # set formula of line, with x fixed to 1
            newedge.a = 1.0
            newedge.b = dy/dx
            newedge.c /= dx
        else:
            # set formula of line, with y fixed to 1
            newedge.b = 1.0
            newedge.a = dx/dy
            newedge.c /= dy

        newedge.edgenum = Edge.EDGE_NUM
        Edge.EDGE_NUM += 1
        return newedge


#------------------------------------------------------------------
class Halfedge(object):
    def __init__(self,edge=None,pm=Edge.LE):
        self.left  = None   # left Halfedge in the edge list
        self.right = None   # right Halfedge in the edge list
        self.qnext = None   # priority queue linked list pointer
        self.edge  = edge   # edge list Edge
        self.pm     = pm
        self.vertex = None  # Site()
        self.ystar  = BIG_FLOAT

    def dump(self):
        print("Halfedge--------------------------")
        print("left: ",    self.left)  
        print("right: ",   self.right) 
        print("edge: ",    self.edge)  
        print("pm: ",      self.pm)    
        print("vertex: ", end=' ')
        if self.vertex: self.vertex.dump()
        else: print("None")
        print("ystar: ",   self.ystar) 


    def __cmp__(self,other):
        if self.ystar > other.ystar:
            return 1
        elif self.ystar < other.ystar:
            return -1
        elif self.vertex.x > other.vertex.x:
            return 1
        elif self.vertex.x < other.vertex.x:
            return -1
        else:
            return 0

    def leftreg(self,default):
        if not self.edge: 
            return default
        elif self.pm == Edge.LE:
            return self.edge.reg[Edge.LE]
        else:
            return self.edge.reg[Edge.RE]

    def rightreg(self,default):
        if not self.edge: 
            return default
        elif self.pm == Edge.LE:
            return self.edge.reg[Edge.RE]
        else:
            return self.edge.reg[Edge.LE]


    # returns True if p is to right of halfedge self
    def isPointRightOf(self,pt):
        e = self.edge
        topsite = e.reg[1]
        right_of_site = pt.x > topsite.x
        
        if(right_of_site and self.pm == Edge.LE): 
            return True
        
        if(not right_of_site and self.pm == Edge.RE):
            return False
        
        if(e.a == 1.0):
            dyp = pt.y - topsite.y
            dxp = pt.x - topsite.x
            fast = 0;
            if ((not right_of_site and e.b < 0.0) or (right_of_site and e.b >= 0.0)):
                above = dyp >= e.b * dxp
                fast = above
            else:
                above = pt.x + pt.y * e.b > e.c
                if(e.b < 0.0):
                    above = not above
                if (not above):
                    fast = 1
            if (not fast):
                dxs = topsite.x - (e.reg[0]).x
                above = e.b * (dxp*dxp - dyp*dyp) < dxs*dyp*(1.0+2.0*dxp/dxs + e.b*e.b)
                if(e.b < 0.0):
                    above = not above
        else:  # e.b == 1.0 
            yl = e.c - e.a * pt.x
            t1 = pt.y - yl
            t2 = pt.x - topsite.x
            t3 = yl - topsite.y
            above = t1*t1 > t2*t2 + t3*t3
        
        if(self.pm==Edge.LE):
            return above
        else:
            return not above

    #--------------------------
    # create a new site where the Halfedges el1 and el2 intersect
    def intersect(self,other):
        e1 = self.edge
        e2 = other.edge
        if (e1 is None) or (e2 is None):
            return None

        # if the two edges bisect the same parent return None
        if e1.reg[1] is e2.reg[1]:
            return None

        d = e1.a * e2.b - e1.b * e2.a
        if isEqual(d,0.0):
            return None

        xint = (e1.c*e2.b - e2.c*e1.b) / d
        yint = (e2.c*e1.a - e1.c*e2.a) / d
        if(cmp(e1.reg[1],e2.reg[1]) < 0):
            he = self
            e = e1
        else:
            he = other
            e = e2

        rightOfSite = xint >= e.reg[1].x
        if((rightOfSite     and he.pm == Edge.LE) or
           (not rightOfSite and he.pm == Edge.RE)):
            return None

        # create a new site at the point of intersection - this is a new 
        # vector event waiting to happen
        return Site(xint,yint)

        

#------------------------------------------------------------------
class EdgeList(object):
    def __init__(self,xmin,xmax,nsites):
        if xmin > xmax: xmin,xmax = xmax,xmin
        self.hashsize = int(2*math.sqrt(nsites+4))
        
        self.xmin   = xmin
        self.deltax = float(xmax - xmin)
        self.hash   = [None]*self.hashsize
        
        self.leftend  = Halfedge()
        self.rightend = Halfedge()
        self.leftend.right = self.rightend
        self.rightend.left = self.leftend
        self.hash[0]  = self.leftend
        self.hash[-1] = self.rightend

    def insert(self,left,he):
        he.left  = left
        he.right = left.right
        left.right.left = he
        left.right = he

    def delete(self,he):
        he.left.right = he.right
        he.right.left = he.left
        he.edge = Edge.DELETED

    # Get entry from hash table, pruning any deleted nodes 
    def gethash(self,b):
        if(b < 0 or b >= self.hashsize):
            return None
        he = self.hash[b]
        if he is None or he.edge is not Edge.DELETED:
            return he

        #  Hash table points to deleted half edge.  Patch as necessary.
        self.hash[b] = None
        return None

    def leftbnd(self,pt):
        # Use hash table to get close to desired halfedge 
        bucket = int(((pt.x - self.xmin)/self.deltax * self.hashsize))
        
        if(bucket < 0): 
            bucket =0;
        
        if(bucket >=self.hashsize): 
            bucket = self.hashsize-1

        he = self.gethash(bucket)
        if(he is None):
            i = 1
            while True:
                he = self.gethash(bucket-i)
                if (he is not None): break;
                he = self.gethash(bucket+i)
                if (he is not None): break;
                i += 1
    
        # Now search linear list of halfedges for the correct one
        if (he is self.leftend) or (he is not self.rightend and he.isPointRightOf(pt)):
            he = he.right
            while he is not self.rightend and he.isPointRightOf(pt):
                he = he.right
            he = he.left;
        else:
            he = he.left
            while (he is not self.leftend and not he.isPointRightOf(pt)):
                he = he.left

        # Update hash table and reference counts
        if(bucket > 0 and bucket < self.hashsize-1):
            self.hash[bucket] = he
        return he


#------------------------------------------------------------------
class PriorityQueue(object):
    def __init__(self,ymin,ymax,nsites):
        self.ymin = ymin
        self.deltay = ymax - ymin
        self.hashsize = int(4 * math.sqrt(nsites))
        self.count = 0
        self.minidx = 0
        self.hash = []
        for i in range(self.hashsize):
            self.hash.append(Halfedge())

    def __len__(self):
        return self.count

    def isEmpty(self):
        return self.count == 0

    def insert(self,he,site,offset):
        he.vertex = site
        he.ystar  = site.y + offset
        last = self.hash[self.getBucket(he)]
        next = last.qnext
        while((next is not None) and cmp(he,next) > 0):
            last = next
            next = last.qnext
        he.qnext = last.qnext
        last.qnext = he
        self.count += 1

    def delete(self,he):
        if (he.vertex is not None):
            last = self.hash[self.getBucket(he)]
            while last.qnext is not he:
                last = last.qnext
            last.qnext = he.qnext
            self.count -= 1
            he.vertex = None

    def getBucket(self,he):
        bucket = int(((he.ystar - self.ymin) / self.deltay) * self.hashsize)
        if bucket < 0: bucket = 0
        if bucket >= self.hashsize: bucket = self.hashsize-1
        if bucket < self.minidx:  self.minidx = bucket
        return bucket

    def getMinPt(self):
        while(self.hash[self.minidx].qnext is None):
            self.minidx += 1
        he = self.hash[self.minidx].qnext
        x = he.vertex.x
        y = he.ystar
        return Site(x,y)

    def popMinHalfedge(self):
        curr = self.hash[self.minidx].qnext
        self.hash[self.minidx].qnext = curr.qnext
        self.count -= 1
        return curr


#------------------------------------------------------------------
class SiteList(object):
    def __init__(self,pointList):
        self.__sites = []
        self.__sitenum = 0

        self.__xmin = pointList[0].x
        self.__ymin = pointList[0].y
        self.__xmax = pointList[0].x
        self.__ymax = pointList[0].y
        for i,pt in enumerate(pointList):
            self.__sites.append(Site(pt.x,pt.y,i))
            if pt.x < self.__xmin: self.__xmin = pt.x
            if pt.y < self.__ymin: self.__ymin = pt.y
            if pt.x > self.__xmax: self.__xmax = pt.x
            if pt.y > self.__ymax: self.__ymax = pt.y
        self.__sites.sort()

    def setSiteNumber(self,site):
        site.sitenum = self.__sitenum
        self.__sitenum += 1

    class Iterator(object):
        def __init__(this,lst):  this.generator = (s for s in lst)
        def __iter__(this):      return this
        def __next__(this): 
            try:
                return next(this.generator)
            except StopIteration:
                return None

    def iterator(self):
        return SiteList.Iterator(self.__sites)

    def __iter__(self):
        return SiteList.Iterator(self.__sites)

    def __len__(self):
        return len(self.__sites)

    def _getxmin(self): return self.__xmin
    def _getymin(self): return self.__ymin
    def _getxmax(self): return self.__xmax
    def _getymax(self): return self.__ymax
    xmin = property(_getxmin)
    ymin = property(_getymin)
    xmax = property(_getxmax)
    ymax = property(_getymax)



#    siteList = SiteList(points)
#     context  = Context()
#     voronoi(siteList,context)
#     return (context.vertices,context.lines,context.edges)


 
#------------------------------------------------------------------
def computeVoronoiDiagram(points, raise_exception=False):
    """ Takes a list of point objects (which must have x and y fields).
        Returns a Context object.

           (1) context.vertices: a list of 2-tuples, which are the x,y
               coordinates of the Voronoi diagram vertices
           (2) context.lines: a list of 3-tuples (a,b,c) which are the
               equations of the lines in the Voronoi diagram: a*x + b*y = c
           (3) context.edges: a list of 3-tuples, (l, v1, v2) representing edges of the 
               Voronoi diagram.  l is the index of the line, v1 and v2 are
               the indices of the vetices at the end of the edge.  If 
               v1 or v2 is -1, the line extends to infinity.
           (4) context.polygons: a dict of site:[edges] pairs
    """

    siteList = SiteList(points)
    context  = Context()
    context.triangulate = True
    voronoi(siteList,context, raise_exception)
    return context

#------------------------------------------------------------------
def computeDelaunayTriangulation(points):
    """ Takes a list of point objects (which must have x and y fields).
        Returns a list of 3-tuples: the indices of the points that form a
        Delaunay triangle.
    """
#   original function in comment    
#    siteList = SiteList(points)
#     context  = Context()
#     context.triangulate = true
#     voronoi(siteList,context)
#     return context.triangles
    
    siteList = SiteList(points)
    context  = Context()
    context.triangulate = True
    voronoi(siteList,context)
    return context.triangles

#-----------------------------------------------------------------------------
# if __name__=="__main__":
#     try:
#         optlist,args = getopt.getopt(sys.argv[1:],"thdp")
#     except getopt.GetoptError:
#         usage()
#         sys.exit(2)
#       
#     doHelp = 0
#     c = Context()
#     c.doPrint = 1
#     for opt in optlist:
#         if opt[0] == "-d":  c.debug = 1
#         if opt[0] == "-p":  c.plot  = 1
#         if opt[0] == "-t":  c.triangulate = 1
#         if opt[0] == "-h":  doHelp = 1
# 
#     if not doHelp:
#         pts = []
#         fp = sys.stdin
#         if len(args) > 0:
#             fp = open(args[0],'r')
#         for line in fp:
#             fld = line.split()
#             x = float(fld[0])
#             y = float(fld[1])
#             pts.append(Site(x,y))
#         if len(args) > 0: fp.close()
# 
#     if doHelp or len(pts) == 0:
#         usage()
#         sys.exit(2)
# 
#     sl = SiteList(pts)
#     voronoi(sl,c)

class Bounds(object):
    def __init__(self):
        self.x_max = 0
        self.y_max = 0
        self.x_min = 0
        self.y_min = 0
        self.r_max = 0
        self.center = (0,0)

    @classmethod
    def new(cls, mode):
        if mode == 'BOX':
            return BoxBounds()
        elif mode == 'CIRCLE':
            return CircleBounds()
        else:
            raise Exception("Unknown bounds type")

    def __repr__(self):
        return f"Bounds[C: {self.center}, R: {self.r_max}, X: {self.x_min} - {self.x_max}, Y: {self.y_min} - {self.y_max}]"

    def restrict(self, point):
        raise Exception("not implemented")

    def init_from_sites(self, sites):
        self.x_max = -BIG_FLOAT
        self.x_min = BIG_FLOAT
        self.y_min = BIG_FLOAT
        self.y_max = -BIG_FLOAT
        x0, y0, z0 = center(sites)
        self.center = (x0, y0)
        # creates points in format for voronoi library, throwing away z
        for x, y, z in sites:
            r = sqrt((x-x0)**2 + (y-y0)**2)
            self.r_max = max(r, self.r_max)
            self.x_max = max(x, self.x_max)
            self.x_min = min(x, self.x_min)
            self.y_max = max(y, self.y_max)
            self.y_min = min(y, self.y_min)

class Mesh2D(object):
    def __init__(self):
        self.verts = []
        self.all_edges = set()
        self.linked_verts = defaultdict(set)
        self._next_vert = 0

    @classmethod
    def from_pydata(cls, verts, edges):
        mesh = Mesh2D()
        for vert in verts:
            mesh.new_vert(vert)
        for i, j in edges:
            mesh.new_edge(i, j)
        return mesh

    def new_vert(self, vert):
        if vert is None:
            raise Exception("new_vert(None)")
        if vert[0] is None or vert[1] is None:
            raise Exception(f"new_vert({vert})")
        self.verts.append(vert)
        idx = self._next_vert
        self._next_vert += 1
        return idx

    def new_edge(self, i, j):
        v1, v2 = self.verts[i], self.verts[j]
        #info("Add: %s (%s) => %s (%s)", i, v1, j, v2)
        self.all_edges.add((v1, v2))
        self.linked_verts[i].add(j)
        self.linked_verts[j].add(i)

    def remove_edge(self, i, j):
        if (self.verts[i], self.verts[j]) in self.all_edges:
            self.all_edges.remove((self.verts[i], self.verts[j]))
        if (self.verts[j], self.verts[i]) in self.all_edges:
            self.all_edges.remove((self.verts[j], self.verts[i]))
        if j in self.linked_verts[i]:
            self.linked_verts[i].remove(j)
        if i in self.linked_verts[j]:
            self.linked_verts[j].remove(i)

    def to_pydata(self):
        verts = [vert for vert in self.verts if vert is not None]
        lut = dict((vert, idx) for idx, vert in enumerate(verts))
        #info(lut)
        edges = []
        for v1, v2 in self.all_edges:
            i1 = lut.get(v1, None)
            i2 = lut.get(v2, None)
            #info("Get: %s (%s) => %s (%s)", v1, i1, v2, i2)
            if i1 is not None and i2 is not None and i1 != i2:
                edges.append((i1, i2))

        return verts, edges

class BoxBounds(Bounds):

    def contains(self, p, edge_ok = True):
        x, y = tuple(p)
        if edge_ok:
            return (self.x_min <= x <= self.x_max) and (self.y_min <= y <= self.y_max)
        else:
            return (self.x_min < x < self.x_max) and (self.y_min < y < self.y_max)
    
    @property
    def edges(self):
        v1 = (self.x_min, self.y_min)
        v2 = (self.x_min, self.y_max)
        v3 = (self.x_max, self.y_max)
        v4 = (self.x_max, self.y_min)

        e1 = (v1, v2)
        e2 = (v2, v3)
        e3 = (v3, v4)
        e4 = (v4, v1)

        return [e1, e2, e3, e4]

    def segment_intersection(self, p1, p2):
        if not isinstance(p1, Vector):
            p1 = Vector(p1)
        if not isinstance(p2, Vector):
            p2 = Vector(p2)

        min_r = BIG_FLOAT
        nearest = None

        for v_i, v_j in self.edges:
            intersection = intersect_line_line_2d(p1, p2, v_i, v_j)
            if intersection is not None:
                r = (p1 - intersection).length
                if r < min_r:
                    nearest = intersection
                    min_r = r

        return nearest

    def ray_intersection(self, p, line):
        p = Vector(center(line.sites))

        min_r = BIG_FLOAT
        nearest = None

        for v_i, v_j in self.edges:
            bound = LineEquation2D.from_two_points(v_i, v_j)
            intersection = bound.intersect_with_line(line)
            if intersection is not None:
                r = (p - intersection).length
                #info("INT: [%s - %s] X [%s] => %s (%s)", v_i, v_j, line, intersection, r)
                if r < min_r:
                    nearest = intersection
                    min_r = r

        return nearest

    def line_intersection(self, line):
        result = []
        eps = 1e-8
        for v_i, v_j in self.edges:
            bound = LineEquation2D.from_two_points(v_i, v_j)
            intersection = bound.intersect_with_line(line)
            if intersection is not None:
                x,y = tuple(intersection)
                if (self.x_min-eps <= x <= self.x_max+eps) and (self.y_min-eps <= y <= self.y_max+eps):
                    result.append(intersection)
        return result

    def restrict(self, point):
        def chop(t, m, M):
            return min(max(t, m), M)

        x, y, z = tuple(point)
        x = chop(x, self.x_min, self.x_max)
        y = chop(y, self.y_min, self.y_max)

        return x,y,z

    def project(self, point):
        x, y, z = tuple(point)
        mid_x = 0.5*(self.x_min + self.x_max)
        mid_y = 0.5*(self.y_min + self.y_max)
        if x > mid_x:
            x = self.x_max
        else:
            x = self.x_min
        if y > mid_y:
            y = self.y_max
        else:
            y = self.y_min
        return x, y, z

class CircleBounds(Bounds):

    @property
    def circle(self):
        return CircleEquation2D(self.center, self.r_max)

    def contains(self, p, edge_ok=True):
        return self.circle.contains(p, include_bound=edge_ok)

    def segment_intersection(self, p1, p2):
        r = self.circle.intersect_with_segment(p1, p2)
        if r is None:
            return None
        if r[0] is None and r[1] is None:
            return None
        if r[0] is not None:
            return r[0]
        if r[1] is not None:
            return r[1]

    def ray_intersection(self, p, line):
        p = Vector(center(line.sites))
        intersection = self.circle.intersect_with_line(line)
        #info("RI: {line} X {self.circle} => {intersection}")
        if intersection is None:
            return None
        else:
            v1, v2 = intersection
            r1 = (p - v1).length
            r2 = (p - v2).length
            if r1 < r2:
                return v1
            else:
                return v2

    def line_intersection(self, line):
        intersection = self.circle.intersect_with_line(line)
        return intersection

    def restrict(self, point):
        pt2d = (point[0], point[1])
        if self.contains(pt2d):
            return point
        else:
            v = self.circle.projection_of_point(Vector(pt2d), nearest=True)
            x,y = tuple(v)
            return x,y,0

    def project(self, point):
        pt2d = (point[0], point[1])
        v = self.circle.projection_of_point(Vector(pt2d), nearest=True)
        x,y = tuple(v)
        return x,y,0

def voronoi_bounded(sites, bound_mode='BOX', clip=True, draw_bounds=True, draw_hangs=False, make_faces=False, ordered_faces=False, max_sides=10):

    bounds = Bounds.new(bound_mode)
    bounds.init_from_sites(sites)
    source_sites = []
    for x, y, z in sites:
        source_sites.append(Site(x, y))

    delta = clip
    bounds.x_max = bounds.x_max + delta
    bounds.y_max = bounds.y_max + delta

    bounds.x_min = bounds.x_min - delta
    bounds.y_min = bounds.y_min - delta

    bounds.r_max = bounds.r_max + delta

    voronoi_data = computeVoronoiDiagram(source_sites, raise_exception=True)
    verts = voronoi_data.vertices
    lines = voronoi_data.lines
    all_edges = voronoi_data.edges

    finite_edges = [(edge[1], edge[2]) for edge in all_edges if -1 not in edge]
    bm = Mesh2D.from_pydata(verts, finite_edges)

    # clipping box to bounding box.
    verts_to_remove = set()
    edges_to_remove = set()
    bounding_verts = []

    # For each diagram vertex that is outside of the bounds,
    # cut each edge connected with that vertex by bounding line.
    # Remove such vertices, remove such edges, and instead add
    # vertices lying on the bounding line and corresponding edges.
    for vert_idx, vert in enumerate(bm.verts[:]):
        x, y = tuple(vert)
        if not bounds.contains((x,y)):
            verts_to_remove.add(vert_idx)
            for other_vert_idx in list(bm.linked_verts[vert_idx]):
                edges_to_remove.add((vert_idx, other_vert_idx))
                if draw_hangs or draw_bounds:
                    other_vert = bm.verts[other_vert_idx]
                    if other_vert is not None:
                        x2, y2 = tuple(other_vert)
                        intersection = bounds.segment_intersection((x,y), (x2,y2))
                        if intersection is not None:
                            intersection = tuple(intersection)
                            new_vert_idx = bm.new_vert(intersection)
                            bounding_verts.append(new_vert_idx)
                            #info("CLIP: Added point: %s => %s", (x_i, y_i), new_vert_idx)
                            bm.new_edge(other_vert_idx, new_vert_idx)

    # Diagram lines that go infinitely from one side of diagram to another
    infinite_lines = []
    # Lines that start at the one vertex of the diagram and go to infinity
    rays = defaultdict(list)
    if draw_hangs or draw_bounds:
        sites_by_line = defaultdict(list)

        for site_idx in voronoi_data.polygons.keys():
            for line_index, i1, i2 in voronoi_data.polygons[site_idx]:
                if i1 == -1 or i2 == -1:
                    site = source_sites[site_idx]
                    sites_by_line[line_index].append((site.x, site.y))

        for line_index, i1, i2 in all_edges:
            if i1 == -1 or i2 == -1:
                line = lines[line_index]
                a, b, c = line
                eqn = LineEquation2D(a, b, -c)
                if i1 == -1 and i2 != -1:
                    eqn.sites = sites_by_line[line_index]
                    rays[i2].append(eqn)
                elif i2 == -1 and i1 != -1:
                    eqn.sites = sites_by_line[line_index]
                    rays[i1].append(eqn)
                elif i1 == -1 and i2 == -1:
                    infinite_lines.append(eqn)

        # For each (half-infinite) ray, calculate it's intersection
        # with the bounding line and draw an edge from ray's beginning to
        # the bounding line.
        # NB: The data returned from voronoi.py for such lines
        # is a vertex and a line equation. The line obviously intersects
        # the bounding line in two points; which one should we choose?
        # Let's choose that one which is closer to site points which the
        # line is dividing.
        for vert_index in rays.keys():
            x,y = bm.verts[vert_index]
            vert = Vector((x,y))
            if vert_index not in verts_to_remove:
                for line in rays[vert_index]:
                    intersection = bounds.ray_intersection(vert, line)
                    intersection = tuple(intersection)
                    new_vert_idx = bm.new_vert(intersection)
                    bounding_verts.append(new_vert_idx)
                    #info("INF: Added point: %s: %s => %s", (x,y), (x_i, y_i), new_vert_idx)
                    bm.new_edge(vert_index, new_vert_idx)

        # For each infinite (in two directions) line,
        # calculate two it's intersections with the bounding
        # line and connect them by an edge.
        for eqn in infinite_lines:
            intersections = bounds.line_intersection(eqn)
            if len(intersections) == 2:
                v1, v2 = intersections
                new_vert_1_idx = bm.new_vert(tuple(v1))
                new_vert_2_idx = bm.new_vert(tuple(v2))
                bounding_verts.append(new_vert_1_idx)
                bounding_verts.append(new_vert_2_idx)
                bm.new_edge(new_vert_1_idx, new_vert_2_idx)
            elif len(intersections) == 1:
                v = intersections[0]
                new_vert_idx = bm.new_vert(tuple(v))
                bounding_verts.append(new_vert_idx)
            else:
                error("unexpected number of intersections of infinite line %s with area bounds %s: %s", eqn, bounds, intersections)

        # TODO: there could be (finite) edges, which have both ends
        # outside of the bounding line. We could detect such edges and
        # process similarly to infinite lines - calculate two intersections
        # with the bounding line and connect them by an edge.
        # Currently I consider such cases as rare, so this is a low priority issue.
        # Btw, such edges do not fall under definition of either "bounding edge"
        # or "hanging edge"; so should we add a separate checkbox for such edges?...

    if draw_bounds and bounding_verts:
        bounding_verts.sort(key = lambda idx: atan2(bm.verts[idx][1], bm.verts[idx][0]))
        for i, j in zip(bounding_verts, bounding_verts[1:]):
            bm.new_edge(i, j)
        bm.new_edge(bounding_verts[-1], bounding_verts[0])

    for i, j in edges_to_remove:
        bm.remove_edge(i, j)
    for vert_idx in verts_to_remove:
        bm.verts[vert_idx] = None

    verts, edges = bm.to_pydata()

    new_vertices = [(vert[0], vert[1], 0) for vert in verts]

    if make_faces:
        for i,j in edges:
            if i==j:
                print(i,j)
        bm = bmesh_from_pydata(new_vertices, edges, [])
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=max_sides)
        new_vertices, edges, new_faces = pydata_from_bmesh(bm)
        bm.free()
        if ordered_faces:
            bvh = BVHTree.FromPolygons(new_vertices, new_faces)
            face_by_site = dict()
            for site_idx, site in enumerate(sites):
                loc, normal, index, distance = bvh.find_nearest(site)
                if index is not None:
                    face_by_site[site_idx] = index
            r = []
            for i in range(len(sites)):
                if i not in face_by_site:
                    raise Exception(f"Can't find a face for site #{i}")
                face_idx = face_by_site[i]
                face = new_faces[face_idx]
                r.append(face)
            new_faces = r
    else:
        new_faces = []

    return new_vertices, edges, new_faces

def unique_points(points, eps=1e-4):
    kdt = KDTree(len(points))
    for i, p in enumerate(points):
        kdt.insert(p, i)
    kdt.balance()
    unique = []
    repeating = []
    mask = []
    for p in points:
        found = kdt.find_n(p, 2)
        if len(found) > 1:
            loc, idx, distance = found[1]
            ok = distance > eps
            mask.append(ok)
            if ok:
                unique.append(p)
            else:
                repeating.append(p)
    return mask, unique, repeating

def lloyd2d(bound_mode, verts, n_iterations, clip=0.0, weight_field=None):
    bounds = Bounds.new(bound_mode)
    bounds.init_from_sites(verts)

    def invert_points(pts):
        result = []
        for pt in pts:
            pt2d = x0,y0 = (pt[0], pt[1])
            if bounds.contains(pt2d, edge_ok=False):
                x1,y1,z1 = bounds.project(pt)
                if x1 == x0 and y1 == y0:
                    continue
                x2 = x0 + 2*(x1-x0)
                y2 = y0 + 2*(y1-y0)
                out_pt = (x2, y2, z1)
                result.append(out_pt)
        return result
    
    def iteration(pts):
        mask, pts, repeating = unique_points(pts)
        n = len(pts)
        all_pts = pts + invert_points(pts)
        voronoi_verts, _, voronoi_faces = voronoi_bounded(all_pts,
                    bound_mode = bound_mode,
                    clip = clip,
                    draw_bounds = True,
                    draw_hangs = True,
                    make_faces = True,
                    ordered_faces = True,
                    max_sides = 20)
        centers = []
        for face in voronoi_faces[:n]:
            face_verts = np.array([voronoi_verts[i] for i in face])
            new_pt = weighted_center(face_verts, weight_field)
            centers.append(tuple(new_pt))

        result = []
        i = 0
        j = 0
        for is_unique in mask:
            if is_unique:
                result.append(centers[i])
                i += 1
            else:
                result.append(repeating[j])
                j += 1
        return result

    def restrict(pts):
        return [bounds.restrict(pt) for pt in pts]

    points = restrict(verts)
    for i in range(n_iterations):
        points = iteration(points)
        points = restrict(points)
    return points

