
from pymongo import MongoClient

# 加载数据库文件，创建数据库实例
client = MongoClient('mongodb://localhost:27017/')
db = client.chatgpt_db
users = db.Users
codes = db.Codes

# 移除用户
def remove_user(user_id):
    users.delete_many({'user_id': user_id})

# 添加 code 额度
def add_code_amount(code, add_amount):
    code_info = codes.find_one({'code': code})
    amount = code_info['amount'] + add_amount
    codes.update_many({'code': code_info['code']}, {'$set': {'amount': amount}})

# 添加用户
def insert_user(user_id, nickname, code):
    users.insert_one({
    'user_id': user_id,
    'nickname': nickname,
    'code': code
})


# remove_user('manager6971')
# insert_user('080567406620809', '光', 'c4ea-be286dc1-1ce0-4f52-b4de-5e66da1e5a4d')
# insert_user('145751385424004372', '庄家庆', 'c4ea-2da0f647-bac4-4d46-ac1a-0a8bf4b7142a')
# insert_user('1558093538679411', '刘洋', 'c4ea-f05ac56f-f11e-4a20-a07c-56a39116bf14')
# insert_user('manager6971', 'Ryan', 'c4ea-2e490c94-6bb0-4f83-b126-46eef986957d')
# add_code_amount('c4ea-be286dc1-1ce0-4f52-b4de-5e66da1e5a4d', 50)
# add_code_amount('c4ea-2da0f647-bac4-4d46-ac1a-0a8bf4b7142a', 50)
# add_code_amount('c4ea-f05ac56f-f11e-4a20-a07c-56a39116bf14', 50)
# add_code_amount('c4ea-2e490c94-6bb0-4f83-b126-46eef986957d', 50)

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
