# s = [10, 20 ,"good"]

# print(type(s))

# print(s[0])
# print(s[-3])
# s[0] = 100
# print(s[0])

# list01 = [0,1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# print(list01[0:5:1])
# print(list01[0:5:2])


# input_str = []
# for i in range(10):
#     input_str.append(int(input(f"这波AI红利一定要吃上。输入10个数字,请输入第{i+1}个数字")))

# print(f"你输入了： {input_str}")
# sorted_list = sorted(input_str)
# print(f"这是排序后的： {sorted_list}")

# print(f"最小值是: {sorted_list[0]}")
# print(f"最大值是: {sorted_list[-1]}")
# print(f"平均数是: {sum(sorted_list)/len(sorted_list)}")


# num_list1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# num_list2 = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
# # num_list = set(num_list1 + num_list2)

# for num in num_list1:
#     num_list2.append(num)

# print(f"合并后的列表{num_list2}")

# num_list = []
# for num in num_list2:
#     if num not in num_list:
#         num_list.append(num)
# print(f"去重后的列表{num_list}")


# num_list = []
# for num in range(1,21):
#     num_list.append(num**2)
# number_list = [num**2 for num in range(1,21)]
# print(f"平方后的列表{num_list}")
# print(f"推导式平方后的列表:{number_list}")


# str1 = "hello world"
# print(str1[0])
# str1[0] = "H"
# print(str1[0])

# str_mail = input("请输入邮箱地址：")
# if str_mail.count("@") == 1 and str_mail.count(".") >=1 :
#     print("邮箱地址格式正确")
# else:
#     print("邮箱地址格式错误")


# t1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
# print(t1)
# print(t1[0])
# print(type(t1))


# t1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
# t2 = 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
# a, b, c, d, e, f, g, h, i, j = t2
# print(t1)
# print(t2)
# print(type (t2))
# print(a)


# student = (
#     ("s001", "张三", 18, 85, 90, 100),
#     ("s002", "李四", 19, 88, 92, 95),
#     ("s003", "王五", 18, 90, 88, 91),
# )
# for s in student:
#     sum_str=sum(s[3:6])
#     sum_pingjung= sum_str/3
#     print(f"{s[1]}同学的总成绩是{sum_str},平均分是：{sum_pingjung:.1f},最低分：{min(s[3:6])},最高分：{max(s[3:6])}")
# chinese_list = [ s[3] for s in student]
# math_list = [s[4] for s in student]
# english_list = [s[5] for s in student]
# print(f"语文成绩最低和最高：{min(chinese_list)},{max(chinese_list)},平均分：{sum(chinese_list)/len(chinese_list):.1f}")
# print(f"数学成绩最低和最高：{min(math_list)},{max(math_list)},平均分：{sum(math_list)/len(math_list):.1f}")
# print(f"英语成绩最低和最高：{min(english_list)},{max(english_list)},平均分：{sum(english_list)/len(english_list):.1f}")
# print(f"总平均分：{sum(chinese_list + math_list + english_list)/len(chinese_list + math_list + english_list):.1f}")

# s1 = {2,1,2,6,7,3,4,5}
# print(s1)
# print(type(s1))


# football_set = {"王林", "曾牛", "徐立国", "遁天", "天运子", "韩立", "厉飞雨", "乌丑", "紫灵"}#选修足球学生名单
# basketball_set = {"张铁", "墨居仁", "王林", "姜老道", "曾牛", "王蝉", "韩立", "天运子", "李化元", "厉飞雨", "云露"}# 选修法语学生名单
# french_set = {"许木", "王卓", "十三", "虎咆", "姜老道", "天运子", "红蝶", "厉飞雨", "棘立", "曾牛"}# 选修艺术学生名单
# art_set = {"遁天", "天运子", "韩立", "虎咆", "姜老道", "紫灵"}# 选修音乐学生名单
# fa_set = french_set.intersection(art_set)
# print(f"同时选修法语和艺术的学生：{fa_set}")
# str_diff =french_set.difference(art_set)
# print(f"只选修法语的学生：{str_diff}")

# def test_get_function(r):
#     """
#     test function.
#     """
#     print("test")
# help(test_get_function)

# def traingle_are(a, b, c):
#     """
#     计算三角形的面积
#     :param a: 三角形的一条边
#     :param b: 三角形的第二条边
#     :param c: 三角形的第三条边
#     :return: 三角形的面积
#     """
#     p = (a + b + c) / 2
#     return p * (p - a) * (p - b) * (p - c) ** 0.5

# print(traingle_are(3, 4, 5))

# def test_get_function(r):
#     """
#     test function.
#     """
#     traingle_are(3, 4, 5)
#     print("test")


# def calc_area(r):
#     """
#     :param r: list
#     :return: max, min, avg
#     """
#     s_max = max(r)
#     s_min = min(r)
#     s_avg = sum(r) / len(r)
#     return s_max, s_min, s_avg

# s_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# s_max, s_min, s_avg = calc_area(s_list)
# print(f"最大值是：{s_max},最小值是：{s_min},平均数是：{s_avg}")

# def calc_area(*args, **kwargs):
#     """
#     :param r: list
#     :return: max, min, avg
#     """
#     s_max = max(args)
#     s_min = min(args)
#     s_avg = sum(args) / len(args)
#     if kwargs.get("round") is not None:
#         s_avg = round(s_avg, kwargs.get("round"))
#     if kwargs.get("print"):
#         print(f"最大值是：{s_max},最小值是：{s_min},平均数是：{s_avg}")
#     else:
#         print(s_max, s_min, s_avg)
#     return s_max, s_min, s_avg

# calc_area(1, 2, 13, 111.33, 5, 6, 7, 8, 29, 10, round=3, print=False)


# def add(x,y):
#     return x + y

# def sub(x,y):
#     return x - y

# def cacl(x, y, func):
#     return func(x, y)

# print(cacl(1, 2, sub))

# import math
# t1 = [1, 2, 13, 111.33, 5, 6, 7, 8, 29, 10]
# t1.sort()
# #
# #
# str = lambda x, y: x+y
# print(str(1, 2))

# import random
# __all__ = ["Student"]


# f = open("tests/test.txt", "r", encoding="utf-8")
# content_list = f.readlines()
# try:
#     for i in range(len(content_list)):
#         content_list[i] = content_list[i].strip()
#         print(f"{content_list[i]}")
# finally:
#     f.close()

# f = open("tests/test.txt", "w", encoding="utf-8")
# try:
#     i = 1 / 1

#     f.write("这是测试写入的内容")
# finally:
#     print("写入完成")
#     f.close()

# with open("tests/test.txt", "w", encoding="utf-8") as f:
#     f.write("这是测试写入的内容\n")
#     f.write("这是测试写入的内容2\n")


# user = {
#     "name": "张三",
#     "age": 18,
#     "gender": "男",
#     "hobbies": ["篮球", "足球", "游泳"],
#     "address": {
#         "province": "广东省",
#         "city": "广州市",
#         "district": "天河区"
#     }
# }

# with open("tests/test.json", "w", encoding="utf-8") as f:
#     import json
#     json.dump(user, f, ensure_ascii=False, indent=4)


# with open("tests/test.json", "r", encoding="utf-8") as f:
#     import json
#     user = json.load(f)
#     print(user)

# import sys
# import os
# from dotenv import load_dotenv

# load_dotenv()
# class Car:

#     whell = 4 # 类属性，4个轮胎
#     tax_rate = float(os.getenv("COUNTRY_TAX_RATE", 0.2))
#     # print(tax_rate)
#     # sys.exit()
#     def __init__(self, color: str, speed: int, price:float):
#         self.color = color  # 实例属性
#         self.speed = speed  # 实例属性
#         self.price = price  # 实例属性

#     def run(self):
#         print(f"Car is running at {self.speed} km/h.")

#     def __eq__(self, other):
#         if not isinstance(other, Car):
#             return False
#         return  self.color == other.color and self.speed == other.speed

#     def total_cost(self, discount:float):
#         total_cost = self.price * discount + self.price * Car.tax_rate
#         return total_cost
#     def __lt__(self, other):
#         return  self.price < other.price

# c1 = Car(color="blue", speed=80, price=2000)
# c2 = Car(color="blue", speed=80, price=3800)
# # print(f"车的颜色是：{c1.color},车的速度是：{c1.speed}")

# # print(c1.__dict__)
# # print(c1==c2)
# # print(c1 > c2)
# print(f"c1价格:{c1.total_cost(0.8)},税率:{c1.tax_rate}")


# str = "1,2,3,4,5,6,7,8,9,10"
# str_split = str.split(",")
# print(str_split)

# import base64
# # ---------- 字符串编码 ----------
# text = "hello world"
# text_byte= text.encode('utf-8')
# encoded = base64.b64encode(text_byte)
# print(encoded)
# print(base64.b64decode(encoded))

# import hmac, hashlib

# message = b"amount=100&to=alic"
# key = b"frank"
# signature=hmac.new(key, message, hashlib.sha256).hexdigest()
# expected = hmac.new(key, message, hashlib.sha256).hexdigest()
# is_valid = hmac.compare_digest(signature, expected)
# print(signature)
# print(expected)
# print(is_valid)


# from itertools import cycle, repeat

# # # 轮流给数据打标签（无限循环）
# # labels = cycle(["A","B","C"])
# # number = range(10)
# # num = list(range(10))
# # print(number)
# # print(num)
# # print(range)
# nested=[[1,2], [3,4], [5,6]]
# result = []
# for sub in nested:
#     for item in sub:
#         result.append(item)
# print(result)


# def timer(func):
#     def wrapper():
#         print("test")
#     return wrapper

# @timer
# def slow_function():
#     print("完成")

# # 调用时完全没变化
# slow_function()


# from contextlib import contextmanager

# @contextmanager
# # 执行流程：进入 with → 执行到 yield 暂停 → 运行 with 块 → 继续执行 yield 后面的代码（清理/收尾）
# def timer():
#     print("1、开始")
#     yield          # 这里就是 with 块内部
#     print(f"3、回到这里来结束")

# # 使用
# with timer():
#     print("2、这里是test")


# from urllib.request import urlretrieve

# # 带进度回调（适合大文件）
# def report(block_num, block_size, total_size):
#     downloaded = block_num * block_size
#     percent = min(100, downloaded / total_size * 100)
#     print(f'下载进度: {percent:.1f}%')

# # 直接下载到本地
# urlretrieve('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSLWILUXUID5uJOvBHKAbmakz3YIff2Yo4JenaWFl41rA&s', 'local_photo.jpg', reporthook=report)

# 服务端
# 客户端
# import socket

# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(('127.0.0.1', 8080))  # 连接服务器
# data = client.recv(1024)             # 接收数据
# print(data.decode())
# client.close()

# import redis
# # 连接本地Redis
# r = redis.Redis(
#     host="127.0.0.1",
#     port=6379,
#     db=0,
#     decode_responses=True
# )
# # print(r.ping())
# # 存储用户信息（类似字典）
# r.hset('user:1001', mapping={
#     'name': '李四',
#     'age': 25,
#     'city': '北京'
# })

# # 获取所有字段
# user = r.hgetall('user:1001')  # {'name': '李四', 'age': '25', 'city': '北京'}

# # 获取单个字段
# name = r.hget('user:1001', 'name')  # '李四'

# # 增加字段值
# r.hincrby('user:1001', 'age', 1)  # 年龄+1
# print(f"test::{name}")

# import re
# s1 ="18809090000是我的手机号,你记住了吗?我的另一个手机号是18800008888,两个QQ号分别是155998992 和 18809091293821 你记住了吗？"
# s2 ="我的手机号是18809090000,你记住了吗?我的另一个手机号是18800008888,两个QQ号分别是155998992 和 18809091293821 你记住了吗？"

# test02 = re.match('1[3-9]\d{9}', s2)
# group_test = re.search(r'1[3-9]\d{9}', s2)
# print(group_test)
# # print(group_test)
# # print(search_test)

# import requests
# import json
# url = "http://www.baidu.com"
# resp = requests.request("GET",url)
# # print(resp.text)
# # print(resp.json()['token-type'])
# s = requests.Session()
# results = s.get(url)
# print(results)

# url = "http://www.google.com"
# respt = requests.request("post",url,json='')