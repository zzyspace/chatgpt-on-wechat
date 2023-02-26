"""
channel factory
"""

from common import const
from channel.wechat.wechat_channel import WechatChannel
from channel.wechat.wechat_mp_service_channel import WechatMPServiceChannel
from channel.dingtalk.dingtalk_channel import DingtalkChannel

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == const.WECHAT:
        return WechatChannel.startup()
    if channel_type == const.WECHAT_MP_SERVICE:
        return WechatMPServiceChannel.startup()
    if channel_type == const.DINGTALK:
        return DingtalkChannel.startup()
    raise RuntimeError