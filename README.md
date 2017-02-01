# slugs
slug tracking for fun and profit

Note: the video and the common files come from the OpenCV Python Samples 

## Pre processing step

pre_process.py is the first stage. 

This takes as an argument a directory full of timelapse images. It goes through each image building a background subtraction model using a moving average. If there is significant camera shake it detects this. The output of pre_process.py is a file  called "test.cfg". This file is an empty config file, and what you have to do with this is to work out the corners of the arena and the initial location of the slug. You can do this in any drawing package (gimp, imageMagick display, probably even MS paint). 

You get to reinitialise every time there is camera shake, so  if there's no camera shake you only have to do this once. At the end of pre-processing the program will tell you what images you need to investigate e.g.

```
You're going to need to look at the following pictures and get arena position
/home/hannah/Videos/slugtest/2016-08-12-13-54-11-029.jpg
/home/hannah/Videos/slugtest/2016-08-12-14-27-32-519.jpg
A template has been saved as test.cfg - edit this and rename it
```

Open the files in whatever image editor you want, and work out where the corners and the slug are.  This might be tricky - sometimes you have to go forwards through the sequence to work out where the slug is, and sometimes it starts in a shelter so is not visible. In these occasions I have just marked a location in the shelter. If you are not 100% sure where the corners are as they are not actually that clear, just have a guess. These are used to convert image locations to approximate centimetre locations so are important, but being a few pixels out is not going to alter things noticably. The key thing is to get the whole arena. Here's an example where I have marked slug location with green/white dot (actually, slug not visible as in shelter - I looked forward in the seq to see where she emerged) and corners with blue/white dots. 


![Example slug locations illustratoin](https://raw.githubusercontent.com/handee/slugs/master/annotated.jpg)


A final config file will look a little something like this:

```
[s0]
image_folder = /home/hannah/Videos/5%/one/5%_1_1/2016-11-11/
frames_of_background = 15
difference_threshold = 30

[1]
startframe = 0
top_left_x = 55
top_left_y = 25
top_right_x = 495
top_right_y = 20
bottom_left_x = 44
bottom_left_y = 333
bottom_right_x = 501
bottom_right_y = 334
initial_slugx = 80
initial_slugy = 174
endframe = 5930 
```
