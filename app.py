# encoding:utf-8

import config
from channel import channel_factory
from common.utils import logger
from common import const


if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        # create channel
        channel = channel_factory.create_channel(const.WECHAT_MP_SERVICE)

        # startup channel
        # channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)
