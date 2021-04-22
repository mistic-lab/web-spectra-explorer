import numpy as np
import h5py
import time
import msgpack_numpy as m
m.patch()
# import redis
import zmq

import rfind_monitor.const as const

def producer(verbose=False):

    pusher_addr = const.ZMQ_PROTOCOL+"://"+const.ZMQ_IP_PUSH+":"+const.ZMQ_PORT

    context = zmq.Context()
    zmq_socket = context.socket(zmq.PUSH)
    zmq_socket.connect(pusher_addr)

    # redis_client = redis.Redis(host=const.REDIS_REMOTE_IP, port=const.REDIS_PORT, db=0, password=const.REDIS_REMOTE_PASSWORD, username=const.REDIS_REMOTE_USER)

    with h5py.File(const.SOURCE_H5,'r') as h5f:
        if verbose: print(f"Using {const.SOURCE_H5} as file source")

        modlen = len(h5f['times'])

        i=0
        while True:
            if verbose: print(f"Trying to send iteration {i} to redis store")
            spec = np.array(h5f['spec'][i % modlen]).tolist()
            timestamp = h5f['times'][i % modlen]
            spec.append(timestamp)
            msg = m.packb(spec)
            try:
                # redis_client.set('latest',msg)
                zmq_socket.send(msg,'latest')
                if verbose: print("-- Succeeded")
            except Exception as e:
                if verbose: print(f"-- Failed: {e}")
            time.sleep(const.INTEGRATION_RATE/1000)
            i+=1


producer(verbose=True)

