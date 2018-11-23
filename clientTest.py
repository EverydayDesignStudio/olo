import asyncio

async def produce(queue):
    while True:
        # produce an item
        item = input("what to do? ")
        print(item)
        # simulate i/o operation using sleep
        # await asyncio.sleep(1)
        # put the item in the queue
        await queue.put(item)
