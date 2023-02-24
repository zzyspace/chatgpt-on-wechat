
import shutil
import threading
from tinydb import TinyDB, where
from tinyrecord import transaction

# 备份数据库文件
shutil.copy2('payment/db.json', 'payment/db_backup.json')

# 加载数据库文件，创建数据库实例
db = TinyDB('payment/db.json')
users = db.table('Users')
codes = db.table('Codes')

_global_lock = threading.Lock()

# 移除用户
def remove_user(user_id):
    # 创建事务
    with transaction(users) as txn:
        txn.remove(where('user_id') == user_id)

# 添加 code 额度
def add_code_amount(code, add_amount):
    with transaction(codes) as txn:
        code_info = codes.search(where('code') == code)
        amount = code_info['amount'] + add_amount
        with _global_lock:
            txn.update({'amount': amount}, where('code') == code_info['code'])



remove_user('044535556426224740')
add_code_amount('c4ea-be286dc1-1ce0-4f52-b4de-5e66da1e5a4d', 50)
add_code_amount('c4ea-2da0f647-bac4-4d46-ac1a-0a8bf4b7142a', 50)
add_code_amount('c4ea-f05ac56f-f11e-4a20-a07c-56a39116bf14', 50)
add_code_amount('c4ea-2e490c94-6bb0-4f83-b126-46eef986957d', 50)

    # txn.insert({
    #     'user_id': '080567406620809',
    #     'nickname': '光',
    #     'code': 'c4ea-be286dc1-1ce0-4f52-b4de-5e66da1e5a4d'
    # })
    # txn.insert({
    #     'user_id': '044535556426224740',
    #     'nickname': '曹步驰',
    #     'code': 'c4ea-57bd396a-9c0f-4ed6-a78d-e9fc2ed96bab'
    # })
    # txn.insert({
    #     'user_id': '145751385424004372',
    #     'nickname': '庄家庆',
    #     'code': 'c4ea-2da0f647-bac4-4d46-ac1a-0a8bf4b7142a'
    # })
    # txn.insert({
    #     'user_id': '1558093538679411',
    #     'nickname': '刘洋',
    #     'code': 'c4ea-f05ac56f-f11e-4a20-a07c-56a39116bf14'
    # })
    # txn.insert({
    #     'user_id': 'manager6971',
    #     'nickname': 'Ryan',
    #     'code': 'c4ea-2e490c94-6bb0-4f83-b126-46eef986957d'
    # })

# 关闭数据库连接
db.close()