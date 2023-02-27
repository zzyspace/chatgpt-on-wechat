import uuid
import os
import shutil
import datetime
from common import const
from pymongo import MongoClient
from payment.payment import Payment


# 加载数据库文件，创建数据库实例
client = MongoClient('mongodb://localhost:27017/')
db = client.chatgpt_db
codes = db.Codes

# 配置
file_path = 'payment/payment_codes/codes'
num_uuids = 1
amount = 30

# 备份 payment_codes
current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
new_file_path = file_path + '_' + current_time
shutil.copyfile(file_path, new_file_path)

# 生成 uuid 字符串数组
uuids = [const.PREFIX_CODE+str(uuid.uuid4()) for _ in range(num_uuids)]

# 将 uuid 字符串数组写入文件
with open(file_path, 'w') as f:
    for uuid_str in uuids:
        f.write(uuid_str + '\n')

if not os.path.exists(file_path):
    print('兑换码文件不存在，请根据 codes_template 模板创建 codes 文件')
else:
    with open(file_path, 'r') as f:
        codes_arr = [line.strip() for line in f.readlines()]

    for code in codes_arr:
        result = codes.find_one({'code': code})
        if result is None:
            code_info = Payment.new_code_info(code, amount)
            codes.insert_one(code_info)
            print(code_info)

client.close()