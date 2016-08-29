#!/usr/bin/python
import glob
import cv2
import common
import video
import math
import numpy as np


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
  
# edit this line to point to the right directory of jpgs
#inputdir="/dcs/hmd1/data/lizzie/"
#inputdir="/home/hmd1/dcshome2/data/lizzie/"
inputdir="/home/hannah/Videos/lizzieslug/"
frames_of_background=15 # magic number: how many frames do we have in our
                        # moving average background model?

# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()

#give us a visualisation window or two
cv2.namedWindow('foregound')
cv2.namedWindow('input')
cv2.namedWindow('slug')

# trackbar related function
def nothing(*arg):
    pass

#cv2.createTrackbar('Size of buffer', 'foreground', frames_of_background, 250, nothing)
#cv2.createTrackbar('Difference threshold', 'foreground', 30, 200, nothing)

n=0
img=cv2.imread(flist[0])
movingaverage=np.float32(img)

for fname in flist:
#read a frame from the video capture obj 
    frame=cv2.imread(fname)
#check the trackbars to see if the default background model length has changed
    #fbuffer=cv2.getTrackbarPos('Size of buffer', 'foreground')
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
# threshold this to find foreground objects
    #difference_thresh=cv2.getTrackbarPos('Difference threshold', 'foreground')
    difference_thresh=30
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
        # it'll give us a completely foreground object. connected components will
        # also return a component that represents "background". 
        num_labels,centroids,stats=prune_outputs(ccraw)    
        
        # The second cell is the label matrix
        labels = ccraw[1]
 
        out=cv2.merge([er,er,th1])
        for point in centroids:
           cv2.circle(out,(int(point[0]),int(point[1])),2,(0,255,0),-1)
           print "i think we have a slug at {} {} in frame {}".format(point[0],point[1],n)
        if len(centroids)<1:
           print "the slug isn't moving in frame {}".format(n)
        cv2.imshow('foregound',out)
    else: 
        cv2.imshow('input',th1) 

#uncommment the next few lines if you want to save the output
#    fn="out/bgmovingav_big"+str(n).rjust(4,'0')+".png"
#    cv2.imwrite(fn,th1);
#    fn="out/bgmovingav_bg_big"+str(n).rjust(4,'0')+".png"
#    cv2.imwrite(fn,res);
    n+=1


#open cv window management/redraw stuff
    ch = cv2.waitKey(5)
    if ch == 27:
        break
cv2.destroyAllWindows()


