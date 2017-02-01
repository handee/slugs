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
    kslugx=0
    kslugy=0
    ikx=0
    iky=0
    ix=0
    iy=0
    currentslugtrail=[] # complete slug trail
    kalmanslugtrail=[] # complete kalman slug trail
    icurrentslugtrail=[] #image coords not arena coords
    ikalmanslugtrail=[] # image coords not arena coords
    kslug=[]
    slugstills=[]  # array of still locations, segmented
    slugtrails=[]  # array of trails, segmented
    slugmindist=20
    still=1 #is the slug still? (starts off still)
    ar=[] # arena
    smoothing_window=5 # for smoothing the stillness or otherwise; 
                       #it's an average
    def __init__(s,a,x,y):
        print "initialising at {},{}".format(x,y)
        s.ar=a
        s.lastslugx=x
        s.lastslugy=y
        s.slugx=x
        s.slugy=y

    def update_location(s, o, n):
        num_blobs,centroids,stats=s.prune_outputs(o)    
        if len(centroids)<1:
           print "no movement detected in frame {} ".format(n)
           s.slugx=s.lastslugx
           s.slugy=s.lastslugy
           if s.still==0:
               # the slug has just stopped
              s.still=1

        # take detected centroids, and trim; hopefully we end up
        # with just one detected motion patch but if we find more
        # find the closest to the last known slug position 
        if (len(centroids)>=1):
           print "movement detected in frame {} ".format(n)
           if (s.still==1):
              s.still=0
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
           s.lastslugx=s.slugx
           s.lastslugy=s.slugy
        # now s.slugx and s.slugy contain the slug's location
        s.currentslugtrail.append([n,s.slugx,s.slugy,s.still])
         
        #apply Kalman filter; not actually used but saved just in case it
        #turns out to be useful in the future
        slugloc=np.array([[np.float32(s.currentslugtrail[-1][1])],[np.float32(s.currentslugtrail[-1][2])]])
        s.kalman.correct(slugloc)
        s.kslug=s.kalman.predict()
        s.kslugx=int(s.kslug[0])
        s.kslugy=int(s.kslug[1])
        s.kalmanslugtrail.append((s.kslugx,s.kslugy))
      
        # transform back into image coords and save those as well
        s.ix,s.iy=s.ar.transform_point_to_image(s.slugx,s.slugy)
        s.ikx,s.iky=s.ar.transform_point_to_image(s.kslugx,s.kslugy)
        s.icurrentslugtrail.append((s.ix,s.iy))
        s.ikalmanslugtrail.append((s.ikx,s.iky))
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


    def return_locations(s):
        return ([s.slugx,s.slugy,s.kslugx,s.kslugy,s.ix,s.iy,s.ikx,s.iky])    

    # takes a box and a frame and looks back through history till it finds
    # the time and place that the slug was most recently not 
    # in that box. 
    # box is defined top-left-bottom-right
    # returns frame # of image where slug isn't in the box, or current frame 
    # if that doesn't happen
    def backtrack_out_of_box(s,box,frame):
       ret_val=frame
       inbox=True
       while inbox:
           if (s.point_in_box(box, s.currentslugtrail[frame][1],s.currentslugtrail[frame][2])): 
               frame-=1
           elif (frame<0):
               inbox=False
           else:
               ret_val=frame
               inbox=False
       return ret_val
 
    # takes a box and a frame and looks forward into future till it finds
    # the time and place that the slug will next not be
    # in that box. 
    # box is defined top-left-bottom-right
    # returns frame # of image where slug isn't in the box, or current frame 
    # if that doesn't happen
    def forwardtrack_out_of_box(s,box,frame):
       ret_val=frame
       inbox=True
       while inbox:
           if (s.point_in_box(box, s.currentslugtrail[frame][1],s.currentslugtrail[frame][2])): 
               frame+=1
           elif (frame>len(s.currentslugtrail)):
               inbox=False
           else:
               ret_val=frame
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
        cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(255,0,0),2)
        if (s.still):
           cv2.circle(img,(int(s.lastslugx),int(s.lastslugy)),2,(0,0,255),-1)
        else:
           cv2.circle(img,(int(s.slugx),int(s.slugy)),2,(0,255,0),-1)
        cv2.circle(img,(int(s.kslugx),int(s.kslugy)),2,(255,0,0),1)
        return img
 
    def highlight_im(s,img):
        cv2.circle(img,(int(s.ix),int(s.iy)),2,(255,0,0),2)
        if (s.still):
           cv2.circle(img,(int(s.ix),int(s.iy)),2,(0,0,255),-1)
        else:
           cv2.circle(img,(int(s.ix),int(s.iy)),2,(0,255,0),-1)
        cv2.circle(img,(int(s.ikx),int(s.iky)),2,(255,0,0),1)
        return img
 


# prints out all the times the slug was still
    def list_pauses(s):
        for pause in s.slugstills:
            print "Slug was still for {} frames starting {} at {},{}".format(pause[3],pause[0],pause[1],pause[2])

    def find_pauses(s):
        still = 1 #slug starts off still
        p=[0,0,0,0]
        s.smooth_still_estimate()
        st=[]
        for frame in s.currentslugtrail:
            n=0
            if (still==0 and frame[3]==1):
               print "it's just stopped"
               p[0]=frame[0]
               p[1]=frame[1]
               p[2]=frame[2]
               p[3]=0
               s.slugtrails.append(st)
               st=[]
            elif (still==1 and frame[3]==1):
               print "it's still"
               #pause[0]=frame[0]
               #it's been stopped for a bit, increment the counter
               p[3]+=1
            elif (still == 1 and frame[3]==0):
               print "it's startedupagain"
               #it's started moving again, store the pause info
               s.slugstills.append(p)
               p=[0,0,0,0]
               #also we're moving, append to the current slug trail
               st.append([frame[0],frame[1],frame[2]])
            else:
               #we're moving, append to the current slug trail
               st.append([frame[0],frame[1],frame[2]])
            still=frame[3]
        if (still==1):
           #we finished still so store it
           s.slugstills.append(p)
        else:
           s.slugtrails.append(st)
        n=n+1
    
            
    def smooth_still_estimate(s):
        l=int(math.floor(s.smoothing_window/2))
        t=len(s.currentslugtrail)
        tempstill=[]
        for i in range(0,l):
           tempstill.append(s.currentslugtrail[i][3])
        for i in range(0+l,t-l):
           current=0
           for j in range(i-l,i+l):
               current+=(s.currentslugtrail[j][3])
           if (current>l):
               tempstill.append(1)
           else:
               tempstill.append(0)
        for i in range(t-l,t):
           tempstill.append(s.currentslugtrail[i][3])
        for i in range(0,t-1):
           s.currentslugtrail[i][3]=tempstill[i]

 
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
            outofboxframeb=s.backtrack_out_of_box((plx,prx,pty,pby),pause[0])
            outofboxframea=s.forwardtrack_out_of_box((plx,prx,pty,pby),pause[0])
            print " slug stopped in {}, frame before {} frame after {}".format(pause[3], outofboxframeb, outofboxframea)
            startim=cv2.imread(ims[outofboxframeb])
            afterim=cv2.imread(ims[outofboxframea])
            cv2.rectangle(startim, (plx,pty), (prx,pby),(255,0,0),2)
            cv2.rectangle(afterim, (plx,pty), (prx,pby),(255,0,0),2)
            fn="out/stillbefore_{}.png".format(pause[0],'03')
            cv2.imwrite(fn,startim)
            fn="out/stillstart{}.png".format(pause[0],'03')
            cv2.imwrite(fn,currim)
            fn="out/stillforward{}.png".format(pause[0],'03')
            cv2.imwrite(fn,afterim)
#

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
 
        
    def getrow(s,n): 
       return(s.icurrentslugtrail[n][0],s.icurrentslugtrail[n][1],s.ikalmanslugtrail[n][0],s.ikalmanslugtrail[n][1],s.currentslugtrail[n][1],s.currentslugtrail[n][2],s.kalmanslugtrail[n][0],s.kalmanslugtrail[n][1],s.currentslugtrail[n][3])

