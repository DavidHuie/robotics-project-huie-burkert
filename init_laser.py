from servo_api import *
from thresh import get_item_rgb
import cv

CAMERA = 0 # use default camera
cam_capture = cv.CaptureFromCAM(CAMERA)

print "Point laser at board and press enter when ready to capture calibration image from cam."
dummy = raw_input()

# Acquire image
image = cv.QueryFrame(cam_capture)

print "Identify the laser."

LASER_R, LASER_G, LASER_B = get_item_rgb(image)

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
INIT_TILT_ANGLE = TILT_MIN

move(PAN_SERVO, INIT_PAN_ANGLE)
move(TILT_SERVO, INIT_TILT_ANGLE)

# Create callback that checks for laser
callback = lambda: check_for_color(LASER_R, LASER_G, LASER_B)

# Move tilt servo until laser is recorded and record the servo's position
INIT_TILT_ANGLE = move_until_callback(TILT_SERVO, callback, start_angle = INIT_TILT_ANGLE, end_angle = TILT_MAX)