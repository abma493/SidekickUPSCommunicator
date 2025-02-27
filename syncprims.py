from threading import Semaphore, Condition
from queue import Queue


comm_queue = Queue() # gonna take aggregate values as dictionary
sem_driver = Semaphore(0)
sem_UI = Semaphore(0)
queue_cond = Condition()