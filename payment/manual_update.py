
import shutil
from tinydb import TinyDB, where
from tinyrecord import transaction

# 备份数据库文件
shutil.copy2('payment/db.json', 'payment/db_backup.json')

# 加载数据库文件，创建数据库实例
db = TinyDB('payment/db.json')
users = db.table('Users')
codes = db.table('Codes')

# 创建事务
with transaction(users) as txn:
    txn.remove(where('user_id') == 'manager6971')
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