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

#call program with 
#python pre_process.py directorycontainingimages 

# it will create a new config file with information on frames where 
# there's camera shake


# get input directory and check there's a / on the end
inputdir=sys.argv[-1]
if (inputdir.endswith('/')):
    print inputdir
else:
    inputdir+='/'
    print inputdir


#create defaults for our new config file
config = ConfigParser.ConfigParser()
config.add_section('s0') 
config.set('s0','image_folder',inputdir)
fbuffer=15
config.set('s0','frames_of_background',fbuffer)
difference_thresh= 30
config.set('s0','difference_threshold',difference_thresh) 

# read directory, get list of files, sort
subdirs=glob.glob(inputdir+"*/")
flist=[]
for subdir in subdirs:
    sflist=glob.glob(subdir+"*.jpg")
    sflist.sort()
    flist=flist+sflist
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
add_position(config,pos,0) #add the starting position

moving=False
for fname in flist:
#read a frame 
    frame=cv2.imread(fname)
#let's deal with that pesky zero case before we divide by fbuffer
    if fbuffer==0:
        fbuffer=1
    alpha=float(1.0/fbuffer)
  # greyscale it, blur it, add it to the moving average, scale it
    grey= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(grey, (5, 5), -1)
    cv2.accumulateWeighted(img_blur,movingaverage,alpha)
    res=cv2.convertScaleAbs(movingaverage)
# get a difference image between input and average
    difference_img = cv2.absdiff(res, img_blur)
 # threshold and count the # of pixels which differ from the bg
    ret,th1 = cv2.threshold(difference_img,difference_thresh,255,cv2.THRESH_BINARY)
    if (n>fbuffer):
        pixels_moving=np.sum(th1==255)
        if (pixels_moving > camerashake_threshold):
            if (moving==False):
               #we've just started moving
                config.set(str(pos),"endframe",n)
                moving=True;
            print "Shaky waky camera in frame {}, with {} moving pixels".format(n,pixels_moving) 
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
