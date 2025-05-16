from time import sleep
import os
from threading import Thread, Lock, Condition
from queue import Queue, Empty
import multiprocessing as mp
from multiprocessing import Process
from enum import Enum, auto

# not uniformly used across the application
# TODO: Either remove entirely or make more use of it
default_timeout = 15000

# Arbitrary waits for synchronization are HIGHLY discouraged.
# This var in particular was used in early development to
# compensate for what appeared to be "long-to-load" html resources
# TODO: Obliterate the use of this variable!
mini_wait = 5 

class Operation(Enum):
    IMPORT = auto()
    EXPORT = auto()
    FIRMWARE = auto()
