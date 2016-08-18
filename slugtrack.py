#!/usr/bin/python
import glob
import cv2
import common
import video
import numpy as np


# edit this line to point to the right directory of jpgs
#inputdir="/dcs/hmd1/data/lizzie/"
#inputdir="/home/hmd1/dcshome2/data/lizzie/"
inputdir="/home/hannah/Videos/lizzieslug/"


# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()

#give us a visualisation window or two
cv2.namedWindow('input')
cv2.namedWindow('bgmodel')
cv2.namedWindow('foregound')
cv2.namedWindow('input')

def nothing(*arg):
    pass
cv2.createTrackbar('Size of buffer', 'bgmodel', 110, 500, nothing)
cv2.createTrackbar('Difference threshold', 'bgmodel', 10, 200, nothing)



n=0
img=cv2.imread(flist[0])
movingaverage=np.float32(img)

for fname in flist:
    frame=cv2.imread(fname)
    cv2.imshow('input',frame)


#read a frame from the video capture obj
    fbuffer=cv2.getTrackbarPos('Size of buffer', 'bgmodel')
#let's deal with that pesky zero case before we divide by fbuffer
    if fbuffer==0:
        fbuffer=1
    alpha=float(1.0/fbuffer)
    img_blur = cv2.GaussianBlur(frame, (5, 5), -1)

    cv2.accumulateWeighted(img_blur,movingaverage,alpha)

# do the drawing stuff
    res=cv2.convertScaleAbs(movingaverage)
# show the background model
    cv2.imshow('bgmodel', res)

#resize the input just so i can have a smaller window and still show the input
#on a little laptop screen
    tmp= cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
    cv2.imshow('input', tmp)

# take the absolute difference of the background and the input
    difference_img = cv2.absdiff(res, img_blur)
# make that greyscale

    grey_difference_img = cv2.cvtColor(difference_img, cv2.COLOR_BGR2GRAY)
# threshold it to get a motion mask
    difference_thresh=cv2.getTrackbarPos('Difference threshold', 'bgmodel')
    ret,th1 = cv2.threshold(grey_difference_img,difference_thresh,255,cv2.THRESH_BINARY)
    cv2.imshow('foregound',th1)

#uncommment the next few lines if you want to save the output
#    fn="out/bgmovingav_big"+str(n).rjust(4,'0')+".png"
#    cv2.imwrite(fn,th1);
#    fn="out/bgmovingav_bg_big"+str(n).rjust(4,'0')+".png"
#    cv2.imwrite(fn,res);
    n+=1
    print n


#open cv window management/redraw stuff
    ch = cv2.waitKey(5)
    if ch == 27:
        break
cv2.destroyAllWindows()


