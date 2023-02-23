import os
import uuid
import json
import threading
from tinydb import TinyDB, where
from common.log import logger
from payment.gen_code import code_prefix

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

_global_lock = threading.Lock()

class Payment(object):

    def __init__(self) -> None:
        self.db = TinyDB('payment/db.json')
        self.users = self.db.table('Users')
        self.codes = self.db.table('Codes')
        self.loadCodes()
        
        # self.test()

    def test(self):
        # result = self.codes.search(where('user') != '')
        # print(f'used codes: {result}')
        # state = self.use_code('123', 'ryan', "2")
        # print(f'use code state: {state}')
        is_newbie = self.is_newbie('123')
        logger.info(f'is_newbie: {is_newbie}')
        has_amount = self.has_amount('123', 'nick')
        logger.info(f'has_amount: {has_amount}')
        self.use_amount('123','abc')

    """
    Users
    """
    # 是否新人 (仅查找, 不自动创建不存在的用户)
    def is_newbie(self, user_id):
        result = self.users.search(where('user_id') == user_id)
        if result:
            return False
        else:
            return True

    # 查找用户, 不存在则创建并返回
    def search_user(self, user_id, nickname = 'Unknow'):
        result = self.users.search(where('user_id') == user_id)
        user = {}
        if result:
            user = result[0]
            user['nickname'] = nickname
            with _global_lock:
                self.users.update({'nickname': nickname}, where('user_id') == user_id)
        else:
            # 新用户送5次体验
            trial_code = self.gen_serial()
            trial_code_info = self.new_code(trial_code, 5)
            user = self.new_user(user_id, nickname, trial_code_info)
            logger.info(f'create user: {user}')
            with _global_lock:
                self.codes.insert(trial_code_info)
                self.users.insert(user)
        return user

    # 是否还有额度
    def has_amount(self, user_id, nickname):
        return self._amount_with_func(user_id, nickname)
            
    # 使用额度
    def use_amount(self, user_id, nickname):
        def function(code_info):
            amount = code_info['amount'] - 1
            with _global_lock:
                self.codes.update({'amount': amount}, where('code') == code_info['code'])
        return self._amount_with_func(user_id, nickname, function)

    # 恢复额度 (请求失败等错误处理恢复额度)
    def recover_amount(self, user_id, nickname):
        def function(code_info):
            amount = code_info['amount'] + 1
            with _global_lock:
                self.users.update({'amount': amount}, where('code') == code_info['code'])
        return self._amount_with_func(user_id, nickname, function)
    
    def _amount_with_func(self, user_id, nickname, function=None):
        user = self.search_user(user_id, nickname)
        code = user['code']
        result = self.codes.search(where('code') == code)
        if result:
            code_info = result[0]
            amount = code_info['amount']
            if amount > 0:
                if function is not None:
                    function(code_info)
                return True
            else:
                return False
        else:
            return False


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
            result = self.codes.search(where('code') == code)
            if len(result) == 0:
                with _global_lock:
                    code = self.new_code(code, 100)
                    self.codes.insert(code)

    # 使用 code
    def bind_code(self, user_id, nickname, code):
        result = self.users.search(where('code') == code & where('user_id') != user_id)
        with _global_lock:
            for user in result:
                self.users.update({'code': ''}, where('user_id') == user['user_id'])
            self.users.update({'code': code}, where('user_id') == user_id)
        logger.info(f'code: {code} used by: [{nickname}]({user_id})')

        return True

        # result = self.codes.search(where('code') == code)
        # print(f'result: {result}')
        # if result and result[0]['user'] == '':
        #     count = result[0]['count']
        #     user = self.search_user(user_id, nickname)

        #     with _global_lock:
        #         self.codes.update({"user": user_id}, where('code') == code)
        #         self.users.update({'amount': user['amount'] + count}, where('user_id') == user_id)

        #     user['amount'] += count
        #     print(f'code: {code} used by: {user}')
        #     return True
        # else:
        #     print(f'[ERROR] use code failed. user_id: {user_id}, nickname: {nickname}, code: {code}')
        #     return False

    def new_code(self, code, amount):
        return {
            "code": code,
            "amount": amount
        }
    
    def new_user(self, user_id, nickname, code_info):
        print(code_info)
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