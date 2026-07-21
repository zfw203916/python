from io import StringIO, BytesIO
import pickle
import threading, multiprocessing
def test_hello_world()->None:
     """Basic sanity check."""
     assert True

def test_math_works()->None:
     """Basic sanity check."""
     assert 1 + 1 == 2

def test_math_fails()->None:
     """Basic sanity check."""
     assert 1 + 3 == 4

# IO
def test_basec_works()->None:
     """Basic sanity check.我想这里不走test测试，就做我基本的语法验证"""
     f = StringIO()
     i = BytesIO()
     Ivalue = i.write("hello world".encode("utf-8"))
     value = f.write("hello world")
     print(f"真是麻烦：{f}")
     print(f"想看一下:{value},")
     print(i.getvalue())
     assert True

#pickle
def test_pickle_works()->None:
     """Basic sanity check."""
     d = dict(name = 'Bob', age = 20, score = 88)
     s = pickle.dumps(d)
     print(f"内容：{s}")

def test_os_frok()->None:
     """进程，子进程问题"""
     import os
     pid = os.fork()
     if pid == 0:
          print("我是子进程pid:%d" % os.getpid())
     else:
          print("我是父进程pid:%d" % os.getpid())



def loop():
     x = 10
     while True:
           x = x ^ 1
     
     print(x)

