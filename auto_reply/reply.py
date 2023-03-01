
from config import dynamic_conf
from payment.payment import Payment
from common import const

_cmds = [
    '/info',
    '/help',
    #'/clear'
]

class Reply(object):

    def is_auto_reply(self, content):
        return content in _cmds

    def reply_newbie(self):
        return self._config()['newbie'].replace('\\n', '\n') + self.reply_help()

    def reply_sensitive(self):
        return self._config()['sensitive'].replace('\\n', '\n')

    def reply_help(self):
        return self._config()['help'].replace('\\n', '\n')

    def reply_runout(self):
        return self._config()['runout'].replace('\\n', '\n')
    
    def reply_bound_code(self, user_id, nickname):
        payment = Payment()
        amount = payment.get_amount(user_id, nickname)
        bound_text = self._config()['bound']
        return f'{bound_text} 剩余额度: {amount}次'

    def reply_bound_invalid(self, user_id, nickname):
        return self._config()['bound_invalid'].replace('\\n', '\n')

    def reply_bound_referral(self):
        return self._config()['bound']

    def reply_bound_referral_invalid(self):
        return self._config()['bound_referral_invalid']

    def reply_with(self, user_id, nickname, content):
        if self.is_auto_reply(content):
            payment = Payment()
            if content == '/info':
                amount = payment.get_amount(user_id, nickname)
                user = payment.search_user(user_id, nickname)
                code = user['code']
                referral = const.PREFIX_REF + user_id
                return f'ID: {user_id}\n用户名: {nickname}\n推荐码: {referral}\n\n:剩余额度: {amount}次\n卡号: {code}'
            elif content == '/help':
                return self.reply_help()

    def _config(self):
        return dynamic_conf()['auto_reply']
                

