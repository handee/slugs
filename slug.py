
import glob
import cv2
import common
import video
import math
import numpy as np

class Slug:

    lastslugx=0
    lastslugy=0
    slugx=0
    slugy=0
    currentslugtrail=[]
    slugtrails=[]
    still=False

    def update_location(s, o, n):
        num_labels,centroids,stats=s.prune_outputs(o)    
      
        if len(centroids)<1:
           if s.still==False:
               # the slug has just stopped
              s.slugtrails.append(list(s.currentslugtrail))
              del s.currentslugtrail[:]
              s.still=True
        else:
            s.slugx=centroids[0][0]
            s.slugy=centroids[0][1]
            s.currentslugtrail.append([n,s.slugx,s.slugy])
            s.lastslugx=s.slugx
            s.lastslugy=s.slugy
            s.still=False
        print "slug is at {} {}. We have {} trails. Still is {}".format(s.slugx, s.slugy, len(s.slugtrails), s.still)
        return(num_labels, centroids, stats)

###
#
# a function to prune the outputs of connected components, getting
# rid of those which are un-slug-like because they are too big 
#
###
    def prune_outputs(s,o):
        # The first cell is the number of labels
        num_labels = o[0]
        # The third cell is the stat matrix
        stats = o[2]
        # The fourth cell is the centroid matrix
        centroids = o[3]
        newcentroids=[]
        newstats=[]
        for i in range(0, num_labels):
            if not (math.isnan(centroids[i][0])):
                if (stats[i][4]<2000):
                    newcentroids.append(centroids[i])
                    newstats.append(stats[i])            

        return(num_labels, newcentroids, newstats)
# takes the slug trails and draws the pics    
    def visualise_trails(s,frame):    
        for currenttrail in s.slugtrails:
           currim=frame
           for point in currenttrail:
               cv2.circle(currim,(int(point[1]),int(point[2])),2,(255,0,0),-1)
               cv2.circle(currim,(int(currenttrail[-1][1]),int(currenttrail[-1][2])),2,(0,0,255),2)
               cv2.circle(currim,(int(currenttrail[0][1]),int(currenttrail[0][2])),2,(0,255,0),2)
           fn="out/trail"+str(currenttrail[0][0]).rjust(4,'0')+".png"
           cv2.imwrite(fn,currim)
     
