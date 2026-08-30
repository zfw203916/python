"""
    多线程扣减功能: 这就是一个演示多线程并发修改共享变量问题的经典案例
    多线程并发修改共享变量问题 = 多个线程同时改同一个数据

"""

import threading
import time
from multiprocessing import Process, Value

# ---------- 不加锁（会出错） ----------
def test_without_lock():
    balance = 100
    def withdraw():
        nonlocal balance
        temp = balance
        time.sleep(0.001)
        temp = temp - 1
        balance = temp

    threads = []
    for i in range(10):
        t = threading.Thread(target=withdraw, name=f"name:{i}")
        print(f"不加锁的线程:{i}")
        threads.append(t)
        t.start()

    for i in threads:
        i.join()

    print(f"不加锁计算结果: {balance}")  # 大概率 99

    
# ---------- 加锁（正确） ----------
def test_with_lock():
    balance = 100
    lock = threading.Lock()
    def withdraw():
        nonlocal balance
        # lock.acquire()
        # temp = balance
        # temp = temp - 1
        # balance = temp
        # lock.release()
        with lock:
            temp = balance
            temp = temp - 1
            balance = temp

    threads=[]
    for i in range(10):
        t = threading.Thread(target=withdraw,name=f"name:{i}")
        print(f"加锁的线程:{i}")
        threads.append(t)
        t.start()

    for i in threads:
        i.join()

    print(f"加锁计算结果: {balance}")  


# ---------- 多进程（test 函数必须定义在全局） ----------
def test(balance):
        # 直接修改共享变量（需要加锁）
        with balance.get_lock():
            temp = balance.value
            temp = temp - 1
            balance.value = temp

# ---- 多进程并行的例子 -----
def multiprocessing_test():
    # 用 Value 创建共享变量
    balance = Value("i",100)
    process_test = []
    for i in range(10):
        t = Process(target=test, args=(balance,))
        process_test.append(t)
        t.start()
        print(f"多进程并行的例子：{i}")

    for i in process_test:
        i.join()

    print(f"多进程并行结果::{balance.value}")



if __name__ == "__main__":
    test_without_lock()
    test_with_lock()
    multiprocessing_test()