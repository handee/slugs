#!/usr/bin/python
import glob
import ConfigParser
import cv2
import common
import video
import math
import sys 
import os
import glob
import csv
import numpy as np
from slug import Slug
from arena import Arena

#magic number to get rid of some baby slugs
slugsize=5
#total frames in trials is the length of the trials across all slug
#experiments
total_frames_in_trials=57595
#if it falls short of this, the program prints an error; if it over-runs
#then it cuts short at this number

#read in config file
current_config_file=sys.argv[-1]
setup_section='s0'
config = ConfigParser.ConfigParser()
config.read(current_config_file)
inputdir= config.get(setup_section,'image_folder')
print inputdir
fbuffer=config.getint(setup_section,'frames_of_background') 
difference_thresh=config.getint(setup_section,'difference_threshold') 
#inputdir should have a / at the end. check this is the case, also
#setup output directory to be inputdir_out
if (inputdir.endswith('/')):
   outputdir=inputdir[:-1]+"_out/"
else:
   outputdir=inputdir+"_out/"
   inputdir+='/'

# read directory, get list of files, sort
subdirs=glob.glob(inputdir+"*/")
flist=[]
for subdir in subdirs:
    sflist=glob.glob(subdir+"*.jpg")
    sflist.sort()
    flist=flist+sflist


print "Output will be saved to {}".format(outputdir)
# set up output dir if it doesn't exist
if not os.path.exists(outputdir):
    print "Creating directory now"
    os.makedirs(outputdir)

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
init_x=config.getint(cs,'initial_slugx') 
init_y=config.getint(cs,'initial_slugy') 
#set arena location
corners=np.float32([[atlx,atly],[atrx,atry],[ablx,ably],[abrx,abry]]) 
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
fn=outputdir+"initialisation_locations.jpg"
cv2.imwrite(fn,cornerim);

# warp image to arena coordinates
warp=a.crop_and_warp(img)
fn=outputdir+"initialdisks.jpg"
cv2.imwrite(fn,warp);

# set up background model
fgbg=cv2.createBackgroundSubtractorMOG2()
fgbg.setVarThreshold(difference_thresh) 

# set up initialisation for the slug
x,y=a.transform_point(init_x,init_y)
thisslug = Slug(a,x,y)
warplist=[]

for fname in flist:
#read a frame from the video capture obj 
     frame=cv2.imread(fname)
     warp=a.crop_and_warp(frame)
     # get the foreground (moving object) mask from our background model 
     fgmask=fgbg.apply(warp)
     # create a structuring element based on our slug size estimate
     element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(slugsize,slugsize))
     #remove tiny foreground blobs
     er=cv2.erode(fgmask,element,iterations=1); 
     # work out connected components (4-connected)
     connectivity = 4  
     ccraw= cv2.connectedComponentsWithStats(er, connectivity, cv2.CV_32S)
     # visualise what's going on    
     slugviz=warp.copy()
     if (n<=startframe):
        # we are in a shaky bit, don't bother tracking slugs but do store images
        # and update bg model
        print "In a shaky gap in frame {} waiting for frame {}".format(n,startframe)
        n+=1 
     else:
       # update the slug's location 
        num_labels,centroids,stats=thisslug.update_location(ccraw,n)    

        locs=thisslug.return_locations()

        
        thisslug.highlight(slugviz);
        thisslug.highlight_im(frame);
     fgimg=cv2.merge([er,er,fgmask])
     cv2.imshow('foregound',fgimg)
     cv2.imshow('slug',slugviz)
     cv2.imshow('unrectified',frame)

     #uncommment the next few lines if you want to save any foreground img
     #it needs an output directory called "out"
     #fn=outputdir+"foreground"+str(n).rjust(5,'0')+".png"
     #cv2.imwrite(fn,fgimg);

     # again uncomment if you want to save the transformed arena img
     #fn=outputdir+"slugviz"+str(n).rjust(5,'0')+".png"
     #cv2.imwrite(fn,slugviz);
  
     # saving warped ones for visualisation porpoises : these will be deleted at the end
     fn=outputdir+"warp"+str(n).rjust(5,'0')+".png"
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

     if (n > total_frames_in_trials):
        break
#open cv window management/redraw stuff
     ch = cv2.waitKey(5)
     if ch == 27:
        break

# storing final states
output=fgbg.getBackgroundImage()
fn=outputdir+"enddisks_bgmodel.png"
cv2.imwrite(fn,output)
fn=outputdir+"enddisks_raw.png"
cv2.imwrite(fn,warp)
thisslug.find_pauses()
thisslug.list_pauses()

# all processing done let's stick it all in a csv file


#for output filename we want to use the directory; for reading in we need a
#slash on the end, let's tidy this up a bit
outputcsvfile=outputdir+"pathdata.csv"
thisslug.write_trail_data_to_file(outputcsvfile,flist)

outputcsvfile=outputdir+"pauseoverview.csv"
thisslug.write_pause_data_to_file(outputcsvfile)

outputcsvfile=outputdir+"trailoverview.csv"
thisslug.write_trail_metadata_to_file(outputcsvfile)

outputcsvfile=outputdir+"shortsummary.csv"
thisslug.write_single_line_summary(outputcsvfile)

#save occupancy grid
ofn=outputdir+"occupancy.csv"
a.save_occupancy(ofn)
ofn=outputdir+"occupancy.png"
a.save_occupancy_image(ofn)
thisslug.visualise_pauses(warplist,outputdir)
thisslug.visualise_trails(output,warplist,outputdir)
cv2.destroyAllWindows()
#delete temporary warp images 
rmstring=outputdir+"warp*"
filelist = glob.glob(rmstring)
for f in filelist:
    os.remove(f)

if (n < total_frames_in_trials):
    print "This trial only had {} frames, and we expected {}".format(n,total_frames_in_trials)
print "All output files can be found in:"
print "    {}".format(outputdir)

