import logging
import time
import datetime

logging.basicConfig(level=logging.INFO)

logging.info(msg="Tado Optimizer starting")

for i in range(10):
    logging.info(msg=f"The time is {datetime.datetime.now()}")
    time.sleep(10)

