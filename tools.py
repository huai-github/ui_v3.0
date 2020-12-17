from ctypes import *
from os.path import join
import cv2 as cv
import numpy as np
from math import sin, cos


def line_parallel(img, a, b, interval, left=1, right=1):
	"""
	:param img: 画布
	:param a: 中线起点坐标
	:param b: 中线终点坐标
	:param interval: 边线偏移量
	:param left: 画在中线的左边（left = -1）
	:param right: 画在总线的右边（right = -1）
	"""
	k = (b[1] - a[1]) / (b[0] - a[0])
	theta = np.arctan(k)
	x_offset = interval * sin(theta) * left  # 想要画在左边，left = -1
	y_offset = interval * cos(theta) * right

	M = np.float32([[1, 0, x_offset],
					[0, 1, y_offset]])
	# print(np.float32([[a], [b]]).shape)
	new_pt = cv.transform(np.float32([[a], [b]]), M).astype(np.int)

	cv.line(img, a, b, (0, 255, 0), 1)
	cv.line(img, tuple(new_pt[0][0]), tuple(new_pt[1][0]), (0, 0, 255), 2)


class TypeSwitchUnion(Union):
	_fields_ = [
		('double', c_double),
		('int', c_int),
		('float', c_float),
		('short', c_short),
		('char_2', c_char * 2),
		('char_8', c_char * 8)
	]