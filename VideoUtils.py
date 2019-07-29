from __future__ import division

import struct
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


def readPVDfile(pvdfile):
  """reads NSMA PVD file and returns timestamps and x,y."""

  with open(pvdfile, 'rb') as f:
    n_lines = sum(1 for line in f)
  f.close()
  ts = np.zeros(n_lines, dtype=np.uint64)
  x = np.zeros(n_lines)
  y = np.zeros(n_lines)
  
  with open(pvdfile, 'rb') as f:
    for i,line in enumerate(f):
      lineparts=(line.split())
      ts[i]=int(lineparts[0])/100
      x[i]=float(lineparts[1])
      y[i]=float(lineparts[2])

  f.close()

  return ts, x, y
   

def smooth(x,window_len=11,window='hanning'):
       # if x.ndim != 1:
                #raise ValueError, "smooth only accepts 1 dimension arrays."
        #if x.size < window_len:
         #       raise ValueError, "Input vector needs to be bigger than window size."
        if window_len<3:
                return x
       # if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        #        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
        s=np.r_[2*x[0]-x[window_len-1::-1],x,2*x[-1]-x[-1:-window_len:-1]]
        if window == 'flat': #moving average
                w=np.ones(window_len,'d')
        else:  
                w=eval('np.'+window+'(window_len)')
        y=np.convolve(w/w.sum(),s,mode='same')
        return y[window_len:-window_len+1]
 
def getVideoData(fname):
  
  with open(fname, 'rb') as f:
    data = f.read()[16384:]
    f.close()
  
  nrecords = int(len(data)/1828)
  print("Number of Records: {}".format(nrecords))
  #nrecs=3000
  xloc=np.zeros(nrecords, dtype=np.uint8)
  yloc=np.zeros(nrecords, dtype=np.uint8)
  hdir=np.zeros(nrecords, dtype=np.uint8)
  ts= np.zeros(nrecords, dtype=np.uint64)
 # dwPoints = np.zeros([nrecords,400])
  dwPoints = []
  dnTargets = []
  recsize=1828
        
  for record in range(nrecords):
    # print(record)
     recoffset = recsize*record
     swstx = int(struct.unpack('H',data[recoffset:recoffset+2])[0])
#     print("swstx: {}".format(swstx))
     swid = int(struct.unpack('H',data[recoffset+2:recoffset+4])[0])
#     print("swid: {}".format(swid))
     swdata_size = int(struct.unpack('H',data[recoffset+4:recoffset+6])[0])
#     print("swdata_size: {}".format(swdata_size)) 
     ts[record] = int(struct.unpack('Q',data[recoffset+6:recoffset+14])[0])
     dwP = struct.unpack('400I',data[recoffset+14:recoffset+1614])
#     print(len(dwP)
     dwPoints.append(tuple(p for p in dwP if int(p) != 0))
#     sncrc = int(struct.unpack('H', data[recoffset+1614:recoffset+1616])[0])

     xloc[record] = struct.unpack('i', data[recoffset+1615:recoffset+1619])[0]
     yloc[record] = struct.unpack('i', data[recoffset+1619:recoffset+1623])[0]
  
     dnT = struct.unpack('50i',data[recoffset+1628:recoffset+1828])
     #newone = struct.unpack('H', data[recoffset+1828:recoffset+1830])[0]
     #print("new one {}".format(newone))

     dnTargets.append(tuple(t for t in dnT if int(t) != 0))
  return ts, xloc, yloc, dwPoints, dnTargets
 
def returnMoving(xfilt,yfilt, thresh=20):
  
    moving = np.zeros(len(xfilt))
    notmoving = np.ones(len(xfilt))
    
    xdiff = np.diff(xfilt)
    ydiff = np.diff(yfilt)
    speed = np.abs(xdiff) + np.abs(ydiff)
    imoving = np.where(speed > thresh)
    moving[imoving] = 1
    notmoving[imoving] = 0
    return moving, notmoving, speed

def group_consecutives(vals, step=1):
    """Return list of consecutive lists of numbers from vals (number list)."""
    run = []
    result = [run]
    expect = None
    for v in vals:
        if (v == expect) or (expect is None):
            run.append(v)
        else:
            run = [v]
            result.append(run)
        expect = v + step
    return result

     
def returnTrajectoryFlags(moving, thresh):
    cmoving = list(np.cumsum(moving))
    plt.plot(cmoving)
    plt.show()
    g=group_consecutives(list(cmoving))
    start = [g[ii][0] for ii in xrange(len(g)) if len(g[ii]) > thresh]
    stop = [g[ii][-1] for ii in xrange(len(g)) if len(g[ii]) > thresh]
   
    cummoving = np.asarray(cmoving)
    trajstart = []
    trajstop = []
    for i in range(len(start)):
        trajstart.append(np.max(np.where(cummoving==start[i])))
        trajstop.append(np.min(np.where(cummoving==stop[i])))


#    trajstart = [cmoving.index(g[ii][0]) for ii in xrange(len(g)) if len(g[ii])  > thresh]
#    trajstop =  [cmoving.index(g[ii][1]) for ii in xrange(len(g)) if len(g[ii])  > thresh]
    return np.asarray(trajstart), np.asarray(trajstop)      
 
"""
Information about file formats for Cheetah video

UInt16 swstx Value indicating the beginning of a record. Always 0x800 (2048).
UInt16 swid ID for the originating system of this record.
UInt16 swdata_size Size of a VideoRec in bytes.
UInt64 qwTimeStamp Cheetah timestamp for this record. This value is in microseconds.
14 + 1600 1 4 4 4 200
UInt32[] dwPoints Points with the color bitfield values for this record. This is a 400
element array. See Video Tracker Bitfield Information below.

Int16 sncrc Unused*

Int32 dnextracted_x Extracted X location of the target being tracked.
Int32 dnextracted_y Extracted Y location of the target being tracked.
Int32 dnextracted_angle The calculated head angle in degrees clockwise from the positive Y
axis. Zero will be assigned if angle tracking is disabled.**

Int32[] dntargets Colored targets using the samebitfield format used by the dwPoints
array. Instead of transitions, the bitfield indicates the colors that make
up each particular target and the center point of that target. This is a
50 element array sorted by size from largest (index 0) to smallest
(index 49). A target value of 0 means that no target is present in that
index location. See Video Tracker Bitfield Information below.

Video Tracker Bitfield Information:
The pixel data consists of four hundred 32 bit values (one 32 bit value per pixel). The target data
consists of fifty 32 bit values. These data have the same bit-field format which means that the 32 bit
value is broken up into sub data to describe the X location (pixel number in the line), Y location (line
number of the frame) and the tracker colors which were above and below threshold.

The X and Y values are allocated 12 bits each, but their maximum value is determined by the resolution
that is used when tracking. See the header of your file for information about the resolution used when
your file was recorded. The other bits indicate which of the color values were above (1) or below (0)
their respective threshold setting. The layout of these bit fields can be visualized by the following:
"""
 
    
    
