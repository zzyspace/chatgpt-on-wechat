import os
import uuid
import json
from common.utils import logger
from payment.gen_code import code_prefix

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
        # 新用户送5次体验
        trial_code = self.gen_serial()
        trial_code_info = self.new_code_info(trial_code, 5)
        user = self.new_user(user_id, nickname, trial_code_info)
        logger.info(f'create user: {user}')

        self.codes.insert_one(trial_code_info)
        self.users.insert_one(user)
        return user


    # 是否还有额度
    def get_amount(self, user_id, nickname = ''):
        return self._amount_with_func(user_id, nickname)
            
    # 使用额度
    def use_amount(self, user_id, nickname = ''):
        def function(code_info):
            amount = code_info['amount'] - 1
            self.codes.update_many({'code': code_info['code']}, {'$set': {'amount': amount}})
        return self._amount_with_func(user_id, nickname, function)

    # 恢复额度 (请求失败等错误处理恢复额度)
    def recover_amount(self, user_id, nickname = ''):
        def function(code_info):
            amount = code_info['amount'] + 1
            self.codes.update_many({'code': code_info['code']}, {'$set': {'amount': amount}})
        return self._amount_with_func(user_id, nickname, function)
    
    def _amount_with_func(self, user_id, nickname, function=None):
        user = self.search_user(user_id, nickname)
        code = user['code']
        if not code:
            return 0

        code_info = self.codes.find_one({'code': code})
        if code_info:
            amount = code_info['amount']
            if amount > 0:
                if function is not None:
                    function(code_info)
                return amount
            else:
                return 0
        else:
            return 0


    """
    Codes
    """
    # 从文件中加载 code
    def loadCodes(self):
        path = 'payment/payment_codes'
        if not os.path.exists(path):
            raise Exception('兑换码文件不存在，请根据 payment_codes_template 模板创建 payment_codes 文件')
        with open(path, 'r') as f:
            codes_arr = [line.strip() for line in f.readlines()]

        for code in codes_arr:
            result = self.codes.find_one({'code': code})
            if result is None:
                code_info = self.new_code_info(code, 100)
                self.codes.insert_one(code_info)

    # 使用 code
    def bind_code(self, user_id, nickname, code):
        code_info = self.codes.find_one({'code': code})
        if code_info:
            """
            注释是因为不同的 channel 会有不同的用户信息, 但是是同一个用户. 所以两个用户信息共用同一 code
            # 将此 code 从其他 user 上移除
            user_result = self.users.search((where('code') == code) & (where('user_id') != user_id))
            for user in user_result:
                    self.users.update({'code': ''}, where('user_id') == user['user_id'])
            """
            # 将当前 user 的卡合并
            if not self.users.find_one({'code': code, 'user_id': user_id}):
                # 如果不是绑定的此卡, 将原卡额度合并更新至此卡, 并绑定 (同时删除原卡余额)
                user = self.search_user(user_id, nickname)
                old_code = user['code']
                remain_amount = self.get_amount(user_id, nickname)
                code_amount = code_info['amount']

                if old_code:
                    self.codes.update_many({'code': old_code}, {'$set': {'amount': 0}})
                self.codes.update_many({'code': code}, {'$set': {'amount': remain_amount + code_amount}})
                self.users.update_many({'user_id': user_id}, {'$set': {'code': code}})

            logger.info(f'code: {code} used by: [{nickname}]({user_id})')
            return True
        else:
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
            "code": code_info['code']
        }

    def gen_serial(self):
        return self.code_prefix()+str(uuid.uuid4())

    def code_prefix(self):
        return code_prefix

# Payment()