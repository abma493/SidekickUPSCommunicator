from time import sleep
import os
import asyncio
import aiohttp
from threading import Thread, Lock, Condition
from queue import Queue, Empty
import multiprocessing as mp
from logger import Logger
from multiprocessing import Process
from enum import Enum, auto

# not uniformly used across the application
# TODO: Either remove entirely or make more use of it
default_timeout = 15000

class Operation(Enum):
    IMPORT = auto()
    EXPORT = auto()
    FIRMWARE = auto()
