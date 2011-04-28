import cv
import thresh
import json
import servo_api
#import numpy
#import Image

BLACK_UPPER = cv.CV_RGB(120, 120, 100)
BLACK_LOWER = cv.CV_RGB(20,20,10)

YELLOW_UPPER = cv.CV_RGB(225,195,25)
YELLOW_LOWER = cv.CV_RGB(200,180,0)

RED_UPPER = cv.CV_RGB(255,215,185)
RED_LOWER = cv.CV_RGB(195,155,140)

TEST_UP = cv.CV_RGB(255,205,100)
TEST_LOW = cv.CV_RGB(125,125,0)
TOLERANCE = 50
LOWER = 30
UPPER = 120
x = 15







with open('data.json', 'r') as f:
	data = json.load(f)

[LASER_R, LASER_G, LASER_B] = data["laser"]
[START_R, START_G, START_B] = data["start"]
[END_R, END_G, END_B] = data["end"]
[MAZE_R, MAZE_G, MAZE_B] = data["maze"]
PAN_ANGLE = data["pan_angle"]
TILT_ANGLE = data["tilt_angle"]


def mark_pixels(image, lower, upper):
	"""
	returns a numpy array with pixels marked that are between the lower and upper rgb tolerances
	image: opencv matrix
	lower: lower tolerances
	upper: upper tolerances
	"""
	copy = cv.CloneMat(image)

	for i in range(image.rows):
		for j in range(image.cols):
			value = cv.Get2D(image, i, j)
			#print i,j,value
			if lower[0] < value[0] and lower[1] < value[1] and lower[2] < value[2] and upper[0] > value[0] and upper[1] > value[1] and upper[2] > value[2]:
				cv.Set2D(copy, i, j, cv.RGB(0,0,0))			
			else:
				cv.Set2D(copy, i, j, cv.RGB(255,255,255))			
	return copy

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

def has_won(mat, tolerance):
	redImage = mark_pixels(mat, RED_LOWER, RED_UPPER)
	yellowImage = mark_pixels(mat, YELLOW_LOWER, YELLOW_UPPER)

	redCenter = center_of_mass(redImage)
	yellowCenter = center_of_mass(yellowImage)
	
	if redCenter == None or yellowCenter == None:
		return False
	if redCenter[0] < yellowCenter[0] + tolerance and redCenter[1] < yellowCenter[1] + tolerance and redCenter[0] > yellowCenter[0] - tolerance and redCenter[1] > yellowCenter[1] - tolerance:
		return True
	else:
		return False 

def get_nearest_wall(mat,pixel, direction):
	"""finds nearest marked pixel
	mat: marked image matrix
	direction: NSEW"""
	counter = 1
	while True:
		if direction == "N":
			value = cv.Get2D(mat, pixel[0] - counter, pixel[1])
		if direction == "S":
			value = cv.Get2D(mat, pixel[0] + counter, pixel[1])
		if direction == "E":
			value = cv.Get2D(mat, pixel[0], pixel[1] + counter)
		if direction == "W":
			value = cv.Get2D(mat, pixel[0], pixel[1] - counter)

		if direction == "NW":
			value = cv.Get2D(mat, pixel[0] - counter, pixel[1] - counter)
		if direction == "SW":
			value = cv.Get2D(mat, pixel[0] + counter, pixel[1] - counter)
		if direction == "NE":
			value = cv.Get2D(mat, pixel[0] -  counter, pixel[1] + counter)
		if direction == "SE":
			value = cv.Get2D(mat, pixel[0] + counter, pixel[1] + counter)
		if value[0] < 1:
			return counter
		counter += 1

def return_right(orientation):
	if orientation == "N":
		return "NE"
	if orientation == "NE":
		return "E"
	if orientation == "E":
		return "SE"
	if orientation == "SE":
		return "S"
	if orientation == "S":
		return "SW"
	if orientation == "SW":
		return "W"
	if orientation == "W":
		return "NW"
	if orientation == "NW":
		return "N"
	return None

def return_right_angle(orientation):
	
	if orientation == "N":
		return "E"
	if orientation == "NE":
		return "SE"
	if orientation == "E":
		return "S"
	if orientation == "SE":
		return "SW"
	if orientation == "S":
		return "W"
	if orientation == "SW":
		return "NW"
	if orientation == "W":
		return "N"
	if orientation == "NW":
		return "NE"
	return None

def get_new_position(orientation, position):
	if orientation == "N":
		return (position[0] - x, position[1])
	if orientation == "NE":
		return (position[0] - x, position[1] + x)
	if orientation == "E":
		return (position[0], position[1]+x)
	if orientation == "SE":
		return (position[0]+ x, position[1] + x)
	if orientation == "S":
		return (position[0] +x, position[1])
	if orientation == "SW":
		return (position[0] + x , position[1] - x)
	if orientation == "W":
		return (position[0], position[1] -x)
	if orientation == "NW":
		return (position[0] - x, position[1] - x)
	return position

def move(orientation, position, counter, frontCounter, lower, upper):
	if frontCounter < lower or counter< lower:
	
		newOrientation = orientation
		for i in range(7):
			newOrientation = return_right(newOrientation)
		move_motor(newOrientation, position)
		return newOrientation
	if counter > lower and counter < upper:
		move_motor(orientation, position)
		return orientation
	if counter > upper:
		move_motor(return_right(orientation), position)
		return return_right(orientation)

def simulated_move(orientation, counter, frontCounter, lower, upper):
	if frontCounter < lower or counter< lower:
		newOrientation = orientation
		for i in range(7):
			newOrientation = return_right(newOrientation)
		return newOrientation
	if counter >= lower and counter <= upper:
		return orientation
	if counter > upper:
		return return_right(orientation)
	
def move_motor(direction, position):
	newPosition = get_new_position(direction, position)
	servo_api.move(1, newPosition)
	servo_api.move(2, newPosition)

def get_move(orientation, position, mat, redCenter):
	rightAngle = return_right_angle(orientation)
	distance = get_nearest_wall(mat, redCenter, rightAngle)
	frontDistance = get_nearest_wall(mat, redCenter, orientation)
	newOrientation = move(orientation, position, distance,frontDistance, LOWER, UPPER)
	return newOrientation, get_new_position(newOrientation, position)


def get_simulated_move(orientation, mat, redCenter, black):
	rightAngle = return_right_angle(orientation)
	distance = get_nearest_wall(black, redCenter, rightAngle)
	frontDistance = get_nearest_wall(black, redCenter, orientation)
	return simulated_move(orientation, distance, frontDistance, LOWER, UPPER)

def has_simulated_won(position, yellowCenter):
	if position == None or yellowCenter == None:
		return False
	if abs(position[0] - yellowCenter[0]) < TOLERANCE and abs(position[1] - yellowCenter[1]) < TOLERANCE:
		return True
	return False
def simulate(photo):
	mat = cv.LoadImageM(photo)
	print "Get Maze"
	maze = thresh.get_item_rgb(mat)
	BLACK_LOWER = cv.CV_RGB(maze[0][0]-2, maze[1][0]-2,maze[2][0]-2)
	BLACK_UPPER = cv.CV_RGB(maze[0][1]+2, maze[1][1]+2,maze[2][1]+2)
	print "Get End"
	maze = thresh.get_item_rgb(mat)
	YELLOW_LOWER = cv.CV_RGB(maze[0][0]-2, maze[1][0]-2,maze[2][0]-2)
	YELLOW_UPPER = cv.CV_RGB(maze[0][1]+2, maze[1][1]+2,maze[2][1]+2)
	print "Get Beginning"
	maze = thresh.get_item_rgb(mat)
	BLUE_LOWER = cv.CV_RGB(maze[0][0]-2, maze[1][0]-2,maze[2][0]-2)
	BLUE_UPPER = cv.CV_RGB(maze[0][1]+2, maze[1][1]+2,maze[2][1]+2)
	
	blue = mark_pixels(mat, BLUE_LOWER, BLUE_UPPER)
	yellow = mark_pixels(mat, YELLOW_LOWER, YELLOW_UPPER)
	black = mark_pixels(mat, BLACK_LOWER, BLACK_UPPER)
	end = center_of_mass(yellow)
	position = center_of_mass(blue)
	orientation = "N"
	print position, end
	while not has_simulated_won(position, end):
		print position, end
		orientation = get_simulated_move(orientation, mat, position, black)
		position = get_new_position(orientation, position)
		temp = cv.CloneMat(mat)
		cv.Circle(temp, position, 3, (255,0,0,0))
		cv.ShowImage("temp", temp)


#simulate("photo.JPG")
'''
camcapture = cv.CreateCameraCapture(0)
cv.SetCaptureProperty(camcapture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
cv.SetCaptureProperty(camcapture, cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

if not camcapture:
	print "ERROR"
	sys.exit(1)

frame = cv.QueryFrame(camcapture)
mat = cv.GetMat(frame)

values = thresh.get_item_rgb(mat)

BLACK_LOWER = cv.CV_RGB(MAZE_R[0]-2,MAZE_G[0]-2,MAZE_B[0]-2)
BLACK_UPPER = cv.CV_RGB(MAZE_R[1]+2,MAZE_G[1]+2,MAZE_B[1]+2)
RED_LOWER = cv.CV_RGB(LASER_R-2,MAZE_G-2,MAZE_B-2)
RED_LOWER = cv.CV_RGB(L_R-2,MAZE_G-2,MAZE_B-2)
YELLOW_LOWER = cv.CV_RGB(MAZE_R-2,MAZE_G-2,MAZE_B-2)
YELLOW_UPPER = cv.CV_RGB(MAZE_R-2,MAZE_G-2,MAZE_B-2)
BLUE_LOWER = cv.CV_RGB(MAZE_R-2,MAZE_G-2,MAZE_B-2)
BLUE_UPPER = cv.CV_RGB(MAZE_R-2,MAZE_G-2,MAZE_B-2)

orientation = "N"
position = (PAN_ANGLE, TILT_ANGLE)
while True:
	frame = cv.QueryFrame(camcapture)
	mat = cv.GetMat(frame)
	if frame is None:
		break
	if has_won(mat, TOLERANCE):
		break
	
	redPixels = mark_pixels(mat, RED_LOWER, RED_UPPER)
	redCenter = center_of_mass(redPixels)
	orientation, position = get_move(orientation, position, mat, redCenter)

	## blackedOut = mark_pixels(mat, BLACK_LOWER,  BLACK_UPPER)
	## redPixels = mark_pixels(mat, RED_LOWER, RED_UPPER)
	## yellowPixels = mark_pixels(mat, YELLOW_LOWER, YELLOW_UPPER)
	## redCenter = center_of_mass(redPixels)
	## yellowCenter = center_of_mass(yellowPixels)
	## if redCenter != None:
	## 	cv.Circle(mat, redCenter, 5, (255,0,0,0))
	## if yellowCenter != None:
	## 	cv.Circle(mat, yellowCenter, 5, (0,255,0,0))
	## cv.ShowImage('Camera', mat)
	## cv.ShowImage('Processed', blackedOut)
	## cv.ShowImage('Processed2',redPixels)
	## cv.ShowImage('Processed3',yellowPixels)

	k = cv.WaitKey(10)
'''
