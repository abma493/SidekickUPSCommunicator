from threading import Semaphore, Condition
from queue import Queue

comm_queue = Queue() # gonna take aggregate values as dictionary
sem_driver = Semaphore(0)
sem_UI = Semaphore(0)
queue_cond = Condition()


# send a request and receive a response
async def send_request(request_type: str, message=None):
    request = {
                            'request': request_type,
                            'message': message
    } 

    with queue_cond:
        comm_queue.put(request)
        queue_cond.notify() # let listen() know there's a request-- let go of lock too!
                
    sem_UI.acquire()
    response = dict(comm_queue.get()).get("message")
    return response
