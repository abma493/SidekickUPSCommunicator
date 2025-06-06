from threading import Semaphore, Condition
from queue import Queue

comm_queue = Queue() # a message at a time, where the message is a dictionary struct
sem_driver = Semaphore(0)
sem_UI = Semaphore(0)
queue_cond = Condition()


# send a request and receive a response
#params:
#
#
#   is_request: Since we are using a single queue for both requests/responses
#               this bool determines whether the listen() func in driver
#               should obviate the message (if it's a response meant for the UI)
#               or process it (if it's a request coming in from the UI)
async def send_request(request_type: str, message=None, is_request=True):
    
    request = {
                            'request': request_type,
                            'message': message,
                            'is_request': is_request
    } 

    with queue_cond:
        comm_queue.put(request)
        queue_cond.notify() # listen() in driver gets request
                
    sem_UI.acquire()
    response = dict(comm_queue.get()).get("message")

    return response



