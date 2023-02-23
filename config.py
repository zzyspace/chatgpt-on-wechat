# encoding:utf-8

import json
import os
from common.log import logger
import configparser

config = {}
dynamic_config = configparser.ConfigParser()
dynamic_config_path = "dynamic-config.conf"

def load_config():
    global config
    config_path = "config.json"
    if not os.path.exists(config_path):
        raise Exception('配置文件不存在，请根据config-template.json模板创建config.json文件')

    config_str = read_file(config_path)
    # 将json字符串反序列化为dict类型
    config = json.loads(config_str)
    logger.info("[INIT] load config: {}".format(config))

    if not os.path.exists(dynamic_config_path):
        raise Exception('配置文件不存在，请根据dynamic-config-template.json模板创建dynamic-config.json文件')


def get_root():
    return os.path.dirname(os.path.abspath( __file__ ))


def read_file(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return f.read()


def conf():
    return config


def dynamic_conf():
    dynamic_config.read(dynamic_config_path, encoding='utf-8')
    return dynamic_config