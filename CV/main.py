import cv2
import numpy as np
import math
import copy
from imutils.perspective import four_point_transform
from imutils import contours
import imutils

ENABLE_DEBUG = 1

def showImage(caption, image):
    if ENABLE_DEBUG:
        cv2.namedWindow(caption, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(caption, 600,600)
        cv2.imshow(caption, image)

def imageScale(img, factor):
    return cv2.resize(img, (0,0), fx=factor, fy=factor)

def concat_tile(im_list_2d, scale):
    im_list_v = []
    for im_list_h in im_list_2d:
        newim_list_h = []
        for im_ in im_list_h:
            newim_list_h.append(imageScale(im_, scale))
        im_list_v.append(cv2.hconcat(newim_list_h))
    return cv2.vconcat(im_list_v)


def extractMaze(frame):
    frame_cpy = copy.deepcopy(frame)
    # Gray image op
    frame_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    frame_gray_gauss = cv2.GaussianBlur(frame_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh = cv2.threshold(frame_gray_gauss, 75, 255, cv2.THRESH_BINARY_INV)

    # extract the maze image only
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(contours, key=cv2.contourArea, reverse=True)
    displayCnt = None

    for c in cnts:
    	# approximate the contour
    	peri = cv2.arcLength(c, True)
    	approx = cv2.approxPolyDP(c, 0.02 * peri, True)

    	if len(approx) == 4:
            displayCnt = approx
            cv2.drawContours(frame, displayCnt, -1, (0,255,0), 3)
            showImage('approx', frame)
            break

    maze_extracted = four_point_transform(frame, displayCnt.reshape(4, 2))
    showImage('maze_extracted', maze_extracted)
    return maze_extracted

def mapMaze(frame):
    frame_cpy = copy.deepcopy(frame)

    maze_gray = cv2.cvtColor(frame,cv2.COLOR_RGB2GRAY)
    maze_gray_gauss = cv2.GaussianBlur(maze_gray,(5,5),cv2.BORDER_DEFAULT)
    # Inverting tholdolding will give us a binary image with a white wall and a black background.
    ret, thresh_maze = cv2.threshold(maze_gray_gauss, 60, 255, cv2.THRESH_BINARY_INV)
    # Kernel
    ke = 15
    kernel = np.ones((ke, ke), np.uint8)
    # Dilation
    dilation_maze = cv2.dilate(thresh_maze, kernel, iterations=1)
    # Erosion
    filtered_maze = cv2.erode(dilation_maze, kernel, iterations=1)

    showImage('filtered', filtered_maze)

    #assign grid to maze

    maze_pixel_height = filtered_maze.shape[0]
    maze_pixel_width  = filtered_maze.shape[1]

    pixel_step_size = 200

    grid_maze = filtered_maze

    #this is just for debug purpose -> not necessary to show in operation

    grid_maze = cv2.line(grid_maze,(0,100),(maze_pixel_width, 100),(169,169,169),1)
    grid_maze = cv2.line(grid_maze,(100,0),(100, maze_pixel_height),(169,169,169),1)
    
    # horizontal line
    # i = 0
    # for i in range(maze_pixel_height):
    #     grid_maze = cv2.line(grid_maze,(0,i),(maze_pixel_width, i),(169,169,169),1)
    #     i = i + pixel_step_size
    #
    # j = 0
    # for j in range(maze_pixel_width):
    #     grid_maze = cv2.line(grid_maze,(j,0),(j, maze_pixel_height),(169,169,169),1)
    #     j = j + pixel_step_size

    showImage('grid', grid_maze)

def detectBall(frame_out, frame_gray):
    # detect circles in the image
    circles = cv2.HoughCircles(frame_gray, cv2.HOUGH_GRADIENT, 1.2, 100)
    # ensure at least some circles were found
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")

        # loop over the (x, y) coordinates and radius of the circles
        for (x, y, r) in circles:
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv2.circle(frame_out, (x, y), r, (0, 255, 0), 4)
            cv2.rectangle(frame_out, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

        # show the output image
        # cv2.imshow("output", imageScale(np.hstack([frame, output]),scale))

def init_webCam():
    cam = cv2.VideoCapture(1)
    if not cam.isOpened():
        raise IOError("Cannot open webcam")
    return cam

def grab_webCam_feed(cam, mirror=False):
    ret_val, img = cam.read()
    if mirror:
        img = cv2.flip(img, 1)
    return img

def nothing(x):
    pass

def showUtilities(properties):
    # Create a black image, a window
    img = np.zeros((300,512,3), np.uint8)
    cv2.namedWindow('calibrate_window')
    # create trackbars for color change
    for prop in properties:
        cv2.createTrackbar(prop,'calibrate_window',0,255,nothing)

def obtainSlides(properties):
    vals = []
    for prop in properties:
        vals.append(cv2.getTrackbarPos(prop,'calibrate_window'))
    return vals

def main():
    ## MODE SELECTION ##
    #MODE = "CALIBRATION_HSV"
    #MODE = "TESTING_RUN"
    MODE = "TESTING_STATIC"

    ##### FOR TESTING RUN_TIME ######
    if "TESTING_RUN" == MODE:
        cam = init_webCam()
        while True:
            frame = grab_webCam_feed(cam, mirror=True)
            maze_lower_bound = [0,0,0]
            maze_upper_bound = [51,115,77]
            # detectMaze(frame, maze_lower_bound, maze_upper_bound, scale = 0.3)
            detectMazeV2(test_frame)
            if cv2.waitKey(1) == 27:
                break  # esc to quit
        cam.release() # kill camera

    ##### FOR TESTING STATIC ######
    elif "TESTING_STATIC" == MODE:
        while True:
            test_frame = cv2.imread('test1.png')

            # detectMaze(test_frame, blue_mount_lower_bound, blue_mount_bound)
            maze = extractMaze(test_frame)
            mapMaze(maze)

            if cv2.waitKey(1) == 27:
                break  # esc to quit

    ##### FOR CALIBRATION ######
    elif "CALIBRATION_HSV" == MODE:
        SLIDE_NAME = ['HL', 'SL', 'VL', 'H', 'S', 'V']
        showUtilities(SLIDE_NAME)
        while True:
            test_frame = cv2.imread('test1.png')
            [Hl_val,Sl_val,Vl_val,H_val,S_val,V_val] = obtainSlides(SLIDE_NAME)
            detectMaze(test_frame, [Hl_val,Sl_val,Vl_val], [H_val,S_val,V_val], ifdetectBall=False)
            if cv2.waitKey(1) == 27:
                break  # esc to quit

    cv2.destroyAllWindows() # close all windows


if __name__ == '__main__':
    main()
