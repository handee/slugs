import cv2
import math
import numpy as np
import matplotlib.pyplot as plt



# Arena class - holds information about the size of the arena
# and handles transformations from image coordinates to arena 
# coordinates.
# Can also backproject from arena coordinates to image coordinates.
# Uses simple perspective transform

class Arena:
    width=580 # width of arena in mm
    height=420 # height of arena in mm
    occupancy=np.zeros((int(height/10), int(width/10)), dtype=np.int)
    pts_world=np.float32([[0,0],[width,0],[0,height],[width,height]])
    pts_arena=[]
# transformation matrix: image -> arena
    tm=[]
# transformation matrix inverse: arena -> image
    tmi=[]
    old_pts=[]
    old_tm=[]

    
    def crop_and_warp(s, img):
    # warps and crops an image so it's just the arena and a pixel is
    # a millimeter
        warpimg=cv2.warpPerspective(img,s.tm,(s.width,s.height))
        return(warpimg)


    def transform_point(s, x, y):
    # takes a point and puts it into arena coordinates
        pt=np.array([[x,y]], dtype=np.float32)
        pt=np.array([pt])
        a=cv2.perspectiveTransform(pt, s.tm)
        nx=a[0,0,0]
        ny=a[0,0,1]
        return(nx,ny) 

    def transform_point_to_image(s, x, y):
    # takes a point in arena coordinates and returns it to image coordinates
        pt=np.array([[x,y]], dtype=np.float32)
        pt=np.array([pt])
        a=cv2.perspectiveTransform(pt, s.tmi)
        nx=a[0,0,0]
        ny=a[0,0,1]
        return(nx,ny) 

    def update_location(s,corners):
    # updates arena corner location and (re)calculates transformation matrices
    # to be used at initialisation and upon camera shake
        if (len(s.pts_arena)>0) :
           s.old_pts.append(s.pts_arena) 
           s.old_tm.append(s.tm) 
        s.pts_arena=corners
        s.tm = cv2.getPerspectiveTransform(s.pts_arena,s.pts_world)
        s.tmi = cv2.getPerspectiveTransform(s.pts_world,s.pts_arena)


    def increment_occupancy(s,x,y):
        s.occupancy[int(y/10)][int(x/10)]+=1
    
    def save_occupancy(s,filename):
        np.savetxt(filename, s.occupancy, delimiter=',')
   
    def get_occupancy(s):
        return(s.occupancy)

    def save_occupancy_image(s, fn):
        logmat=np.where(s.occupancy>0, np.log(s.occupancy), 0)
        plt.imshow(logmat, cmap='hot', interpolation='nearest')
        fn2=fn+".log.png"
        plt.savefig(fn2)
        plt.imshow(s.occupancy, cmap='hot', interpolation='nearest')
        plt.savefig(fn)
