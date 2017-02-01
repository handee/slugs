#!/usr/bin/python
import glob
import ConfigParser
import cv2
import common
import video
import math
import sys 
import os
import csv
import numpy as np
from slug import Slug
from arena import Arena

#read in config file
current_config_file=sys.argv[-1]
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

# set up temporary output dir "out" if it doesn't exist
if not os.path.exists("out"):
    os.makedirs("out")

#give us a visualisation window or two
cv2.namedWindow('foregound')
cv2.namedWindow('slug')
cv2.namedWindow('unrectified')

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
init_x=config.getint(cs,'initial_slugx') 
init_y=config.getint(cs,'initial_slugy') 

a.update_location(corners);
img=cv2.imread(flist[0])

# save corner image for visualisation purposes
cornerim=img.copy()
cv2.circle(cornerim, (atrx,atry), 4, (255,0,0), -1)
cv2.circle(cornerim, (atrx,atry), 1, (255,255,255), -1)
cv2.circle(cornerim, (abrx,abry), 4, (255,0,0), -1)
cv2.circle(cornerim, (abrx,abry), 1, (255,255,255), -1)
cv2.circle(cornerim, (ablx,ably), 4, (255,0,0), -1)
cv2.circle(cornerim, (ablx,ably), 1, (255,255,255), -1)
cv2.circle(cornerim, (atlx,atly), 4, (255,0,0), -1)
cv2.circle(cornerim, (atlx,atly), 1, (255,255,255), -1)
cv2.circle(cornerim, (init_x,init_y), 4, (0,255,0), -1)
cv2.circle(cornerim, (init_x,init_y), 1, (255,255,255), -1)
fn="out/initialisation_locations.jpg"
cv2.imwrite(fn,cornerim);


# set up background model
warp=a.crop_and_warp(img)
overrim=warp
fgbg=cv2.createBackgroundSubtractorMOG2()
fgbg.setVarThreshold(difference_thresh) 

# set up initialisation for the slug
x,y=a.transform_point(init_x,init_y)
thisslug = Slug(a,x,y)
warplist=[]

for fname in flist:
    if (n<startframe+2):
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

        locs=thisslug.return_locations()

        
        # visualise what's going on    
        out=cv2.merge([er,er,fgmask])
        slugviz=warp.copy()
        thisslug.highlight(slugviz);
        thisslug.highlight_im(frame);
        cv2.imshow('foregound',out)
        cv2.imshow('slug',slugviz)
        cv2.imshow('unrectified',frame)

        #uncommment the next few lines if you want to save any foreground img
        #it needs an output directory called "out"
        #fn="out/foreground"+str(n).rjust(4,'0')+".png"
        #cv2.imwrite(fn,out);

        # again uncomment if you want to save the transformed arnea img
        #fn="out/slugviz"+str(n).rjust(4,'0')+".png"
        #cv2.imwrite(fn,slugviz);
  
        # saving warped ones for visualisation porpoises
        fn="out/warp"+str(n).rjust(4,'0')+".png"
        cv2.imwrite(fn,warp) 

        #keeping filelist of the warped ones - enables us to see what is
        #happening at key times e.g. before a slug visited a leaf disk
        warplist.append(fn)
            
        n+=1
    if (n>=endframe): #we are past the end of that shaky bit so it's all moved
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

# storing final states
output=fgbg.getBackgroundImage()
fn="out/enddisks_bgmodel.png"
cv2.imwrite(fn,output)
fn="out/enddisks_raw.png"
cv2.imwrite(fn,warp)
thisslug.find_pauses()
thisslug.list_pauses()

# all processing done let's stick it all in a csv file


#for output filename we want to use the directory; for reading in we need a
#slash on the end, let's tidy this up a bit
if (inputdir.endswith('/')):
   outputcsvfile=inputdir[:-1]+".csv"
else:
   outputcsvfile=inputdir+".csv"
   inputdir+='/'

with open(outputcsvfile, 'a+') as f:
   csvwrite=csv.writer(f)
   csvwrite.writerow(["filename","Image x","Image y","Kalman image x","Kalman image y","Arena x","Arena y","Kalman arena x","Kalman arena y", "Still"])


with open(outputcsvfile, 'a+') as f:
   csvwrite=csv.writer(f)
   for i in range(0,n-5):  # last 5 frames are dodge
       d=thisslug.getrow(i) 
       print "{} = i {} = d {} = n".format(i,d,n)
       row=(flist[i],d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8])
       csvwrite.writerow(row)

thisslug.visualise_pauses(warplist)
thisslug.visualise_trails(output,warplist)
cv2.destroyAllWindows()


