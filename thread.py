from time import sleep

from bsp_serialport import *
from bsp_4g import *
from bsp_gps import *
from datetime import datetime
from threading import Timer
import threading

# 消息类型。1：心跳，2：上报
TYPE_HEART = 1
TYPE_SEND = 2
# 挖掘机ID
diggerId = 111
# 高斯坐标，全局变量，double类型
g_x = 0
g_y = 0
g_h = 0


class TimeInterval(object):
	def __init__(self, start_time, interval, callback_proc, args=None, kwargs=None):
		self.__timer = None
		self.__start_time = start_time
		self.__interval = interval
		self.__callback_pro = callback_proc
		self.__args = args if args is not None else []
		self.__kwargs = kwargs if kwargs is not None else {}

	def exec_callback(self, args=None, kwargs=None):
		self.__callback_pro(*self.__args, **self.__kwargs)
		self.__timer = Timer(self.__interval, self.exec_callback)
		self.__timer.start()

	def start(self):
		interval = self.__interval - (datetime.now().timestamp() - self.__start_time.timestamp())
		# print( interval )
		self.__timer = Timer(interval, self.exec_callback)
		self.__timer.start()

	def cancel(self):
		self.__timer.cancel()
		self.__timer = None


def thread_gps_func():
	GPS_COM = "com5"
	GPS_REC_BUF_LEN = 138
	while True:
		gps_data = GPSINSData()
		gps_msg_switch = LatLonAlt()
		gps_rec_buffer = []
		gps_com = SerialPortCommunication(GPS_COM, 115200, 0.2)  # 5Hz
		gps_com.rec_data(gps_rec_buffer, GPS_REC_BUF_LEN)  # int
		gps_com.close_com()
		# g_gps_threadLock.acquire()  # 加锁
		gps_data.gps_msg_analysis(gps_rec_buffer)
		# 8 -> 1，得到经纬度
		gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude = gps_data.gps_typeswitch()
		# print("纬度：%s\t经度：%s\t海拔：%s\t" % (gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude))
		# 经纬度转高斯坐标
		global g_x, g_y, g_h
		g_x, g_y = LatLon2XY(gps_msg_switch.latitude, gps_msg_switch.longitude)
		g_h = gps_msg_switch.altitude
		# 判断是否挖完一次
		h_last = g_h
		if g_h > h_last: 	# 当前的海拔大于上一次的海拔，说明斗开始上升了
			global g_worked_flag
			g_worked_flag = True
		# g_gps_threadLock.release()  # 解锁
		# print("x：%s\t y：%s\t deep：%s" % (g_x, g_y, g_h))  # 高斯坐标


def thread_4g_func():
	COM_ID_4G = "com21"

	rec = RecTasks()
	heart = Heart(TYPE_HEART, diggerId)

	com_4g = SerialPortCommunication(COM_ID_4G, 115200, 0.5)

	# 间隔一分钟发送一次心跳
	start = datetime.now().replace(minute=0, second=0, microsecond=0)
	minute = TimeInterval(start, 6, heart.send_heart_msg, [com_4g])  # 6s
	minute.start()
	minute.cancel()

	while True:
		# 接收
		rec_buf = com_4g.read_line()  # byte -> bytes
		# print("rec_buf", rec_buf)
		if rec_buf != b'':
			rec_buf_dict = task_switch_dict(rec_buf)
			rec.save_msg(rec_buf_dict)
			# print(rec.rec_task_dict["diggerId"])
			# print(rec.rec_task_dict["section"][0]["sortNo"])

		# 发送
		send = SendMessage(TYPE_HEART, diggerId, round(g_x, 2), round(g_y, 2), round(g_h, 2))
		send_msg_json = send.switch_to_json()
		com_4g.send_data(send_msg_json.encode('utf-8'))


if __name__ == "__main__":
	gps_thread = threading.Thread(target=thread_gps_func)
	_4g_thread = threading.Thread(target=thread_4g_func)

	gps_thread.start()  # 启动线程
	sleep(0.5)
	_4g_thread.start()
