# slugs
slug tracking for fun and profit

Note: the video and the common files come from the OpenCV Python Samples 

## Pre processing step

pre_process.py is the first stage. 

This takes as an argument a directory full of timelapse images. It goes through each image building a background subtraction model using a moving average. If there is significant camera shake it detects this. The output of pre_process.py is a file  called "test.cfg". This file is an empty config file, and what you have to do with this is to work out the corners of the arena and the initial location of the slug. You can do this in any drawing package (gimp, imageMagick display, probably even MS paint). 

You get to reinitialise every time there is camera shake, so  if there's no camera shake you only have to do this once. At the end of pre-processing the program will tell you what images you need to investigate e.g.

'You're going to need to look at the following pictures and get arena position
'/home/hannah/Videos/slugtest/2016-08-12-13-54-11-029.jpg
'/home/hannah/Videos/slugtest/2016-08-12-14-27-32-519.jpg
'A template has been saved as test.cfg - edit this and rename it

