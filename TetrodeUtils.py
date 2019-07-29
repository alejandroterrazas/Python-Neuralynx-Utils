import numpy as np
import struct

def readTFile(filename):
  
  with open(filename, 'rb') as f:
    data  = f.read()
  f.close()

  spikes = data[data.index('%%ENDHEADER')+12:]
  if filename.endswith('t64'):
    recsize = 8
    nevents = len(spikes)//recsize 
    ts = np.ndarray((nevents,), '>Q', spikes, 0, (8,))
  else:
    recsize = 4
    nevents = len(spikes)//recsize
    print("nspikes in tfile: {}".format(nevents)) 
    ts = np.ndarray((nevents,), '>I', spikes, 0, (4,))
     
  print("nspikes in tfile: {}".format(nevents))
  return ts
 
def readTetrode(filename):
   recsize = 304
   with open(filename, 'rb') as f:  
    spikedata = f.read()[16384:]
    f.close()
   
   nevents=int(len(spikedata)/recsize)
   print("Number of spikes: {}".format(nevents))
   ts = np.ndarray((nevents,), '<Q', spikedata, 0, (304,))
   dwScnumber = np.ndarray((nevents,), '<I', spikedata, 8, (304,))
   dwCellnumber = np.ndarray((nevents,), '<I', spikedata, 12, (304,))
   dnParams = np.ndarray((nevents,4), '<I', spikedata, 16, (304,4))

   waveforms = np.ndarray((nevents,128), '<h', spikedata, 48, (304,2)).reshape(nevents,32,4).transpose()
  
   return ts, waveforms
'''
def writeTetrode(ts, waveforms, prefix, filename):
   recsize = 304
   with open(filename, 'rb') as f:
     headerdata=f.read()[:16384]
   f.close()

   "epoch1"+filename
   with open(prefix+filename, 'wb') as f:
     f.write(headerdata)
     for index, timestamp in enumerate(ts):
       f.write(ts)
       f.write(0)
'''       


def readMSFiringFile(cfile, printsummary=False):

  with open(cfile, 'rb') as f:
    curated = f.read()
    f.close()
    
    #print("data format {}".format(struct.unpack('i', hdr[0:4])[0]))
    nrecs = struct.unpack('i', curated[16:20])[0]
    if nrecs == 0:
       print("No records!!")
       return [],[],[]  
    if printsummary:
      print("data format {}".format(struct.unpack('i', curated[0:4])[0]))
      #print("recsize: {}".format(recsize))
      print("n dimensions {}".format(struct.unpack('i', curated[8:12])[0]))
      print("size of dim 1 {}".format(struct.unpack('i', curated[12:16])[0]))
      print("number of events detected: {}".format(nrecs))
    recsize=24  #note: doesn't agree with value above  
    tindex = np.ndarray((nrecs,), '<d', curated, 28, (recsize,))
    cluster = np.ndarray((nrecs,), '<d', curated, 36, (recsize,))
    adj_index = tindex//128

   #print("tindex[] {}: cluster[] {}".format(tindex[i], cluster[i]))

    return tindex, cluster, adj_index
