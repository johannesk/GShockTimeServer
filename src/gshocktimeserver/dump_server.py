import asyncio
import sys
from datetime import datetime
import time

from connection import Connection
from gshock_api import GshockAPI
from casio_watch import WatchButton
from scanner import scanner
from configurator import conf
from logger import logger
from args import args
from api_tests import run_api_tests
from watch_info import watch_info
from result_queue import result_queue, KeyedResult
from utils import to_hex_string

__authors__ = ["Ivo Zivkov", "Johannes Krude"]
__license__ = "MIT"


async def main(argv):
    await run_dump_server()


async def run_dump_server():
    try:
        if args.get().multi_watch:
            address = None
        else:
            address = conf.get("device.address")

        device = await scanner.scan(address)
        logger.debug("Found: {}".format(device))

        connection = Connection(device)
        await connection.connect()

        api = GshockAPI(connection)

        #await api.set_time()

        futures = []

        def receive_raw(raw_data):
            hex_data = to_hex_string(raw_data)
            print(hex_data)
            sys.stdout.flush()
            futures.pop()["future"].set_result(True)

        api.subscribe_raw(receive_raw)

        async def request_raw(request):
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            futures.append({"request": bytearray(request), "future": future})
            await api.request_raw(request)
            await future;

        await request_raw([0x1d, 0])
        await request_raw([0x1d, 2])
        await request_raw([0x1d, 4])
        for i in range(0,6):
            await request_raw([0x1e, i])
        for i in range(0,6):
            await request_raw([0x1f, i])
        time.sleep(1)

        await connection.disconnect()

    except Exception as e:
        logger.error(f"Got error: {e}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
