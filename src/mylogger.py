"""
:Author: Balazs Szigeti <b.islander@protonmail.com>
:Copyright: 2020, DrugNerdsLab
:License: MIT
"""

import traceback
import logging
import sys
import os


src_folder = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(src_folder, os.pardir))
log_path = os.path.join(base_dir, "psynudge.log")

logging.basicConfig(
    level=logging.INFO,
    filename=log_path,
    datefmt='%Y-%m-%d - %H:%M:%S',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s')

psylog = logging.getLogger("psylog")

def log_exception(*exc_info):
    text = "".join(traceback.format_exception(*exc_info))
    logging.error("Unhandled exception: %s", text)

sys.excepthook = log_exception

#None()
