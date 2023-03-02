
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

    def reply_newbie(self, user_id):
        return self._config()['newbie'].replace('\\n', '\n') + self.reply_help(user_id)

    def reply_sensitive(self):
        return self._config()['sensitive'].replace('\\n', '\n')

    def reply_help(self, user_id):
        return self._config()['help'].replace('\\n', '\n').format(const.PREFIX_REF + user_id)

    def reply_runout(self, user_id):
        return self._config()['runout'].replace('\\n', '\n').format(const.PREFIX_REF + user_id)
    
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

    def reply_bound_referral_rewards(self, user_id, nickname):
        payment = Payment()
        amount = payment.get_amount(user_id, nickname)
        return f'邀请成功！您获得10次额度。当前剩余额度: {amount}次'

    def reply_with(self, user_id, nickname, content):
        if self.is_auto_reply(content):
            payment = Payment()
            if content == '/info':
                amount = payment.get_amount(user_id, nickname)
                user = payment.search_user(user_id, nickname)
                code = user['code']
                referral = const.PREFIX_REF + user_id
                return f'【剩余额度】\n{amount}次\n\n【卡号】\n{code}\n\n【推荐码】\n{referral}'
            elif content == '/help':
                return self.reply_help(user_id)

    def _config(self):
        return dynamic_conf()['auto_reply']
                

