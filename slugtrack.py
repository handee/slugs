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
#current_config_file='short_test_seq.cfg'
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
#grey=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
warp=a.crop_and_warp(img)
overrim=warp
#movingaverage=np.float32(warp)
fgbg=cv2.createBackgroundSubtractorMOG2()
x=fgbg.getVarThreshold() 
print x
fgbg.setVarThreshold(difference_thresh) 
thisslug = Slug(a)
warplist=[]

for fname in flist:
    if (n<startframe):
       print "In a shaky gap in frame {} waiting for frame {}".format(n,startframe)
       n+=1 
    else:
#read a frame from the video capture obj 
        frame=cv2.imread(fname)
        warp=a.crop_and_warp(frame)
        # get the foreground (moving object) mask from our background model 
        fgmask=fgbg.apply(warp)
        # create a 5x5 eliptical structuring element
        element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
        #remove tiny foreground blobs
        er=cv2.erode(fgmask,element,iterations=1); 
        # work out connected components (4-connected)
        connectivity = 4  
        ccraw= cv2.connectedComponentsWithStats(er, connectivity, cv2.CV_32S)
        # update the slug's location 
        num_labels,centroids,stats=thisslug.update_location(ccraw,n)    
        
        # visualise what's going on    
        out=cv2.merge([er,er,fgmask])
        slugviz=warp.copy()
        thisslug.highlight(slugviz);
        cv2.imshow('foregound',out)
        cv2.imshow('slug',slugviz)
       #uncommment the next few lines if you want to save any foreground img
       #it needs an output directory called "out"
       #fn="out/foreground"+str(n).rjust(4,'0')+".png"
       #cv2.imwrite(fn,out);
        
        fn="out/slugviz"+str(n).rjust(4,'0')+".png"
        cv2.imwrite(fn,slugviz);
        fn="out/warp"+str(n).rjust(4,'0')+".png"
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
output=fgbg.getBackgroundImage()
fn="out/enddisks.png"
cv2.imwrite(fn,output)
thisslug.find_pauses()
thisslug.list_pauses()
thisslug.visualise_pauses(warplist)
#thisslug.visualise_trails(output,warplist)
cv2.destroyAllWindows()


