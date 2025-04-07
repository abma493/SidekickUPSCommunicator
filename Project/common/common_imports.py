from time import sleep
import os
from threading import Thread, Lock, Condition
from queue import Queue, Empty
import multiprocessing as mp
from multiprocessing import Process
from enum import Enum, auto

default_timeout = 15000
mini_wait = 5

class Operation(Enum):
    IMPORT = auto()
    EXPORT = auto()
    FIRMWARE = auto()
