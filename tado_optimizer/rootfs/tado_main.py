import logging
import time
import datetime

logging.basicConfig(filename="logfile.log", level=logging.INFO,
                    format="%(asctime)s : %(levelname)s : %(filename)s line %(lineno)d : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logging.info(msg="Tado Optimizer starting")

for i in range(10):
    logging.info(msg=f"The time is {datetime.datetime.now()}")
    time.sleep(10)

