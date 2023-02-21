
import uuid
import json
import threading
from tinydb import TinyDB, where
# from common.log import logger

"""
"Users": [{
    "user_id": "xxx",
    "nickname": "Alice",
    "is_paid": false,
    "is_used": false,
    "amount": 0,
    "payments": ["code1", "code2"]
}]
"Codes": [{
    "code": "xxxx",
    "used": false
}]
"""

_global_lock = threading.Lock()

class Payment(object):

    def __init__(self) -> None:
        self.db = TinyDB('db.json')
        self.users = self.db.table('Users')
        self.codes = self.db.table('Codes')
        self.loadCodes()
        
        self.test()

    def test(self):
        # result = self.codes.search(where('user') != '')
        # print(f'used codes: {result}')
        # state = self.use_code('123', 'ryan', "2")
        # print(f'use code state: {state}')
        is_newbie = self.is_newbie('123')
        print(f'is_newbie: {is_newbie}')
        has_amount = self.has_amount('123', 'nick')
        print(f'has_amount: {has_amount}')
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
            user = {
                "user_id": user_id,
                "nickname": nickname,
                "amount": 5, # 新用户送5次体验
            }
            print(f'create user: {user}')
            with _global_lock:
                self.users.insert(user)
        return user

    # 是否还有额度
    def has_amount(self, user_id, nickname):
        return self._amount_with_func(user_id, nickname)
            
    # 使用额度
    def use_amount(self, user_id, nickname):
        def function(amount):
            amount -= 1
            with _global_lock:
                self.users.update({'amount': amount}, where('user_id') == user_id)
        return self._amount_with_func(user_id, nickname, function)

    # 恢复额度 (请求失败等错误处理恢复额度)
    def recover_amount(self, user_id, nickname):
        def function(amount):
            amount += 1
            with _global_lock:
                self.users.update({'amount': amount}, where('user_id') == user_id)
        return self._amount_with_func(user_id, nickname, function)
    
    def _amount_with_func(self, user_id, nickname, function=None):
        user = self.search_user(user_id, nickname)
        amount = user['amount']
        if amount > 0:
            if function is not None:
                function(amount)
            return True
        else:
            return False


    """
    Codes
    """
    # 从文件中加载 code
    def loadCodes(self):
        content = ''
        with open('payment_codes', 'r') as file:
            content = file.read()

        codes_arr = json.loads(content)
        for code in codes_arr:
            result = self.codes.search(where('code') == code)
            if len(result) == 0:
                with _global_lock:
                    self.codes.insert({
                        "code": code,
                        "user": '',
                        "count": 100
                    })

    # 使用 code
    def use_code(self, user_id, nickname, code):
        result = self.codes.search(where('code') == code)
        print(f'result: {result}')
        if result and result[0]['user'] == '':
            count = result[0]['count']
            user = self.search_user(user_id, nickname)

            with _global_lock:
                self.codes.update({"user": user_id}, where('code') == code)
                self.users.update({'amount': user['amount'] + count}, where('user_id') == user_id)

            user['amount'] += count
            print(f'code: {code} used by: {user}')
            return True
        else:
            print(f'[ERROR] use code failed. user_id: {user_id}, nickname: {nickname}, code: {code}')
            return False

Payment()