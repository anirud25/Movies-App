import logging
import os
from datetime import datetime

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_path=os.path.join(os.getcwd(),"logs",LOG_FILE) # Folder name logs
os.makedirs(logs_path,exist_ok=True)    
# Even if folder and file already exist, keep appending in it

# format for logs. logs/<datetime>.log/<datetime>.log
LOG_FILE_PATH = os.path.join(logs_path,LOG_FILE)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(lineno)d %(filename)s - %(levelname)s - %(message)s",
    level=logging.INFO,

)

# if __name__ =="__main__":
#     logging.info("Logging has started.. ")