
import shutil
from tinydb import TinyDB, where
from tinyrecord import transaction

# 备份数据库文件
shutil.copy2('db.json', 'db_backup.json')

# 加载数据库文件，创建数据库实例
db = TinyDB('db.json')
users = db.table('Users')
codes = db.table('Codes')

# 创建事务
with transaction(codes) as txn:
    txn.update({'user': '789'}, where('code') == '1')

# 关闭数据库连接
db.close()