"""
channel factory
"""

from common import const

def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == const.WECHAT:
        from channel.wechat.wechat_channel import WechatChannel
        return WechatChannel.startup()
    if channel_type == const.WECHAT_MP_SERVICE:
        from channel.wechat.wechat_mp_service_channel import WechatMPServiceChannel
        return WechatMPServiceChannel.startup()
    if channel_type == const.DINGTALK:
        from channel.dingtalk.dingtalk_channel import DingtalkChannel
        return DingtalkChannel.startup()
    raise RuntimeError