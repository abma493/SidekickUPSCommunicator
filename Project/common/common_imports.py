from time import sleep
import os
from threading import Thread, Lock, Condition
from queue import Queue, Empty
import multiprocessing as mp
from multiprocessing import Process

default_timeout = 0
mini_wait = 5
current_mode: str = "Single (Default)"
path_to_batch = ""
path_to_config = ""