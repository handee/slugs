#!/usr/bin/python
import glob
import cv2
import common
import video
import math
import numpy as np

 
# edit this line to point to the right directory of jpgs
#inputdir="/dcs/hmd1/data/lizzie/"
#inputdir="/home/hmd1/dcshome2/data/lizzie/"
inputdir="/home/hannah/Videos/lizzieslug/"
frames_of_background=15 # magic number: how many frames do we have in our
                        # moving average background model?
difference_thresh=30 # magic number: how different does the background
              #have to be before it counts as background?
 
###
#
# a function to prune the outputs of connected components, getting
# rid of those which are un-slug-like because they are too big 
#
###
def prune_outputs(o):
    # The first cell is the number of labels
    num_labels = o[0]
    # The second cell is the label matrix
    labels = o[1]
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
 
# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()

#give us a visualisation window or two
cv2.namedWindow('foregound')
cv2.namedWindow('input')
cv2.namedWindow('slug')

n=0
img=cv2.imread(flist[0])
movingaverage=np.float32(img)

for fname in flist:
#read a frame from the video capture obj 
    frame=cv2.imread(fname)
    fbuffer=frames_of_background
#let's deal with that pesky zero case before we divide by fbuffer
    if fbuffer==0:
        fbuffer=1
    alpha=float(1.0/fbuffer)
    img_blur = cv2.GaussianBlur(frame, (5, 5), -1)
# build the background model from the blurred input image
    cv2.accumulateWeighted(img_blur,movingaverage,alpha)
# convert to absolute values and uint8, show it in a little window 
    res=cv2.convertScaleAbs(movingaverage)
    tmp= cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
    cv2.imshow('input', tmp)

# take the absolute difference of the background and the input
    difference_img = cv2.absdiff(res, img_blur)
# make that greyscale
    grey_difference_img = cv2.cvtColor(difference_img, cv2.COLOR_BGR2GRAY)
# threshold it to get a motion mask
    ret,th1 = cv2.threshold(grey_difference_img,difference_thresh,255,cv2.THRESH_BINARY)
# if we've had enough frames of background then our motion estimate is probably stable...
    if (n>frames_of_background):
 
        # create a 5x5 elipptical structuring element
        element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        #remove tiny foreground blobs
        er=cv2.erode(th1,element,iterations=1); 
        # work out connected components (4-connected)
        connectivity = 4  
        ccraw= cv2.connectedComponentsWithStats(er, connectivity, cv2.CV_32S)
   
        # now we can cut down our guess of slug location by ignoring the really
        # massive components - if there's camera shake, or something like that
        # it'll give us a completely foreground object. cc will
        # also return a component that represents "background" so we need
        # to lose that. 
        num_labels,centroids,stats=prune_outputs(ccraw)    
        
        # The second cell is the label matrix
        labels = ccraw[1]
 
        out=cv2.merge([er,er,th1])
        for i in range(0,len(centroids)):
           cv2.circle(out,(int(centroids[i][0]),int(centroids[i][1])),2,(0,255,0),-1)
           print "i think we have a slug at {} {} in frame {}".format(centroids[i][0],centroids[i][1],n)
           # remember we need to adjust size estimates as we've shrunk 
           # everything by a pixel in order to get rid of small foreground
           # noise blobs
           print "it's location may be y= {} h = {} x= {} w={}".format(stats[i][1]-2,stats[i][3]+4,stats[i][0]-2,stats[i][2]+4)
           candidateslug=frame[stats[i][1]-2:stats[i][3]+stats[i][1]+2,stats[i][0]:stats[i][2]-2+stats[i][0]+2]
           #uncommment the next few lines if you want to save any slug img
           #it needs an output directory called "out"
           fn="out/slugf"+str(n).rjust(4,'0')+".png"
           cv2.imwrite(fn,candidateslug)
        if len(centroids)<1:
           print "the slug isn't moving in frame {}".format(n)
        cv2.imshow('foregound',out)
        #uncommment the next few lines if you want to save any foreground img
        #it needs an output directory called "out"
        fn="out/foreground"+str(n).rjust(4,'0')+".png"
        cv2.imwrite(fn,out);
    else: 
        cv2.imshow('input',th1) 

    n+=1


#open cv window management/redraw stuff
    ch = cv2.waitKey(5)
    if ch == 27:
        break
cv2.destroyAllWindows()


