#!/usr/bin/python
import glob
import ConfigParser
import cv2
import common
import video
import math
import numpy as np
from slug import Slug
from arena import Arena
current_config_file='slug2.cfg'


setup_section='s0'


config = ConfigParser.ConfigParser()
config.read(current_config_file)
inputdir= config.get(setup_section,'image_folder')
print inputdir
fbuffer=config.getint(setup_section,'frames_of_background') 
difference_thresh=config.getint(setup_section,'difference_threshold') 

# read directory, get list of files, sort
flist=glob.glob(inputdir+"*.jpg")
flist.sort()

#give us a visualisation window or two
cv2.namedWindow('foregound')
cv2.namedWindow('slug')
cv2.namedWindow('warp')

camerashakes=config.sections() # camera shake baby
camerashakes.remove('s0') #get rid of setup
camerashakes.sort()

n=0 # the first frame
a=Arena()
p=0 # the first camera position
cs=camerashakes[p]
# arena corners
atlx=config.getint(cs,'top_left_x') 
atly=config.getint(cs,'top_left_y') 
atrx=config.getint(cs,'top_right_x') 
atry=config.getint(cs,'top_right_y') 
ablx=config.getint(cs,'bottom_left_x') 
ably=config.getint(cs,'bottom_left_y') 
abrx=config.getint(cs,'bottom_right_x') 
abry=config.getint(cs,'bottom_right_y') 
endframe=config.getint(cs,'endframe') 
startframe=config.getint(cs,'startframe') 
corners=np.float32([[atlx,atly],[atrx,atry],[ablx,ably],[abrx,abry]]) 

a.update_location(corners);
img=cv2.imread(flist[0])
grey=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
warp=a.crop_and_warp(grey)
overrim=warp
movingaverage=np.float32(warp)
thisslug = Slug(a)
warplist=[]

for fname in flist:
    if (n<startframe):
       print "In a shaky gap in frame {} waiting for frame {}".format(n,startframe)
       n+=1 
    else:
#read a frame from the video capture obj 
        frame=cv2.imread(fname)
    # make that greyscale
        grey=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        warp=a.crop_and_warp(grey)
        cv2.imshow('warp',warp)
        if fbuffer==0:
            fbuffer=1
        alpha=float(1.0/fbuffer)
        img_blur = cv2.GaussianBlur(warp, (5, 5), -1)
    # build the background model from the blurred input image
        cv2.accumulateWeighted(img_blur,movingaverage,alpha)
    # convert to absolute values and uint8
        res=cv2.convertScaleAbs(movingaverage)
    # take the absolute difference of the background and the input
        difference_img = cv2.absdiff(res, img_blur)
    # threshold it to get a motion mask
        ret,th1 = cv2.threshold(difference_img,difference_thresh,255,cv2.THRESH_BINARY)
        if (startframe-n==fbuffer): 
            fn="out/startdisks{}.png".format(p)
            cv2.imwrite(fn,movingaverage)
# if we've had enough frames of background then our motion estimate is probably stable...
        if (n>fbuffer):
        
            # create a 5x5 elipptical structuring element
            element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
            #remove tiny foreground blobs
            er=cv2.erode(th1,element,iterations=1); 
            # work out connected components (4-connected)
            connectivity = 4  
            ccraw= cv2.connectedComponentsWithStats(er, connectivity, cv2.CV_32S)
       
            num_labels,centroids,stats=thisslug.update_location(ccraw,n)    
            
            out=cv2.merge([er,er,th1])
            slugviz=cv2.merge([warp,warp,warp])
            thisslug.highlight(slugviz);
            cv2.imshow('foregound',out)
            cv2.imshow('slug',slugviz)
       #uncommment the next few lines if you want to save any foreground img
       #it needs an output directory called "out"
       #fn="out/foreground"+str(n).rjust(4,'0')+".png"
       #cv2.imwrite(fn,out);
        
       #fn="out/slugviz"+str(n).rjust(4,'0')+".png"
       #cv2.imwrite(fn,slugviz);
        fn="out/warp{}.png".format(n,"03")
        cv2.imwrite(fn,warp) 
        warplist.append(fn)
    #let's deal with that pesky zero case before we divide by fbuffer
            
        n+=1
    if (n>=endframe):
        p+=1 # the next camera position
        print "position {}".format(p)
        print "len {}".format(len(camerashakes))
        if (p>=len(camerashakes)):
            print "breaking"
            break
        cs=camerashakes[p]
    # arena corners
        atlx=config.getint(cs,'top_left_x') 
        atly=config.getint(cs,'top_left_y') 
        atrx=config.getint(cs,'top_right_x') 
        atry=config.getint(cs,'top_right_y') 
        ablx=config.getint(cs,'bottom_left_x') 
        ably=config.getint(cs,'bottom_left_y') 
        abrx=config.getint(cs,'bottom_right_x') 
        abry=config.getint(cs,'bottom_right_y') 
        startframe=config.getint(cs,'startframe') 
        endframe=config.getint(cs,'endframe') 
        corners=np.float32([[atlx,atly],[atrx,atry],[ablx,ably],[abrx,abry]]) 

        a.update_location(corners);


#open cv window management/redraw stuff
    ch = cv2.waitKey(5)
    if ch == 27:
        break
output=cv2.merge([movingaverage,movingaverage,movingaverage])
thisslug.visualise_trails(output,warplist)
fn="out/andthatsallfolks.png"
cv2.imwrite(fn,overrim)
fn="out/enddisks.png"
cv2.imwrite(fn,movingaverage)
cv2.destroyAllWindows()


