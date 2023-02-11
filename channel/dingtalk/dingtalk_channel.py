
"""
dingtalk channel
"""
import asyncio
import tornado
import json
import requests
from common.log import logger
from concurrent.futures import ThreadPoolExecutor
from channel.dingtalk.tornado_utils import Application, route
from channel.channel import Channel
from config import conf, dynamic_conf

thread_pool = ThreadPoolExecutor(max_workers=8)

@route("/")
class DingtalkChannel(tornado.web.RequestHandler, Channel):
    # def __init__(self):
    #     pass

    # Request Handler

    def get(self):
        return self.write_json({"ret": 200})

    def post(self):

        request_data = self.request.body
        data = json.loads(request_data)
        # msg = data['text']['content']

        return self.handle(data)

    def write_json(self, struct):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(tornado.escape.json_encode(struct))

    def notify_dingding(self, answer):
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "chatgpt: ",
                "text": answer
            },

            "at": {
                "atMobiles": [
                    ""
                ],
                "isAtAll": False
            }
        }

        notify_url = f"https://oapi.dingtalk.com/robot/send?access_token={dd_token}"
        try:
            r = requests.post(notify_url, json=data)
            reply = r.json()
            logger.info("dingding: " + str(reply))
        except Exception as e:
            logger.error(e)

    # Channel

    @classmethod
    def startup(self):
        # 运行服务
        loop = asyncio.get_event_loop()
        http_server = tornado.httpserver.HTTPServer(Application())
        print("Starting tornado on port [8080]", )
        http_server.listen(8080, "0.0.0.0")

        loop.run_forever()

    def handle(self, msg):
        logger.debug("[Ding]receive msg:", json.dumps(msg, ensure_ascii=False))
        content = msg['text']['content']
        from_user_id = '' # TODO
        match_prefix = self.check_prefix(content, conf().get('single_chat_prefix'))
        match_payment = True #self.check_payment(msg['User']['NickName']) # TODO
        logger.debug(f'[Ding] match: {match_prefix is not None}, {match_payment}')
        logger.debug(content)
        if match_payment and match_prefix is not None:
            if match_prefix != '':
                logger.debug(1)
                str_list = content.split(match_prefix, 1)
                if len(str_list) == 2:
                    content = str_list[1].strip()
            
                img_match_prefix = self.check_prefix(content, conf().get('image_create_prefix'))
                if img_match_prefix:
                    content = content.split(img_match_prefix, 1)[1].strip()
                    return thread_pool.submit(self._do_send_img, content, from_user_id)
                else:
                    logger.debug(2)
                    return thread_pool.submit(self._do_send, content, from_user_id)
            
            return self.write_json({"ret": 400})
        
        return self.write_json({"ret": 400})


    def send(self, msg, receiver):
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))
        self.notify_dingding(msg)
        return self.write_json({"ret": 200})

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                logger.debug(3)
                return self.write_json({"ret": 400})
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:

                logger.debug('4', reply_text)
                return self.send(conf().get("single_chat_reply_prefix") + reply_text, reply_user_id)
            return self.write_json({"ret": 400})
        except Exception as e:
            logger.exception(e)
            return self.write_json({"ret": 400})
    
    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None

    def check_payment(self, nickname):
        white_list = json.loads(dynamic_conf()['white_list']['ids'])
        return nickname in white_list

    def check_group_payment(self, groupname):
        group_white_list = json.loads(dynamic_conf()['group_white_list']['ids'])
        return groupname in group_white_list