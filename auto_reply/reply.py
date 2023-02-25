
from config import dynamic_conf
from payment.payment import Payment

_config = dynamic_conf()['auto_reply']
_cmds = [
    '/info',
    '/help',
    #'/clear'
]

class Reply(object):

    def is_auto_reply(self, content):
        return content in _cmds

    def reply_newbie(self):
        return _config['newbie'].replace('\\n', '\n') + self.reply_help()

    def reply_help(self):
        return _config['help'].replace('\\n', '\n')

    def reply_runout(self):
        return _config['runout'].replace('\\n', '\n')
    
    def reply_bound_code(self, user_id, nickname):
        payment = Payment()
        amount = payment.get_amount(user_id, nickname)
        bound_text = _config['bound']
        return f'{bound_text} 剩余额度: {amount}次'
    def reply_bound_invalid(self, user_id, nickname):
        return _config['bound_invalid'].replace('\\n', '\n')

    def reply_with(self, user_id, nickname, content):
        if self.is_auto_reply(content):
            payment = Payment()
            if content == '/info':
                amount = payment.get_amount(user_id, nickname)
                user = payment.search_user(user_id, nickname)
                code = user['code']
                return f'ID: {user_id}\n用户名: {nickname}\n剩余额度: {amount}次\n卡号: {code}'
            elif content == '/help':
                return self.reply_help()
                

