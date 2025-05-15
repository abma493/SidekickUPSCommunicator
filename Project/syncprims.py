from threading import Semaphore
from asyncio import Condition
from queue import Queue

comm_queue = Queue() # a message at a time, where the message is a dictionary struct
sem_driver = Semaphore(0)
sem_UI = Semaphore(0)
queue_cond = Condition()


# send a request and receive a response
async def send_request(request_type: str, message=None):
    
    request = {
                            'request': request_type,
                            'message': message
    } 

    async with queue_cond:
        comm_queue.put(request)
        queue_cond.notify() # listen() in driver gets request
                
    sem_UI.acquire()
    response = dict(comm_queue.get()).get("message")
    return response
