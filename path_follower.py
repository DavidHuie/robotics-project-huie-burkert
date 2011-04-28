import json
import math
import cv
from cluster import HierarchicalClustering as HC
from servo_api import *
with open('data.json', 'r') as f:
	data = json.load(f)

class RGBRange:
	pass

LASER = RGBRange()
START = RGBRange()
END = RGBRange()
GRID = RGBRange()
MAZE = RGBRange()

[LASER.r, LASER.g, LASER.b] = data["laser"]
[START.r, START.g, START.b] = data["start"]
[END.r, END.g, END.b] = data["end"]
[GRID.r, GRID.g, GRID.b] = data["grid"]
[MAZE.r, MAZE.g, MAZE.b] = data["maze"]
PAN_ANGLE = data["pan_angle"]
TILT_ANGLE = data["tilt_angle"]

threshold = 10

def get_relevant_points(image_m, R, G, B):
	points = []
	
	compare = lambda color, val: color[0] <= val <= color[1]
	
	for y in range(image_m.rows):
		for x in range(image_m.cols):
		
			b,g,r,_ = cv.Get2D(image_m, y, x)

			if compare(R, r) and compare(G, g) and compare(B, b):
				points.append( (x,y) )
	return points

def point_distance(point1, point2):
	x1, y1 = point1
	x2, y2 = point2
	return math.sqrt( (x1 - x2)**2 + (y1 - y2)**2 )

def center_of_mass_points(points):
	length = len(points)
	x_sum = sum([x for x, _ in points])
	y_sum = sum([y for _, y in points])

	return x_sum/length, y_sum/length

def get_center(image_m, obj):
	points = get_relevant_points(image_m, obj.r, obj.g, obj.b)
	return center_of_mass_points(points)

def get_grid_locations(image_m, max_dist = 50):
	points = get_relevant_points(image_m, GRID.r, GRID.g, GRID.b)
	clusterer = HC(points, point_distance)
	clusters = clusterer.getlevel(max_dist)

	coords = [center_of_mass_points(c) for c in clusters]

	return coords

def mark_points(image_m, points):
	point_set = set(points)
	
	copy = cv.CloneMat(image_m)

	for y in range(image_m.rows):
		for x in range(image_m.cols):
			if (x,y) in point_set:
				cv.Set2D(copy, y, x, cv.RGB(0,0,0))
			else:
				cv.Set2D(copy, y, x, cv.RGB(255,255,255))
	return copy

def no_obstacle(point1, point2, image_m):
	if point1 == point2: return False
	
	x1, y1 = point1
	x2, y2 = point2
	
	def apx_line(x):
		return int( (1.0*y2-y1)/(x2-x1) * (x-x1) + y1 )
	
	points = [(x, apx_line(x)) for x in range(min(x1,x2), max(x1,x2))]

	compare = lambda color, val: color[0] <= val <= color[1]

	for x, y in points:
		b,g,r,_ = cv.Get2D(image_m, y, x)
		for obj in [MAZE]:
			if compare(obj.r, r) and compare(obj.g, g) and compare(obj.b, b):
				return False
	return True

def create_graph(points, start_point, end_point, image_m):
	all_points = points + [start_point, end_point]

	graph = dict([(p, []) for p in all_points])

	for source in all_points:
		for dest in all_points:
			if no_obstacle(source, dest, image_m):
				graph[source].append(dest)
	return graph

def dfs(graph, start, end):
	return dfs_helper(graph, start, end, [])

def dfs_helper(graph, start, end, visited):
	visited.append(start)

	if start == end:
		return [start]

	for child in graph[start]:
		if child not in visited:
			l = dfs_helper(graph, child, end, visited)
			if l:
				return [start] + l
	return False


def move_servo(point1, point2):
	if abs(point1[0] - point2[0]) > TOLERANCE or  abs(point1[1] - point2[1]) > TOLERANCE:
			
		if  abs(point1[0] - point2[0]) > abs(point1[1] - point2[1]):
			if point1[0] > point2[0]:
				PAN_ANGLE = delta_move(0, PAN_ANGLE, delta = -1)
			else:
				  
				PAN_ANGLE = delta_move(0, PAN_ANGLE)
		else:
			if point1[1] > point2[1]:
				PAN_ANGLE = delta_move(1, PAN_ANGLE, delta = -1)
			else:
				PAN_ANGLE = delta_move(1, PAN_ANGLE)
		capture = cv.CapturefromCAM(CAMERA)
		image = cv.GetMat(cv.QueryFrame(cam_capture))
		points = get_relevant_points(image, LASER.r, LASER.g, LASER.b)
		point1 = center_of_mass(points)
		move_servo(point1, point2)		 


CAMERA = 0 # use default camera
cam_capture = cv.CaptureFromCAM(CAMERA)

image = cv.GetMat(cv.QueryFrame(cam_capture))

grid_points = get_grid_locations(image)
print "grid points:", grid_points

start_point = get_center(image, START)
end_point = get_center(image, END)

print "start point", start_point
print "end point", end_point

graph = create_graph(grid_points, start_point, end_point, image)

print "graph", graph

path = dfs(graph, start_point, end_point)
print path

for i in path[1:]
	next = path[i]
	current = path[i-1]
	move_servo(point1, point2) 


## marked = mark_points(image, points)
## cv.ShowImage('marked', marked)
## raw_input()
        
