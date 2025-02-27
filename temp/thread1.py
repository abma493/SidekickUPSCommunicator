# thread1.py
# This module variable will be set from main.py
from time import sleep
lock = None  

def thread1_function():
    with lock:  # Using the module-level variable
        print("Thread 1 accessing shared resource")
        x = 1 
        while x <= 5:
            print(f"thread 1 sleeping in lock [sec: {x}]")
            sleep(1)
            x+=1