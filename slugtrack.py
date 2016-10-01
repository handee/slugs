#!/usr/bin/python
import glob
import cv2
import common
import video
import math
import numpy as np
from slug import Slug
 
# edit this line to point to the right directory of jpgs
#inputdir="/dcs/hmd1/data/lizzie/"
#inputdir="/home/hmd1/dcshome2/data/lizzie/"
#inputdir="/home/hannah/Videos/lizzieslug/"
inputdir="/home/hannah/Videos/slugtest/"

frames_of_background=15 # magic number: how many frames do we have in our
                        # moving average background model?
difference_thresh=30 # magic number: how different does the background
              #have to be before it counts as background?
 
 
# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()

#give us a visualisation window or two
cv2.namedWindow('foregound')
cv2.namedWindow('slug')

n=0
img=cv2.imread(flist[0])
overrim=img
movingaverage=np.float32(img)
thisslug = Slug()

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
# convert to absolute values and uint8
    res=cv2.convertScaleAbs(movingaverage)
# take the absolute difference of the background and the input
    difference_img = cv2.absdiff(res, img_blur)
# make that greyscale
    grey_difference_img = cv2.cvtColor(difference_img, cv2.COLOR_BGR2GRAY)
# threshold it to get a motion mask
    ret,th1 = cv2.threshold(grey_difference_img,difference_thresh,255,cv2.THRESH_BINARY)
    if (n==15): 
        fn="out/startdisks.png"
        cv2.imwrite(fn,movingaverage)
# if we've had enough frames of background then our motion estimate is probably stable...
    if (n>frames_of_background):
        
        # create a 5x5 elipptical structuring element
        element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        #remove tiny foreground blobs
        er=cv2.erode(th1,element,iterations=1); 
        # work out connected components (4-connected)
        connectivity = 4  
        ccraw= cv2.connectedComponentsWithStats(er, connectivity, cv2.CV_32S)
   
        num_labels,centroids,stats=thisslug.update_location(ccraw,n)    
        
        out=cv2.merge([er,er,th1])
        cv2.imshow('foregound',out)
        #uncommment the next few lines if you want to save any foreground img
        #it needs an output directory called "out"
        fn="out/foreground"+str(n).rjust(4,'0')+".png"
        cv2.imwrite(fn,out);
    
        
    n+=1


#open cv window management/redraw stuff
    ch = cv2.waitKey(5)
    if ch == 27:
        break

thisslug.visualise_trails(movingaverage)
fn="out/andthatsallfolks.png"
cv2.imwrite(fn,overrim)
fn="out/enddisks.png"
cv2.imwrite(fn,movingaverage)
cv2.destroyAllWindows()


