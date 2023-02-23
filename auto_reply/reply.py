
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
        return _config['newbie'].replace('\n', '\n')

    def reply_help(self):
        return _config['help'].replace('\n', '\n')
    
    def reply_bound_code(self, user_id, nickname):
        payment = Payment()
        amount = payment.get_amount(user_id, nickname)
        bound_text = _config['bound']
        return f'{bound_text} 剩余额度: {amount}次'

    def reply_with(self, user_id, nickname, content):
        if self.is_auto_reply(content):
            payment = Payment()
            if content == '/info':
                amount = payment.get_amount(user_id, nickname)
                return f'剩余额度: {amount}次'
            elif content == '/help':
                return self.reply_help()
                

