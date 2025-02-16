
"""
dingtalk channel
"""
import asyncio
import tornado
import json
import requests
import hmac  
import hashlib  
import base64 
import io
from common import const
from auto_reply.reply import Reply
from payment.payment import Payment
from common.utils import logger
from concurrent.futures import ThreadPoolExecutor
from channel.dingtalk.tornado_utils import Application, route
from channel.channel import Channel
from config import conf, dynamic_conf, channel_conf
from channel.dingtalk.ding_access_token import AccessToken
from common.detector import DFADetector

sensitive_detector = DFADetector()
sensitive_detector.parse('common/keywords')
thread_pool = ThreadPoolExecutor(max_workers=8)

@route("/")
class DingtalkChannel(tornado.web.RequestHandler, Channel):
    _access_token = AccessToken()
    _payment = Payment()
    _reply = Reply()

    # Request Handler

    def post(self):
        timestamp = self.request.headers.get('timestamp', None)  
        sign = self.request.headers.get('sign', None)  
        app_secret = channel_conf(const.DINGTALK).get('app_secret')
        app_secret_enc = app_secret.encode('utf-8')  
        string_to_sign = '{}\n{}'.format(timestamp, app_secret)  
        string_to_sign_enc = string_to_sign.encode('utf-8')  
        hmac_code = hmac.new(app_secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()  
        my_sign = base64.b64encode(hmac_code).decode('utf-8')  
        if sign != my_sign:  
            return self.finish({"errcode":1,"msg":"wrong signature"})  

        data = json.loads(self.request.body)
        self.handle(data)
        ret = {"errcode":0,"msg":'success'}
        return self.finish(ret)

    def push_ding(self, msg, uid):
        try:
            # https://open.dingtalk.com/document/isvapp/send-single-chat-messages-in-bulk
            app_key = channel_conf(const.DINGTALK).get('app_key')
            resp = requests.post("https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend",
            data=json.dumps({
                "robotCode":app_key,
                "userIds":[uid],
                "msgKey":"sampleText",
                "msgParam":json.dumps({"content":msg})
            }),
            headers={"Content-Type":"application/json","x-acs-dingtalk-access-token":DingtalkChannel._access_token.get_access_token()})
            logger.info(f'[Ding] push_ding response: {resp.json()}')
        except Exception as e:
            logger.error(e)

    def push_img_ding(self, img, uid):
        try:
            app_key = channel_conf(const.DINGTALK).get('app_key')
            resp = requests.post("https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend",
            data=json.dumps({
                "robotCode":app_key,
                "userIds":[uid],
                "msgKey":"sampleImageMsg",
                "msgParam":json.dumps({"photoURL": img})
            }),
            headers={"Content-Type":"application/json","x-acs-dingtalk-access-token":DingtalkChannel._access_token.get_access_token()})
            logger.info(f'[Ding] push_img_ding response: {resp.json()}')
        except Exception as e:
            logger.error(e)

    # Channel

    @classmethod
    def startup(cls):
        # 运行服务
        loop = asyncio.get_event_loop()
        http_server = tornado.httpserver.HTTPServer(Application())
        print("Starting tornado on port [8080]", )
        http_server.listen(8080, "0.0.0.0")

        loop.run_forever()

    def handle(self, msg):
        bot_prefix = conf().get("single_chat_reply_prefix")
        content = msg['text']['content']
        nickname = msg['senderNick']
        from_user_id = msg['senderStaffId']
        logger.info(f"[Ding] receive msg: {json.dumps(msg, ensure_ascii=False)}\nuser: {nickname}\nid: {from_user_id}")

        # 新人
        if self._payment.is_newbie(from_user_id, nickname):
            logger.info(f'[Ding] new user: {from_user_id}')
            reply = self._reply.reply_newbie(from_user_id)
            self.send(bot_prefix + reply, from_user_id)
        # 敏感词
        if sensitive_detector.detect(content):
            reply = self._reply.reply_sensitive()
            self.send(reply, from_user_id)
        # 自动回复
        if self._reply.is_auto_reply(content):
            reply = self._reply.reply_with(from_user_id, nickname, content)
            self.send(bot_prefix + reply, from_user_id)
        # 使用兑换码
        elif content.startswith(const.PREFIX_CODE):
            bind_success = self._payment.bind_code(from_user_id, nickname, content)
            reply = ''
            if bind_success:
                reply = self._reply.reply_bound_code(from_user_id, nickname)
            else:
                reply = self._reply.reply_bound_invalid(from_user_id, nickname)
            self.send(bot_prefix + reply, from_user_id)
        elif content.startswith(const.PREFIX_REF):
            bind_success = self._payment.bind_referral(from_user_id, nickname, content)
            reply = ''
            if bind_success:
                reply = self._reply.reply_bound_referral()
                self.send(bot_prefix + reply, from_user_id)
                ref_user_id = content.lstrip(const.PREFIX_REF)
                ref_reply = self._reply.reply_bound_referral_rewards(ref_user_id, '')
                self.send(bot_prefix + ref_reply, ref_user_id)
            else:
                reply = self._reply.reply_bound_referral_invalid()
                self.send(bot_prefix + reply, from_user_id)

        else:
            payment_amount = self._payment.get_amount(from_user_id, nickname)
            # match_prefix = self.check_prefix(content, conf().get('single_chat_prefix'))
            logger.info(f'[Ding] payment amount: {payment_amount}')
            if payment_amount:#) & (match_prefix is not None):
                # if match_prefix != '':
                #     str_list = content.split(match_prefix, 1)
                #     if len(str_list) == 2:
                #         content = str_list[1].strip()
                
                img_match_prefix = self.check_prefix(content, conf().get('image_create_prefix'))
                if img_match_prefix:
                    content = content.split(img_match_prefix, 1)[1].strip()
                    thread_pool.submit(self._do_send_img, content, from_user_id)
                else:
                    if (content == '/clear'):
                        self._payment.recover_amount(from_user_id, nickname)
                    thread_pool.submit(self._do_send, content, from_user_id)
            else:
                reply = self._reply.reply_runout(from_user_id)
                self.send(bot_prefix + reply, from_user_id)


    def send(self, msg, receiver):
        logger.info('[Ding] sendMsg={}, receiver={}'.format(msg, receiver))
        self.push_ding(msg, receiver)

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                self._payment.use_amount(reply_user_id)
                self.send(conf().get("single_chat_reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            logger.exception(e)

    def _do_send_img(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['type'] = 'IMAGE_CREATE'
            img_url = super().build_reply_content(query, context)
            if not img_url:
                return

            # 图片发送
            logger.info('[Ding] sendImage, receiver={}'.format(reply_user_id))
            self._payment.use_amount(reply_user_id)
            self.push_img_ding(img_url, reply_user_id)
        except Exception as e:
            logger.exception(e)
    
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