
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

# 关闭数据库连接
db.close()