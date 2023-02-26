import werobot
from config import channel_conf
from common import const
from common.utils import logger
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor

robot = werobot.WeRoBot(token=channel_conf(const.WECHAT_MP_SERVICE).get('token'))
thread_pool = ThreadPoolExecutor(max_workers=8)

@robot.text
def hello_world(msg):
    logger.info(f'[WX_MP_SERVICE] receive from: {msg.source} msg: {msg.content},')
    return WechatMPServiceChannel().handle(msg)

class WechatMPServiceChannel(Channel):
    @classmethod
    def startup(cls):
        logger.info('[WX_MP_SERVICE] ******** Service start! ********')
        robot.config['PORT'] = channel_conf(const.WECHAT_MP_SERVICE).get('port')
        robot.config["APP_ID"] = channel_conf(const.WECHAT_MP_SERVICE).get('app_id')
        robot.config["APP_SECRET"] = channel_conf(const.WECHAT_MP_SERVICE).get('app_secret')
        robot.config['HOST'] = '0.0.0.0'
        robot.run()
        
    def handle(self, msg, count=0):
        context = {}
        context['from_user_id'] = msg.source
        thread_pool.submit(self._do_send, msg.content, context)
        return "正在思考中..."


    def _do_send(self, query, context):
        reply_text = super().build_reply_content(query, context)
        logger.info('[WX_MP_SERVICE] reply content: {}'.format(reply_text))
        client = robot.client
        client.send_text_message(context['from_user_id'], reply_text)