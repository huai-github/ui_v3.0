import sys
import UI
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore
from time import sleep
from my_thread import MyThread
from thread import *
import globalvar as gl

h = 480  # 画布大小
w = 550

g_startX = 0
g_startY = 0
g_startH = 0
g_startW = 0
g_endX = 0
g_endY = 0
g_endH = 0
g_endW = 0


def get_global_value():
	global g_startX, g_startY, g_startH, g_startW, g_endX, g_endY, g_endH, g_endW
	g_startX = gl.get_value('g_startX')
	g_startY = gl.get_value('g_startY')
	g_startH = gl.get_value('g_startH')
	g_startW = gl.get_value('g_startW')
	g_endX = gl.get_value('g_endX')
	g_endY = gl.get_value('g_endY')
	g_endH = gl.get_value('g_endH')
	g_endW = gl.get_value('g_endW')


class UIFreshThread(object):  # 界面刷新线程
	def __init__(self):
		self.startX = 0  # from could
		self.startY = 0
		self.endX = 0
		self.endY = 0
		self.Interval = 0

		self.nowX = 0  # from gps
		self.nowY = 0
		self.deep = 0

	def __call__(self):  # 调用实例本身 ——>> MyThread(self.__thread,....
		if g_startX != 0:
			self.startX = g_startX  # from could
			self.startY = g_startY
			self.endX = g_endX
			self.endY = g_endY
			self.Interval = g_startW

		self.nowX = thread.g_x - 4076000  # from gps
		self.nowY = thread.g_y - 515000
		self.deep = thread.g_h  # - 基准高 baseHeight from could

		sleep(1)

	def get_msg_xy(self):
		return self.startX, self.startY, self.endX, self.endY, self.Interval, self.nowX, self.nowY

	def get_msg_deep(self):
		return self.deep

	def get_msg_startXY(self):
		return self.startX, self.startY

	def get_msg_endXY(self):
		return self.endX, self.endY

	def get_msg_nowXY(self):
		return self.nowX, self.nowY


class MyWindows(QWidget, UI.Ui_Form):
	def __init__(self):
		super().__init__()
		# 注意：里面的控件对象也成为窗口对象的属性了
		self.setupUi(self)
		self.imgLine = np.zeros((h, w, 3), np.uint8)  # 画布
		self.imgBar = np.zeros((h, w, 3), np.uint8)
		self.figure = plt.figure()  # 可选参数,facecolor为背景颜色
		self.canvas = FigureCanvas(self.figure)
		self.__timer = QtCore.QTimer()  # 定时器用于定时刷新
		self.set_slot()
		self.__thread = UIFreshThread()  # 开启线程(同时将这个线程类作为一个属性)
		MyThread(self.__thread, (), name='UIFreshThread', daemon=True).start()
		self.__timer.start(1000)  # ms
		self.DeepList = []
		self.NumList = []

	def set_slot(self):
		self.__timer.timeout.connect(self.update)

	def leftWindow(self, img, startX, startY, endX, endY, Interval, nowX, nowY):
		img[...] = 255
		startPoint = (int(startX), int(startY))
		endPoint = (int(endX), int(endY))
		width = Interval * 5
		currentPoint = (int(nowX), int(nowY))
		dist = work_area(img, startPoint, endPoint, width, currentPoint)

		cv2.circle(img, currentPoint, 6, (255, 0, 0), -1)
		BorderReminderLedXY = (530, 460)  # 边界指示灯位置 界内绿色
		BorderReminderTextXY = (230, 470)
		cv2.circle(img, BorderReminderLedXY, 12, (0, 255, 0), -1)
		self.BorderReminder.setText("   ")
		# 如果超出边界，BorderReminder红色,并提示汉字信息
		if dist == 0:
			cv2.circle(img, BorderReminderLedXY, 12, (0, 0, 255), -1)  # 边界报警指示灯
			self.BorderReminder.setText("！！即将超出边界！！")
		elif dist == -1:
			cv2.circle(img, BorderReminderLedXY, 12, (0, 0, 255), -1)  # 边界报警指示灯
			self.BorderReminder.setText("！！超出边界！！")

		cv2.putText(img, "BorderReminder", BorderReminderTextXY, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
		QtImgLine = QImage(cv2.cvtColor(img, cv2.COLOR_BGR2RGB).data,
						   img.shape[1],
						   img.shape[0],
						   img.shape[1] * 3,  # 每行的字节数, 彩图*3
						   QImage.Format_RGB888)

		pixmapL = QPixmap(QtImgLine)
		self.leftLabel.setPixmap(pixmapL)

	def rightWindow(self, img, deep):
		img[::] = 255  # 设置画布颜色

		if len(self.NumList) >= 5:  # 最多显示5条柱状图
			self.DeepList.pop(0)
			self.NumList.pop(0)

		self.DeepList.append(deep)
		self.NumList.append(' ')

		# 将self.DeepList中的数据转化为int类型
		self.DeepList = list(map(float, self.DeepList))

		# 将x,y轴转化为矩阵式
		self.x = np.arange(len(self.NumList)) + 1
		self.y = np.array(self.DeepList)

		colors = ["g" if i > 0 else "r" for i in self.DeepList]
		plt.clf()
		plt.bar(range(len(self.NumList)), self.DeepList, tick_label=self.NumList, color=colors, width=0.5)

		# 在柱体上显示数据
		for a, b in zip(self.x, self.y):
			plt.text(a - 1, b, '%.4f' % b, ha='center', va='bottom')

		# 画图
		self.canvas.draw()

		img = np.array(self.canvas.renderer.buffer_rgba())

		QtImgBar = QImage(img.data,
						  img.shape[1],
						  img.shape[0],
						  img.shape[1] * 4,
						  QImage.Format_RGBA8888)
		pixmapR = QPixmap(QtImgBar)

		self.rightLabel.setPixmap(pixmapR)

	def showStartXY(self, startX, startY):
		self.startXY.setText("(%.2f, %.2f)" % (startX, startY))

	def showEndXY(self, endX, endY):
		self.endXY.setText("(%.2f, %.2f)" % (endX, endY))

	def showNowXY(self, nowX, nowY):
		self.nowXY.setText("(%.2f, %.2f)" % (nowX, nowY))

	def update(self):
		self.rightWindow(self.imgBar, self.__thread.get_msg_deep())
		self.leftWindow(self.imgLine, *self.__thread.get_msg_xy())
		self.showStartXY(*self.__thread.get_msg_startXY())
		self.showEndXY(*self.__thread.get_msg_endXY())
		self.showNowXY(*self.__thread.get_msg_nowXY())


if __name__ == "__main__":
	gl._init()
	app = QApplication(sys.argv)

	gps_thread = threading.Thread(target=thread.thread_gps_func, daemon=True)
	_4g_thread = threading.Thread(target=thread.thread_4g_func, daemon=True)

	gps_thread.start()  # 启动线程
	mainWindow = MyWindows()
	_4g_thread.start()
	sleep(0.5)
	if thread.g_reced_flag:
		get_global_value()
		mainWindow.show()
	else:
		print("--rec task failed--")
	sys.exit(app.exec_())
