from django.contrib.auth.backends import ModelBackend
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


from .models import User


def get_user_account(account):
    """
    通过传入账户查询user
    :param account:
    :return:
    """
    try:
        if re.match(r'^1[3-9]\d{9}$',account):
            user_model = User.objects.get(mobile=account)

        else:
            user_model = User.objects.get(username=account)

    except User.DoesNotExist:
        return None


    return user_model


class UsernameMobileBackend(ModelBackend):
    """自定义认证后端类"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1.查询到user ,可以通过手机号或用户名
        user = get_user_account(username)
        # 2.校验user的密码是否正确
        if user and user.check_password(password):
            return user



def generate_verify_email_url(user):
    """拼接用户邮箱激活url"""
    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60*60*24)
    # 包装要加密的字典数据
    data = {'user_id': user.id, 'email':user.email}

    # 对字典加密
    token = serializer.dumps(data).decode()

    # 拼接用户激活邮箱url
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token

    return verify_url


def check_verify_email_token(token):

    """对token进行解密并返回user或None"""

    # 创建加密对象
    serializer = Serializer(settings.SECRET_KEY, 60 * 60 * 24)

    try:
        data = serializer.loads(token)
        user_id = data.get('user_id')
        email = data.get('email')

        try:
            user = User.objects.get(id=user_id, email=email)
            return user
        except User.DoesNotExist:
            return None


    except BadData:
        return None