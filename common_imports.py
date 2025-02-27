from time import sleep
from os import system
from threading import Thread, Lock, Condition
from queue import Queue, Empty
import multiprocessing as mp
from multiprocessing import Process

default_timeout = 0
mini_wait = 5
