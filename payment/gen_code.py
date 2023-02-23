import uuid

code_prefix = 'c4ea-'

# 生成 uuid 字符串的数量
num_uuids = 100

# 生成 uuid 字符串数组
uuids = [code_prefix+str(uuid.uuid4()) for _ in range(num_uuids)]

# 将 uuid 字符串数组写入文件
with open('payment_codes', 'w') as f:
    for uuid_str in uuids:
        f.write(uuid_str + '\n')