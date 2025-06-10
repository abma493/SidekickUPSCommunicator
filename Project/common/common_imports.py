from time import sleep
import os
import asyncio
import aiohttp
from aiohttp import BasicAuth
from queue import Queue, Empty
import multiprocessing as mp
from logger import Logger
from enum import Enum, auto

# not uniformly used across the application
# TODO: Either remove entirely or make more use of it
default_timeout = 15000

class Operation(Enum):
    EXPORT = auto()
    IMPORT = auto()
    FIRMWARE = auto()
    DIAGNOSTICS = auto()

class ModeMismatch(Exception):
    def __init__(self, message):
        super().__init__()
        self.message: str = message
    def get_err_msg(self) -> str:
        return self.message

# parse the IPs in the batch file to a list of jobs 
# A job entry in the list is comprised of an IP and an ID
# IP is used to navigate to webcard website
# ID is used to provide a selector identifier to the widgets on screen   
def parse_to_list(path_to_batch: str) -> list:
    
    jobs = []

    with open(path_to_batch, 'r') as file:

        lines = [line.strip() for line in file.readlines() if line.strip()]
        for i, ip in enumerate(lines, 1):
            entry = {
                "ip": ip,
                "id": f'job-entry{i}'
            }
            Logger.log(f'appending {entry["ip"]}/{entry["id"]}')
            jobs.append(entry)

    return jobs