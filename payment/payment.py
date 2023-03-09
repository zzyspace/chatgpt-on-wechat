import os
import uuid
import json
import config
from common.utils import logger
from common import const

from pymongo import MongoClient

"""
"Users": [{
    "user_id": "xxx",
    "nickname": "Alice",
    "code": "code"
}]
"Codes": [{
    "code": "xxxx",
    "amount": 0,
}]
"""

class Payment(object):

    def __init__(self) -> None:
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.chatgpt_db
        self.users = self.db.Users
        self.codes = self.db.Codes
        self.loadCodes()
        
        # self.test()

    def test(self):
        # result = self.codes.search(where('user') != '')
        # print(f'used codes: {result}')
        # state = self.use_code('123', 'ryan', "2")
        # print(f'use code state: {state}')
        is_newbie = self.is_newbie('123')
        logger.info(f'is_newbie: {is_newbie}')
        has_amount = self.get_amount('123', 'nick')
        logger.info(f'has_amount: {has_amount}')
        self.use_amount('123','abc')

    """
    Users
    """
    # 是否新人 
    def is_newbie(self, user_id, nickname):
        user = self.users.find_one({'user_id': user_id})
        if user:
            return False
        else:
            self.create_user(user_id, nickname)
            return True
    
    # 持久化用户名
    def set_nickname(self, user_id, nickname):
        if nickname:
            user = self.users.update_many({'user_id': user_id}, {'$set': {'nickname': nickname}})


    # 查找用户, 不存在则创建并返回
    def search_user(self, user_id, nickname = ''):
        user = self.users.find_one({'user_id': user_id})
        if user:
            user['nickname'] = nickname if nickname else user['nickname']
            self.users.update_many(
                {'user_id': user_id}, 
                {'$set': {'nickname': user['nickname']}}
            )
        else:
            user = self.create_user()
        return user
    
    def create_user(self, user_id, nickname):
        # 新用户送10次体验
        trial_code = self.gen_serial()
        trial_code_info = self.new_code_info(trial_code, 10)
        user = self.new_user(user_id, nickname, trial_code_info)

        self.codes.insert_one(trial_code_info)
        self.users.insert_one(user)

        logger.info(f'[DB] create user: {user}')
        return user


    # 是否还有额度
    def get_amount(self, user_id, nickname = ''):
        return self._amount_with_func(user_id, nickname)
            
    # 使用额度
    def use_amount(self, user_id, nickname = ''):
        logger.info(f'[DB] use_amount by {nickname}({user_id})')
        def function(code_info):
            amount = code_info['amount'] - 1
            self.codes.update_many({'code': code_info['code']}, {'$set': {'amount': amount}})
        return self._amount_with_func(user_id, nickname, function)

    # 恢复额度 (请求失败等错误处理恢复额度)
    def recover_amount(self, user_id, nickname = '', count = 1):
        logger.info(f'[DB] increse_amount by {nickname}({user_id})')
        def function(code_info):
            amount = code_info['amount'] + count
            self.codes.update_many({'code': code_info['code']}, {'$set': {'amount': amount}})
        return self._amount_with_func(user_id, nickname, function)
    
    def _amount_with_func(self, user_id, nickname, function=None):
        user = self.search_user(user_id, nickname)
        if not user:
            return 0
        code = user['code']
        if not code:
            return 0

        code_info = self.codes.find_one({'code': code})
        if code_info:
            amount = code_info['amount']
            if function is not None:
                function(code_info)
            return amount
        else:
            return 0


    """
    Codes
    """
    # 从文件中加载 code
    def loadCodes(self):
        pass

    # 使用 code
    def bind_code(self, user_id, nickname, code):
        code_info = self.codes.find_one({'code': code})
        if code_info and code_info['amount'] != 0:
            """
            注释是因为不同的 channel 会有不同的用户信息, 但是是同一个用户. 所以两个用户信息共用同一 code
            # 将此 code 从其他 user 上移除
            user_result = self.users.search((where('code') == code) & (where('user_id') != user_id))
            for user in user_result:
                    self.users.update({'code': ''}, where('user_id') == user['user_id'])
            """
            user = self.search_user(user_id, nickname)
            current_channel = user['channel']

            # 当前 channel 已有其他 user 绑定了这个 code
            if self.users.find({'code': code, 'channel': current_channel}):
                logger.info(f'[DB] code: {code} used failed by: [{nickname}]({user_id}), channel: {current_channel}, reason: already used')
                return False

            # 将当前 user 的卡合并
            if not self.users.find_one({'code': code, 'user_id': user_id}):
                # 如果不是绑定的此卡, 将原卡额度合并更新至此卡, 并绑定 (同时删除原卡余额)
                old_code = user['code']
                remain_amount = self.get_amount(user_id, nickname)
                code_amount = code_info['amount']

                if old_code:
                    self.codes.update_many({'code': old_code}, {'$set': {'amount': 0}})
                self.codes.update_many({'code': code}, {'$set': {'amount': remain_amount + code_amount}})
                self.users.update_many({'user_id': user_id}, {'$set': {'code': code}})

            logger.info(f'[DB] code: {code} used by: [{nickname}]({user_id})')
            return True
        else:
            return False

    def bind_referral(self, user_id, nickname, referral):
        ref_user_id = referral.lstrip(const.PREFIX_REF)
        ref_user = self.search_user(ref_user_id)
        user = self.search_user(user_id, nickname)
        # 没绑过 referral 且 不是本人的码 且 本渠道的码
        if not user['referral'] and user_id != ref_user_id and user['channel'] == ref_user['channel']:
            # 绑定推荐码
            self.users.update_many({'user_id': user_id}, {'$set': {'referral': referral}})
            # 推荐人+10次
            self.recover_amount(ref_user_id, '', 10)
            return True
        else:
            # 已有推荐码, 不能绑定
            return False
        

    def new_code_info(self, code, amount):
        return {
            "code": code,
            "amount": amount
        }
    
    def new_user(self, user_id, nickname, code_info):
        return {
            "user_id": user_id,
            "nickname": nickname,
            "code": code_info['code'],
            "channel": config.conf()["channel"]["type"],
            "referral": ""
        }

    def gen_serial(self):
        return const.PREFIX_CODE+str(uuid.uuid4())


# Payment()