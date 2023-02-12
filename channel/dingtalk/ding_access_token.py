import threading
import time
import requests
import json
from config import conf, dynamic_conf
from common.log import logger

class AccessToken:
    def __init__(self):
        self.access_token = None
        self.interval = 10#3600  # Access token refresh interval in seconds
        self.lock = threading.Lock()
        self.update_thread = threading.Thread(target=self.update_token, args=())
        self.update_thread.start()
        logger.info("[Ding] init access_token")

    def update_token(self):
        while True:
            # Request access_token from the API
            app_key = dynamic_conf()['global']['ding_app_key']
            app_secret = dynamic_conf()['global']['ding_app_secret']
            response = requests.post("https://api.dingtalk.com/v1.0/oauth2/accessToken",
                                    data=json.dumps({"appKey": app_key,"appSecret": app_secret}),
                                    headers={"Content-Type":"application/json"})  

            if response.status_code == 200:
                access_token = response.json()["accessToken"]
                with self.lock:
                    self.access_token = access_token
                logger.info("[Ding] updated access_token")
            else:
                logger.info("[Ding] Error: Unable to fetch access_token")
            time.sleep(self.interval)

    def get_access_token(self):
        with self.lock:
            return self.access_token
