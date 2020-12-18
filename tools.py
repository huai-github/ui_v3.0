from ctypes import *
from os.path import join
import cv2 as cv
import numpy as np
from math import sin, cos


def work_area(img, a, b, interval, point):
	k = (b[1] - a[1]) / (b[0] - a[0])
	theta = np.arctan(k)
	x_offset = interval * sin(theta) * -1
	y_offset = interval * cos(theta)

	x1_offset = interval * sin(theta)
	y1_offset = interval * cos(theta) * -1

	M = np.float32([[1, 0, x_offset],
					[0, 1, y_offset]])

	M1 = np.float32([[1, 0, x1_offset],
					 [0, 1, y1_offset]])

	new_pt = cv.transform(np.float32([[a], [b]]), M).astype(np.int)
	new_pt1 = cv.transform(np.float32([[a], [b]]), M1).astype(np.int)

	cv.line(img, a, b, (0, 255, 0), 1)
	cv.line(img, tuple(new_pt[0][0]), tuple(new_pt[1][0]), (0, 0, 255), 2)
	cv.line(img, tuple(new_pt1[0][0]), tuple(new_pt1[1][0]), (0, 0, 255), 2)
	# 补全矩形框
	cv.line(img, tuple(new_pt1[0][0]), tuple(new_pt[0][0]), (255, 255, 255), 1)
	cv.line(img, tuple(new_pt1[1][0]), tuple(new_pt[1][0]), (255, 255, 255), 1)

	gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
	ret, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY)
	image, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
	cv.drawContours(image, contours, -1, (255, 0, 255), 1)
	# point = (200, 200)
	dist = cv.pointPolygonTest(contours[0], point, False)

	return dist


class TypeSwitchUnion(Union):
	_fields_ = [
		('double', c_double),
		('int', c_int),
		('float', c_float),
		('short', c_short),
		('char_2', c_char * 2),
		('char_8', c_char * 8)
	]