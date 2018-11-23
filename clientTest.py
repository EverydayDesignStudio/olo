#
# import socket
#
# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.connect(('localhost', 15555))
# request = None
#
# try:
#     while request != 'quit':
#         request = input('>> ')
#         if request:
#             server.send(request.encode('utf8'))
#             response = server.recv(255).decode('utf8')
#             print(response)
# except KeyboardInterrupt:
#     server.close()

import asyncio, time

"""
Producer, simplely takes the urls and dump them into the queue
"""
async def produce(queue):
    if (int(time.time()) % 5 == 0):
        print("## producing ")
        item = str(int(time.time()) % 5)
        await queue.put(item)
        await queue.put(None) # poison pill to signal all the work is done
