# encoding:utf-8

import config
from channel import channel_factory
from common.utils import logger
from common import const


if __name__ == '__main__':
    try:
        # load config
        config.load_config()

        # model_type = config.conf().get("model").get("type")
        channel_type = config.conf().get("channel").get("type")

        logger.info(f"[INIT] Start up on channel: {channel_type}")

        # create channel
        channel_factory.create_channel(channel_type)

        # startup channel
        # channel.startup()
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)
