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
    tm=[]

    def __init__(s,dimensions):
    # set up arena transformation into approximate millimetres
        s.pts_arena=dimensions
        s.tm = cv2.getPerspectiveTransform(s.pts_arena,s.pts_world)
    
    def crop_and_warp(s, img):
        warpimg=cv2.warpPerspective(img,s.tm,(s.width,s.height))
        return(warpimg)
