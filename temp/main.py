# main.py
import threading
import thread1
import thread2

# Create lock in main
shared_lock = threading.Lock()

# Explicitly assign the lock to the modules
thread1.lock = shared_lock  
thread2.lock = shared_lock

t1 = threading.Thread(target=thread1.thread1_function)
t2 = threading.Thread(target=thread2.thread2_function)

t1.start()
t2.start()