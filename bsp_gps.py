from tools import *
import math
import thread

g_line_worked_flag = False  # 本直线段工作完成标志
g_deep_worked_flag = False  # 挖完一斗


def LatLon2XY(latitude, longitude):
	a = 6378137.0
	# b = 6356752.3142
	# c = 6399593.6258
	# alpha = 1 / 298.257223563
	e2 = 0.0066943799013
	# epep = 0.00673949674227

	# 将经纬度转换为弧度
	latitude2Rad = (math.pi / 180.0) * latitude

	beltNo = int((longitude + 1.5) / 3.0)  # 计算3度带投影度带号
	L = beltNo * 3  # 计算中央经线
	l0 = longitude - L  # 经差
	tsin = math.sin(latitude2Rad)
	tcos = math.cos(latitude2Rad)
	t = math.tan(latitude2Rad)
	m = (math.pi / 180.0) * l0 * tcos
	et2 = e2 * pow(tcos, 2)
	et3 = e2 * pow(tsin, 2)
	X = 111132.9558 * latitude - 16038.6496 * math.sin(2 * latitude2Rad) + 16.8607 * math.sin(
		4 * latitude2Rad) - 0.0220 * math.sin(6 * latitude2Rad)
	N = a / math.sqrt(1 - et3)

	x = X + N * t * (0.5 * pow(m, 2) + (5.0 - pow(t, 2) + 9.0 * et2 + 4 * pow(et2, 2)) * pow(m, 4) / 24.0 + (
			61.0 - 58.0 * pow(t, 2) + pow(t, 4)) * pow(m, 6) / 720.0)
	y = 500000 + N * (m + (1.0 - pow(t, 2) + et2) * pow(m, 3) / 6.0 + (
			5.0 - 18.0 * pow(t, 2) + pow(t, 4) + 14.0 * et2 - 58.0 * et2 * pow(t, 2)) * pow(m, 5) / 120.0)

	return x, y


class LatLonAlt(object):
	def __init__(self):
		self.latitude = 0
		self.longitude = 0
		self.altitude = 0


class GPSINSData(object):
	def __init__(self):
		self.head = [b'\xaa', b'\x33']  # 2B deviation 0-2     b'3' == b'\x33'
		self.length = [b'\x00'] * 2  # 2B deviation 4-6
		self.latitude = [b'\x00'] * 8  # 8B deviation 24
		self.longitude = [b'\x00'] * 8  # 8B deviation 32
		self.altitude = [b'\x00'] * 8  # 8B deviation 40
		self.checksum = 0  # 2B deviation 136
		self.xor_check = 0  # 定义异或校验返回值

	def gps_msg_analysis(self, recbuff):
		if (recbuff[0] == self.head[0]) and (recbuff[1] == self.head[1]):
			self.length = recbuff[4:6]
			self.latitude = recbuff[24:32]
			self.longitude = recbuff[32:40]
			self.altitude = recbuff[40:48]

			self.checksum = recbuff[136:138]
			self.checksum = self.checksum[0] + self.checksum[1]  # 将checksum 2字节合并

			for i in range(len(recbuff) - 2):  # 计算校验值
				recbuff[i] = int.from_bytes(recbuff[i], byteorder='little', signed=False)  # bytes转int
				self.xor_check = self.xor_check ^ recbuff[i]
			self.xor_check = self.xor_check.to_bytes(length=2, byteorder='little', signed=False)

			if self.xor_check == self.checksum:  # 数据包异或校验通过
				if recbuff[104] == b'\x04':  # gps信号稳定
					print("The signal of gps is stable！\r\n")
				else:
					print("The signal of gps is unstable！\r\n")
					pass
			else:
				print("checksum error!!!\r\n")
				pass
				return
		else:
			print("data head error!!!\r\n")

	# return

	def gps_typeswitch(self):
		gps_switch_lat = TypeSwitchUnion()
		gps_switch_lon = TypeSwitchUnion()
		gps_switch_alt = TypeSwitchUnion()
		# 字符串拼接
		latitude = self.latitude[0] + self.latitude[1] + self.latitude[2] + self.latitude[3] + self.latitude[4] + \
				   self.latitude[5] + self.latitude[6] + self.latitude[7]
		longitude = self.longitude[0] + self.longitude[1] + self.longitude[2] + self.longitude[3] + self.longitude[4] + \
					self.longitude[5] + self.longitude[6] + self.longitude[7]
		altitude = self.altitude[0] + self.altitude[1] + self.altitude[2] + self.altitude[3] + self.altitude[4] + \
				   self.altitude[5] + self.altitude[6] + self.altitude[7]

		gps_switch_lat.char_8 = latitude
		gps_switch_lon.char_8 = longitude
		gps_switch_alt.char_8 = altitude

		return gps_switch_lat.double, gps_switch_lon.double, gps_switch_alt.double
