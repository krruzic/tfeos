import logging
import sys

LOG_FORMAT = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, stream=sys.stdout)
