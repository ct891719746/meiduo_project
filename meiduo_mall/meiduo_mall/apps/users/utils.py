from django.contrib.auth.backends import ModelBackend
import re
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