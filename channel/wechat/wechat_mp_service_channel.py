import werobot
import json
from werobot.client import Client
from config import channel_conf
from common import const
from common.utils import logger
from config import conf, dynamic_conf
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor

from common import const
from auto_reply.reply import Reply
from payment.payment import Payment

robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP_SERVICE).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)

@robot.text
def hello_world(msg):
    logger.info(f'[WX_MP_SERVICE] receive from: {msg.source} msg: {msg.content},')
    return WechatMPServiceChannel().handle(msg)

class WechatMPServiceChannel(Channel):
    _payment = Payment()
    _reply = Reply()

    @classmethod
    def startup(cls):
        logger.info('[WX_MP_SERVICE] ******** Service start! ********')
        robot.config['PORT'] = channel_conf(const.WECHAT_MP_SERVICE).get('port')
        robot.config["APP_ID"] = channel_conf(const.WECHAT_MP_SERVICE).get('app_id')
        robot.config["APP_SECRET"] = channel_conf(const.WECHAT_MP_SERVICE).get('app_secret')
        robot.config['HOST'] = '0.0.0.0'
        robot.run()
        
    def handle(self, msg, count=0):
        user_id = msg.source
        nickname = ''
        content = msg.content
        logger.info(f"[WX_MP_SERVICE] receive:\nuser: {nickname}\nid: {user_id}\ncontent: {content}")

        # 新人
        if self._payment.is_newbie(user_id, nickname):
            reply = self._reply.reply_newbie()
            self.send(reply, user_id)
            self._fetch_user_info(user_id)
        # 自动回复
        elif self._reply.is_auto_reply(content):
            reply = self._reply.reply_with(user_id, nickname, content)
            self.send(reply, user_id)
        # 使用兑换码
        elif content.startswith(const.PREFIX_CODE):
            bind_success = self._payment.bind_code(user_id, nickname, content)
            reply = ''
            if bind_success:
                reply = self._reply.reply_bound_code(user_id, nickname)
            else:
                reply = self._reply.reply_bound_invalid(user_id, nickname)
            self.send(reply, user_id)
        elif content.startswith(const.PREFIX_REF):
            bind_success = self._payment.bind_referral(user_id, nickname, content)
            reply = ''
            if bind_success:
                reply = self._reply.reply_bound_referral()
            else:
                reply = self._reply.reply_bound_referral_invalid()
            self.send(reply, user_id)

        else:
            payment_amount = self._payment.get_amount(user_id, nickname)
            logger.info(f'[WX_MP_SERVICE] payment amount: {payment_amount}')

            if payment_amount:
                # img_match_prefix = self.check_prefix(content, conf().get('image_create_prefix'))
                # if img_match_prefix:
                #     content = content.split(img_match_prefix, 1)[1].strip()
                #     self._do_send_img(content, from_user_id)
                # else:
                if (content == '/clear'):
                    self._payment.recover_amount(user_id, nickname)
                thread_pool.submit(self._do_send, content, user_id)
            else:
                reply = self._reply.reply_runout()
                self.send(reply, user_id)

        # return "正在思考中..."

    def send(self, msg, receiver):
        logger.info(f"[WX_MP_SERVICE] reply:\nuser_id: {receiver}\ncontent: {msg}")
        client = robot.client
        client.send_text_message(receiver, msg)

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = {}
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            logger.info(f'[WX_MP_SERVICE] reply: {reply_text}')
            if reply_text:
                self._payment.use_amount(reply_user_id)
                self.send(reply_text, context['from_user_id'])
        except Exception as e:
            logger.error(e)

    def _fetch_user_info(self, user_id):
        """
        {'subscribe': 1, 'openid': 'oV2je6v3Iuf-mXT5atczEe2kr40U', 'nickname': '', 'sex': 0, 'language': 'zh_CN', 'city': '', 'province': '', 'country': '', 'headimgurl': '', 'subscribe_time': 1677398414, 'remark': '', 'groupid': 0, 'tagid_list': [], 'subscribe_scene': 'ADD_SCENE_QR_CODE', 'qr_scene': 0, 'qr_scene_str': ''}
        """
        res = robot.client.get_user_info(user_id)
        self._payment.set_nickname(user_id, res['nickname'])