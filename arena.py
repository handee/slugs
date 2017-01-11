import cv2
import common
import video
import math
import numpy as np


# Arena class - holds information about the size of the arena
# and handles transformations from image coordinates to arena 
# coordinates.
# Can also backproject from arena coordinates to image coordinates.
# Uses simple perspective transform

class Arena:
    width=580 # width of arena in mm
    height=420 # height of arena in mm
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
        pt=np.array([[x,y]])
        (nx,ny)=cv2.perspectiveTransform(pt, s.tm)
        return(nx,ny) 

    def transform_point_to_image(s, x, y):
    # takes a point in arena coordinates and returns it to image coordinates
        pt=np.array([[x,y]])
        (nx,ny)=cv2.perspectiveTransform(pt, s.tmi)
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

