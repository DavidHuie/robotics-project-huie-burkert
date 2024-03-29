from servo_api import *
from thresh import get_item_rgb
#from whitemaze import center_of_mass
import cv
import json

CAMERA = 0 # use default camera
cam_capture = cv.CaptureFromCAM(CAMERA)

PAN_ANGLE = None
TILT_ANGLE = None

def move_laser_to_start(tilt_angle, pan_angle, tolerance):
    laser_x, laser_y = 1000, 0
    start_x, start_y = 0, 1000

    # we might need a None check here...

    # Orient vertically
    if start_y > laser_y:
        delta = 1
    else:
        delta = -1

    angle = tilt_angle
    while ( abs(start_y - laser_y) >= tolerance ):
        image =  cv.GetMat(cv.QueryFrame(cam_capture))

        laser_image = mark_pixels(image, LASER_R, LASER_G, LASER_B)
        start_image = mark_pixels(image, START_R, START_G, START_B)

        cv.ShowImage('laser', laser_image)
        cv.ShowImage('start', start_image)
        
        _, laser_y = center_of_mass(laser_image)
        _, start_y = center_of_mass(start_image)

        if laser_y is None or start_y is None:
            laser_y = float("infinity")
            start_y = 0
        
        angle = delta_move(TILT_SERVO, angle, delta = delta)

    global PAN_ANGLE
    PAN_ANGLE = angle

    print "Found Y"

    # Orient horizontally
    if start_x > laser_x:
        delta = -1
    else:
        delta = 1

    angle = pan_angle
    while ( abs(start_x - laser_x) >= tolerance ):
        image =  cv.GetMat(cv.QueryFrame(cam_capture))

        laser_image = mark_pixels(image, LASER_R, LASER_G, LASER_B)
        start_image = mark_pixels(image, START_R, START_G, START_B)
        
        laser_x, _ = center_of_mass(laser_image)
        start_x, _ = center_of_mass(start_image)

        if laser_x is None or start_x is None:
            laser_x = float("infinity")
            start_x = 0
        
        angle = delta_move(PAN_SERVO, angle, delta = delta)

    print "Found X"

    global TILT_ANGLE
    TILT_ANGLE = angle

def center_of_mass(marked):
	"""returns center of mass of marked pixels
	marked: matrix of marked pixels
	"""
	xtotal = 0
	ytotal = 0
	total = 0
	for i in range(marked.rows):
		for j in range(marked.cols):
			value = cv.Get2D(marked, i,j)
			if value[0] < 1:
				total += 1
				xtotal += j
				ytotal += i
	if total == 0:
		return None, None
	return (xtotal/total, ytotal/total)

def mark_pixels(image, R, G, B):
	copy = cv.CloneMat(image)
        check = lambda c, x: c[0] <= x <= c[1]

	for i in range(image.rows):
		for j in range(image.cols):
                    
			b,g,r,_ = cv.Get2D(image, i, j)
                        
			if check(B,b) and check(R,r) and check(G,g):
				cv.Set2D(copy, i, j, cv.RGB(0,0,0))			
			else:
				cv.Set2D(copy, i, j, cv.RGB(255,255,255))			
	return copy

def overlay_exists(mat, tolerance):
	laser_image = mark_pixels(mat, LASER_R, LASER_G, LASER_B)
	start_image = mark_pixels(mat, START_R, START_G, START_B)

	laser_x, laser_y = center_of_mass(laser_image)
	start_x, start_y = center_of_mass(start_image)
	
        if lazer_x is None or start_x is None:
            return False

        check = lambda x, y: (y - tolerance) < x < (y + tolerance)

        if (check(laser_x, start_x) and check(laser_y, start_y)):
            return True

        return False

print "Point laser at board and press enter when ready to capture calibration image from cam."
dummy = raw_input()

# Acquire image
image = cv.QueryFrame(cam_capture)

print "Identify the laser."

LASER_R, LASER_G, LASER_B = get_item_rgb(image)

print "Identify starting marker"

START_R, START_G, START_B = get_item_rgb(image)

print "Identify ending marker"

END_R, END_G, END_B = get_item_rgb(image)

print "Identify maze"

MAZE_R, MAZE_G, MAZE_B = get_item_rgb(image)

print "Identify grid"

GRID_R, GRID_G, GRID_B = get_item_rgb(image)

def check_for_color(r_range, g_range, b_range):
    image =  cv.GetMat(cv.QueryFrame(cam_capture))
    
    for i in range(image.rows):
            for j in range(image.cols):
                    b,g,r,_ = cv.Get2D(image, i, j)
                    
                    check = lambda c, x: c[0] <= x <= c[1]
                    
                    if check(r_range, r) and check(g_range, g) and check(b_range, b):
                        print "Found color"
                        return True
    return False

print "Press enter when ready for init step"
dummy = raw_input()

# Move servos to starting position
INIT_PAN_ANGLE = (PAN_MIN + PAN_MAX)/2
INIT_TILT_ANGLE = (TILT_MIN + TILT_MAX)/2

move(PAN_SERVO, INIT_PAN_ANGLE)
move(TILT_SERVO, INIT_TILT_ANGLE)

# Create callback that checks for laser
callback = lambda: check_for_color(LASER_R, LASER_G, LASER_B)

# Move tilt servo until laser is recorded and record the servo's position
INIT_TILT_ANGLE = move_until_callback(TILT_SERVO, callback, start_angle = INIT_TILT_ANGLE, end_angle = TILT_MAX)

move_laser_to_start(INIT_TILT_ANGLE, INIT_PAN_ANGLE, tolerance = 30)

data = { "laser": [LASER_R, LASER_G, LASER_B],
         "start": [START_R, START_G, START_B],
         "end": [END_R, END_G, END_B],
         "maze": [MAZE_R, MAZE_G, MAZE_B],
         "grid": [GRID_R, GRID_G, GRID_B],
         "pan_angle": PAN_ANGLE,
         "tilt_angle": TILT_ANGLE }

with open("data.json", 'w') as f:
    json.dump(data, f)
