import cv2
import common
import video
import math
import numpy as np


class Arena:
    width=580
    height=420
    pts_world=np.float32([[0,0],[width,0],[0,height],[width,height]])
    pts_arena=[]
 # transformation matrix
    tm=[]
    old_pts=[]
    old_tm=[]

    
    def crop_and_warp(s, img):
    # warps and crops an image so it's just the arena and a pixel is
    # a millimeter
        warpimg=cv2.warpPerspective(img,s.tm,(s.width,s.height))
        return(warpimg)


    def transform_point(s, x, y):
        pt=np.array([[x,y]])
        (nx,ny)=cv2.perspectiveTransform(pt, s.tm)
        return(nx,ny) 

    def update_location(s,corners):
        if (len(s.pts_arena)>0) :
           s.old_pts.append(s.pts_arena) 
           s.old_tm.append(s.tm) 
        s.pts_arena=corners
        s.tm = cv2.getPerspectiveTransform(s.pts_arena,s.pts_world)

