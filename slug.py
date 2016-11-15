
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
    ar=[]
    def __init__(s,a):
        ar=a

    def update_location(s, o, n):
        num_blobs,centroids,stats=s.prune_outputs(o)    
        if len(centroids)<1:
           if s.still==False:
              print "Adding a slugtrail to our trails"
               # the slug has just stopped
              s.slugtrails.append(list(s.currentslugtrail))
              del s.currentslugtrail[:]
              s.still=True
        if (len(centroids)>=1):
           if (len(centroids)==1):
              i=0
           else:
               mindist=100000
               closest=0
               for i in range(0, len(centroids)):
                  print "{} candidate at {} {}, left {} top {} width {} height {} area {}".format(n, centroids[i][0], centroids[i][1], stats[i][0], stats[i][1], stats[i][2], stats[i][3], stats[i][4])
                  dslug=((centroids[i][0]-s.lastslugx)* (centroids[i][0]-s.lastslugx) + (centroids[i][1]-s.lastslugy)* (centroids[i][1]-s.lastslugy)) 
                  if (dslug<mindist):
                     mindist=dslug
                     closest=i
                  print "mindist {} dslug {} closest: {}  i: {}".format(mindist,dslug,closest,i)
                  print "lastslugx {} lastslugy {} ".format(s.lastslugx, s.lastslugy)

           
           s.slugx=centroids[i][0]
           s.slugy=centroids[i][1]
           print "settled on {} {}".format(s.slugx,s.slugy)
           s.currentslugtrail.append([n,s.slugx,s.slugy])
           s.lastslugx=s.slugx
           s.lastslugy=s.slugy
           s.still=False

        # by the time we get to this stage, num_blobs should be 1!
        return(num_blobs, centroids, stats)

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
        num_blobs=len(newcentroids) 
        return(num_blobs, newcentroids, newstats)


    def highlight(s,img):
        if (s.still):
           cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(0,0,255),-1)
        else:
           cv2.circle(img,(int(s.slugx),int(s.slugy)),2,(0,255,0),-1)
        return img

# takes the slug trails as a set and draws the pics    
    def visualise_trails(s,movingav,filelist):    
        print "Going to visualise {} slugtrails now".format(len(s.slugtrails))
        overim=movingav.copy()
        for currenttrail in s.slugtrails:
           if (len(currenttrail)>3):
               currim=cv2.imread(filelist[currenttrail[0][0]])
               for point in currenttrail:
                   cv2.circle(currim,(int(point[1]),int(point[2])),2,(255,0,0),-1)
                   cv2.circle(overim,(int(point[1]),int(point[2])),2,(255,0,0),-1)
               cv2.circle(currim,(int(currenttrail[-1][1]),int(currenttrail[-1][2])),2,(0,0,255),2)
               cv2.circle(currim,(int(currenttrail[0][1]),int(currenttrail[0][2])),2,(0,255,0),2)
               cv2.circle(overim,(int(currenttrail[-1][1]),int(currenttrail[-1][2])),2,(0,0,255),2)
               cv2.circle(overim,(int(currenttrail[0][1]),int(currenttrail[0][2])),2,(0,255,0),2)
               fn="out/trail{}.png".format(currenttrail[0][0],'03')
               cv2.imwrite(fn,currim)
        fn="out/alltrails{}.png".format(currenttrail[0][0],'03')
        cv2.imwrite(fn,overim)
 
         
