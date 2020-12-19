from ctypes import *
from os.path import join
import cv2 as cv
import numpy as np
from math import sin, cos


def rad2angle(rad):
	return rad * 180 / np.pi


def work_area(img, a, b, l, point):
	# k = (b[1] - a[1]) / (b[0] - a[0])
	# theta = np.arctan(k)
	# x_offset = interval * sin(theta) * -1
	# y_offset = interval * cos(theta)
	#
	# x1_offset = interval * sin(theta)
	# y1_offset = interval * cos(theta) * -1
	#
	# M = np.float32([[1, 0, x_offset],
	# 				[0, 1, y_offset]])
	#
	# M1 = np.float32([[1, 0, x1_offset],
	# 				 [0, 1, y1_offset]])
	#
	# new_pt = cv.transform(np.float32([[a], [b]]), M).astype(np.int)
	# new_pt1 = cv.transform(np.float32([[a], [b]]), M1).astype(np.int)
	#
	# cv.line(img, a, b, (0, 255, 0), 1)
	# cv.line(img, tuple(new_pt[0][0]), tuple(new_pt[1][0]), (0, 0, 255), 2)
	# cv.line(img, tuple(new_pt1[0][0]), tuple(new_pt1[1][0]), (0, 0, 255), 2)
	# # 补全矩形框
	# cv.line(img, tuple(new_pt1[0][0]), tuple(new_pt[0][0]), (255, 255, 255), 1)
	# cv.line(img, tuple(new_pt1[1][0]), tuple(new_pt[1][0]), (255, 255, 255), 1)
	#
	# gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
	# ret, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY)
	# image, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
	# cv.drawContours(image, contours, -1, (255, 0, 255), 1)
	# # point = (200, 200)
	# dist = cv.pointPolygonTest(contours[0], point, False)
	#
	# return dist
	k = (b[1] - a[1]) / (b[0] - a[0])

	theta = np.arctan(k)

	x_offset = l * sin(theta) * -1
	y_offset = l * cos(theta)
	M = np.float32([[1, 0, x_offset],
					[0, 1, y_offset]])
	new_pt = cv.transform(np.float32([[a], [b]]), M).astype(np.int)

	x1_offset = l * sin(theta)
	y1_offset = l * cos(theta) * -1
	M1 = np.float32([[1, 0, x1_offset],
					 [0, 1, y1_offset]])
	new_pt1 = cv.transform(np.float32([[a], [b]]), M1).astype(np.int)

	box = np.array([tuple(new_pt1[0][0]), tuple(new_pt[0][0]), tuple(new_pt[1][0]), tuple(new_pt1[1][0])])
	# cv.drawContours(img, [box[:, np.newaxis, :]], 0, (0, 0, 255), 2)	 # 旋转前工作区域

	circle_pt = np.array(point)
	# print("circle_pt", circle_pt)
	# cv.circle(img, tuple(circle_pt.astype(np.int)), 2, (0, 0, 255), 2)	 # 旋转前挖斗实时位置

	if theta > np.pi / 2:
		angle = rad2angle(theta)
	else:
		angle = -rad2angle(theta)

	M = cv.getRotationMatrix2D(tuple(np.mean(box, axis=0)), angle, 1)

	box = np.vstack([box, circle_pt])
	box = cv.transform(box[:, np.newaxis, :], M)
	circle_pt_rotate = tuple(box[-1][0].astype(np.int))
	cv.drawContours(img, [box[:-1].astype(np.int)], -1, (0, 0, 255), 2)
	cv.circle(img, circle_pt_rotate, 3, (255, 0, 255), 5)
	img = cv.resize(img, None, fx=0.8, fy=0.8)
	# print("box",box)
	return box


class TypeSwitchUnion(Union):
	_fields_ = [
		('double', c_double),
		('int', c_int),
		('float', c_float),
		('short', c_short),
		('char_2', c_char * 2),
		('char_8', c_char * 8)
	]