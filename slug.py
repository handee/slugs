import glob
import cv2
import common
import video
import math
import numpy as np

class Slug:
    kalman = cv2.KalmanFilter(4,2)
    kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]],np.float32)
    kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]],np.float32)
    kalman.processNoiseCov = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],np.float32) * 0.03

    lastslugx=0
    lastslugy=0
    slugx=0
    slugy=0
    currentslugtrail=[]
    kalmanslugtrail=[]
    kslug=[]
    slugstills=[]
    slugmindist=20
    still=False
    ar=[]
    def __init__(s,a):
        s.ar=a

    def update_location(s, o, n):
        num_blobs,centroids,stats=s.prune_outputs(o)    
        if len(centroids)<1:
           if s.still==False:
               # the slug has just stopped
              s.still=True
           s.currentslugtrail.append([n,s.lastslugx,s.lastslugy,s.still])
        if (len(centroids)>=1):
           if (s.still==True):
              s.still=False
           if (len(centroids)==1):
              closest=0
           else:
               mindist=100000
               closest=0
               for i in range(0, len(centroids)):
                  dslug=((centroids[i][0]-s.lastslugx)* (centroids[i][0]-s.lastslugx) + (centroids[i][1]-s.lastslugy)* (centroids[i][1]-s.lastslugy)) 
                  if (dslug<mindist):
                     mindist=dslug
                     closest=i

           s.slugx=centroids[closest][0]
           s.slugy=centroids[closest][1]
           s.currentslugtrail.append([n,s.slugx,s.slugy,s.still])
           s.lastslugx=s.slugx
           s.lastslugy=s.slugy

        # by the time we get to this stage, num_blobs should be 1!
        slugloc=np.array([[np.float32(s.currentslugtrail[-1][1])],[np.float32(s.currentslugtrail[-1][2])]])
        s.kalman.correct(slugloc)
        s.kslug=s.kalman.predict()
        s.kalmanslugtrail.append((int(s.kslug[0]),int(s.kslug[1])));
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
    

    # takes a box and a frame and looks back through history till it finds
    # the time and place that the slug was most recently not 
    # in that box. 
    # box is defined top-left-bottom-right
    # returns [t,x,y,m]; returns [0,0,0,0] if slug was never in box
    def backtrack_out_of_box(s,box,frame):
       ret_val=[0,0,0,0]
       inbox=True
       while inbox:
           if (s.point_in_box(box, s.currentslugtrail[frame][1],s.currentslugtrail[frame][2])): 
               frame-=1
           elif (frame<0):
               inbox=False
           else:
               ret_val=s.currentslugtrail[frame]
               inbox=False
       return ret_val
 
    # is a point in a box? True is yes, False is no
    def point_in_box(s,box,x,y):
       if ((x>box[0]) and (x<box[2]) and (y>box[1]) and (y<box[3])):
          return(True)
       else:
          return(False)
  

 
# draws a dot on the slug 
    def highlight(s,img):
        if (s.still):
           cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(255,0,0),2)
           cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(0,0,255),-1)
        else:
           cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(255,0,0),2)
           cv2.circle(img,(int(s.slugx),int(s.slugy)),2,(0,255,0),-1)
        cv2.circle(img,(int(s.kslug[0]),int(s.kslug[1])),2,(255,0,0),1)
        return img
 


# prints out all the times the slug was still
    def list_pauses(s):
        for pause in s.slugstills:
            print "Slug was still for {} frames starting {} at {},{}".format(pause[3],pause[0],pause[1],pause[2])

    def find_pauses(s):
        moving=False #slug starts off still
        p=[0,0,0,0]
        for frame in s.currentslugtrail:
            print frame
            if (moving==True and frame[3]==False):
               print "it's just stopped"
               p[0]=frame[0]
               p[1]=frame[1]
               p[2]=frame[2]
               p[3]=0
            elif (moving==False and frame[3]==False):
               print "it's still"
               #pause[0]=frame[0]
               #it's been stopped for a bit, increment the counter
               p[3]+=1
            elif (moving==False and frame[3]==True):
               print "it's startedupagain"
               #it's started moving again, store the pause info
               s.slugstills.append(p)
               p=[0,0,0,0]
            moving=frame[3]
        if (moving==False):
           #we finished still so store it
           s.slugstills.append(p)
    
            
 
# visualises all the times the slug was still
    def visualise_pauses(s,ims):
        w=15
        h=15
        for pause in s.slugstills:
            plx=int (pause[1]-w)
            prx=int (pause[1]+w)
            pty=int (pause[2]-h)
            pby=int (pause[2]+h)
            currim=cv2.imread(ims[pause[3]])
            if (plx<0): plx=0
            if (pty<0): pty=0
            if (prx>currim.shape[1]): prx=currim.shape[1]
            if (pby>currim.shape[0]): pby=currim.shape[0]
            cv2.rectangle(currim, (plx,pty), (prx,pby),(255,0,0),2)
            loc=s.backtrack_out_of_box((plx,prx,pty,pby),pause[0])
            start=loc[0]
            startim=cv2.imread(ims[start])
            cv2.rectangle(startim, (plx,pty), (prx,pby),(255,0,0),2)
            fn="out/stillb4{}.png".format(pause[0],'03')
            cv2.imwrite(fn,startim)
            fn="out/stillstart{}.png".format(pause[0],'03')
            cv2.imwrite(fn,currim)
            print "Slug was still for {} frames starting {} at {},{}".format(pause[3],pause[0],pause[1],pause[2])
#

# takes the slug trails as a set and draws the pics    
    #def visualise_trails(s,movingav,filelist):    
        #print "Going to visualise {} slugtrails now".format(len(s.slugtrails))
        #overim=movingav.copy()
        #for currenttrail in s.slugtrails:
           #if (len(currenttrail)>3):
               #currim=cv2.imread(filelist[currenttrail[0][0]])
               #for point in currenttrail:
                   #cv2.circle(currim,(int(point[1]),int(point[2])),2,(255,0,0),-1)
                   #cv2.circle(overim,(int(point[1]),int(point[2])),2,(255,0,0),-1)
               #cv2.circle(currim,(int(currenttrail[-1][1]),int(currenttrail[-1][2])),2,(0,0,255),2)
               #cv2.circle(currim,(int(currenttrail[0][1]),int(currenttrail[0][2])),2,(0,255,0),2)
               #cv2.circle(overim,(int(currenttrail[-1][1]),int(currenttrail[-1][2])),2,(0,0,255),2)
               #cv2.circle(overim,(int(currenttrail[0][1]),int(currenttrail[0][2])),2,(0,255,0),2)
               #fn="out/trail{}.png".format(currenttrail[0][0],'03')
               #cv2.imwrite(fn,currim)
        #fn="out/alltrails{}.png".format(currenttrail[0][0],'03')
        #cv2.imwrite(fn,overim)
 
         
