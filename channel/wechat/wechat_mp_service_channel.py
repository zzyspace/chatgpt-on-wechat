import werobot
import json
import time
import requests
from werobot.client import Client
from io import BytesIO
from config import channel_conf
from common import const
from common.utils import logger
from config import conf, dynamic_conf
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.detector import DFADetector

from common import const
from auto_reply.reply import Reply
from payment.payment import Payment

robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP_SERVICE).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)
sensitive_detector = DFADetector()
sensitive_detector.parse('common/keywords')

robot.client.create_menu({
    'button': [
        {
            'name': '我要额度',
            'sub_button': [
                {
                    'type': 'click',
                    'name': '我的额度',
                    'key': 'amount_query'
                },
                {
                    'type': 'click',
                    'name': '获取免费额度',
                    'key': 'amount_free'
                },
                {
                    'type': 'click',
                    'name': '兑换码购买',
                    'key': 'amount_buy'
                }
            ]
        },
        {
            'name': '功能',
            'sub_button': [
                {
                    'type': 'click',
                    'name': '清除上下文记忆',
                    'key': 'func_clear'
                },
                {
                    'type': 'click',
                    'name': '帮助',
                    'key': 'func_help'
                }
            ]
        },
        {
            'name': '关于我们',
            'sub_button': [
                {
                    'type': 'click',
                    'name': '联系我们',
                    'key': 'about_us'
                },
                {
                    'type': 'click',
                    'name': '商务合作',
                    'key': 'about_cooperation'
                }
            ]
        }
    ]
})

@robot.key_click('amount_query')
def amount_query(msg):
    msg['content'] = '/info'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('amount_free')
def amount_free(msg):
    msg['content'] = '/amount_free'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('amount_buy')
def amount_buy(msg):
    msg['content'] = '/amount_buy'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('func_clear')
def func_clear(msg):
    msg['content'] = '/clear'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('func_help')
def func_help(msg):
    msg['content'] = '/help'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('about_us')
def about_us(msg):
    msg['content'] = '/about_us'
    WechatMPServiceChannel().handle(msg)

@robot.key_click('about_cooperation')
def about_cooperation(msg):
    msg['content'] = '/about_us'
    WechatMPServiceChannel().handle(msg)

@robot.text
def hello_world(msg):
    return WechatMPServiceChannel().handle(msg)

@robot.image
def receive_img(msg):
    if msg.source == 'oZbIF5226smPC9DoELmwYZunqtLU':
        img_url = msg.img
        res = requests.get(img_url)
        file_object = BytesIO(res.content)
        result = robot.client.upload_permanent_media('image', file_object)
        return json.dumps(json['media_id'])


@robot.subscribe
def subscribe(msg):
    if msg.source != 'oZbIF5226smPC9DoELmwYZunqtLU':
        return
    media_id = ''
    robot.client.send_image_message(msg.source, media_id)


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
        logger.info(f"[WX_MP_SERVICE]\n[receive]:\nuser: {nickname}\nid: {user_id}\ncontent: {content}")

        # 新人
        if self._payment.is_newbie(user_id, nickname):
            # pass
            reply = self._reply.reply_newbie(user_id)
            self.send(reply, user_id)
            # self._fetch_user_info(user_id)
        # 敏感词
        if sensitive_detector.detect(content):
            reply = self._reply.reply_sensitive()
            self.send(reply, user_id)
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
        # 使用推荐码
        elif content.startswith(const.PREFIX_REF):
            bind_success = self._payment.bind_referral(user_id, nickname, content)
            reply = ''
            if bind_success:
                reply = self._reply.reply_bound_referral()
                self.send(reply, user_id)
                ref_user_id = content.lstrip(const.PREFIX_REF)
                ref_reply = self._reply.reply_bound_referral_rewards(ref_user_id, '')
                self.send(ref_reply, ref_user_id)
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
                reply = self._reply.reply_runout(user_id)
                self.send(reply, user_id)

        # return "正在思考中..."

    def send(self, msg, receiver):
        logger.info(f"[WX_MP_SERVICE]\n[reply]:\nuser_id: {receiver}\ncontent: {msg}")
        client = robot.client
        client.send_text_message(receiver, msg)

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = {}
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            # logger.info(f'[WX_MP_SERVICE] reply: {reply_text}')
            if reply_text:
                self._payment.use_amount(reply_user_id)
                reply_arr = self._split_string(reply_text, 600)
                for reply_chunk in reply_arr:
                    self.send(reply_chunk, context['from_user_id'])
                    time.sleep(0.5)
        except Exception as e:
            logger.error(e)

    def _fetch_user_info(self, user_id):
        """
        {'subscribe': 1, 'openid': 'oV2je6v3Iuf-mXT5atczEe2kr40U', 'nickname': '', 'sex': 0, 'language': 'zh_CN', 'city': '', 'province': '', 'country': '', 'headimgurl': '', 'subscribe_time': 1677398414, 'remark': '', 'groupid': 0, 'tagid_list': [], 'subscribe_scene': 'ADD_SCENE_QR_CODE', 'qr_scene': 0, 'qr_scene_str': ''}
        """
        res = robot.client.get_user_info(user_id)
        self._payment.set_nickname(user_id, res['nickname'] if res['nickname'] else '未知')

    def _split_string(self, s, max_length):
        result = []
        start = 0
        while start < len(s):
            end = start + max_length
            if end < len(s):
                # 如果字符串长度超过max_length，则从最后一个空格处分割
                end = s.rfind("。", start, end)
                if end == -1:
                    end = start + max_length
                else:
                    end += 1
            result.append(s[start:end])
            start = end
        return result