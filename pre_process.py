#!/usr/bin/python
import glob
import ConfigParser
import cv2
import common
import video
import math
import time
import sys
import numpy as np


def add_position(cfile, number, startframe):
   sectionstring=str(number)
   cfile.add_section(sectionstring)
   cfile.set(sectionstring,"startframe",startframe)
   cfile.set(sectionstring,"top_left_x",0)
   cfile.set(sectionstring,"top_left_y",0)
   cfile.set(sectionstring,"top_right_x",0)
   cfile.set(sectionstring,"top_right_y",0)
   cfile.set(sectionstring,"bottom_left_x",0)
   cfile.set(sectionstring,"bottom_left_y",0)
   cfile.set(sectionstring,"bottom_right_x",0)
   cfile.set(sectionstring,"bottom_right_y",0)
   cfile.set(sectionstring,"initial_slugx",0)
   cfile.set(sectionstring,"initial_slugy",0)

start_time=time.time()

# create a cfg file with the following kind of content (without the #):
#[s0]
#image_folder=/home/hmd1/data/lizzie/2016-10-19/
#frames_of_background=15 
#difference_threshold=30 
 
#call program with 
#python pre_process.py config-file-name

# it will create a new config file with information on frames where 
# there's camera shake


infilename=sys.argv[-1]


#read in the start config file, and copy across defaults to our new config
config = ConfigParser.ConfigParser()
config.add_section('s0') 
stconfig = ConfigParser.ConfigParser()
stconfig.read(infilename)
inputdir= stconfig.get('s0','image_folder')
config.set('s0','image_folder',inputdir)
print inputdir
fbuffer=stconfig.getint('s0','frames_of_background') 
config.set('s0','frames_of_background',fbuffer)
difference_thresh=stconfig.getint('s0','difference_threshold') 
config.set('s0','difference_threshold',difference_thresh) 

# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()
shakepics=[]

n=0 # frame number
pos=1 #position - incremented each time we get camera shake
img=cv2.imread(flist[0])
maxpix=img.size
camerashake_threshold=maxpix/16
grey= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
movingaverage=np.float32(grey)

print "we've a maximum of {}, threshold= {}".format(maxpix,camerashake_threshold)
shakepics.append(flist[0])
add_position(config,pos,1)

moving=False
for fname in flist:
#read a frame from the video capture obj 
    frame=cv2.imread(fname)
    grey= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#let's deal with that pesky zero case before we divide by fbuffer
    if fbuffer==0:
        fbuffer=1
    alpha=float(1.0/fbuffer)
    img_blur = cv2.GaussianBlur(grey, (5, 5), -1)
    cv2.accumulateWeighted(img_blur,movingaverage,alpha)
    res=cv2.convertScaleAbs(movingaverage)
    difference_img = cv2.absdiff(res, img_blur)
    ret,th1 = cv2.threshold(difference_img,difference_thresh,255,cv2.THRESH_BINARY)
    if (n>fbuffer):
        pixels_moving=np.sum(th1==255)
        if (pixels_moving > camerashake_threshold):
            if (moving==False):
               #we've just started moving
                config.set(str(pos),"endframe",n)
                moving=True;
            print "Shaky in Frame {} with {} moving pixels".format(n,pixels_moving) 
        else: 
            if (moving==True):
              # we've just become still after shake
                pos += 1
                shakepics.append(fname)
                add_position(config,pos,n)
                moving=False
    
        
    n+=1



config.set(str(pos),"endframe",n)
seconds=time.time()-start_time
print "Processed {} frames in {} seconds: {} fps".format(n,seconds,n/seconds)
with open('test.cfg', 'w') as configfile:
   config.write(configfile)
print "You're going to need to look at the following pictures and get arena position"
for pic in shakepics:
   print pic
print "A template has been saved as test.cfg - edit this and rename it"
