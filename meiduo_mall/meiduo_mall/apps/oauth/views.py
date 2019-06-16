from django import http
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views import View
from django_redis import get_redis_connection

from QQLoginTool.QQtool import OAuthQQ

from meiduo_mall.utils.response_code import RETCODE
from users.models import User

from .models import OAuthQQUser
from .utils import generate_openid_signature,check_openid_signature


import logging
import re


logger = logging.getLogger('django')


class QQAuthURLView(View):
    """提供QQ登陆的URL"""

    def get(self,request):
        # 获取查询参数 next
        next = request.GET.get('next','/')

        # QQ_CLIENT_ID = '101518219'
        # QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
        # QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'

        # 创建OAuthQQ 实例对象 并给实例属性赋值
        # auth_qq = OAuthQQ(client_id='app_id', client_secret='app_key',
        # redirect_uri='QQ登录成功后的回调url', state='标识')

        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI,
                          state=next)


        # 调用他里面的get_qq_url方法得到拼接好的QQ登陆URL
        login_url = auth_qq.get_qq_url()



        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

class QQAuthView(View):
    """QQ登陆成功后的回调处理"""
    def get(self,request):

        # 获取查询参数的code
        code = request.GET.get('code')

        if code is None:
            return http.HttpResponseForbidden("缺少code")


        auth_qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 调用SKD中的get_access_token方法传入code获取access_token
            access_token = auth_qq.get_access_token(code)

            # 调用SKD中get_open_id方法传入access_token获取openid
            openid = auth_qq.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('OAuth2.0认证失败')


        try:
            # 使用openid查询tb_oauth_qq表
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果查询不到openid，说明QQ是第一次登陆，应该要让他绑定
            openid = generate_openid_signature(openid)

            return render(request, 'oauth_callback.html', {'openid':openid})

        else:
            # 如果查询到openid,说明此QQ已经绑定过梅多用户，那么就直接显示登陆成功
            user = oauth_model.user
            # 状态保持
            login(request,user)
            # 重定向到来源页面
            response = redirect(request.GET.get('state','/'))

            # 在cookie中存储username
            response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

            return response

    def post(self,request):
        """绑定用户处理"""

        # 接收表单数据，mobile，pwd,sms_code,openid
        query_dict  = request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        openid_sign = query_dict.get('openid')

        if all([mobile, password, sms_code, openid_sign]) is False:
            return http.HttpResponseForbidden('缺少必传的参数')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$',password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')


        # 创建连接对象
        redis_conn = get_redis_connection('verify_code')

        # 获取redis中的短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断验证码是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden("短信验证码已过期")

        # 删除redis中已经用过的短信验证码

        redis_conn.delete('sms_%s' % mobile)

        # 由bytes 类型转换为str
        sms_code_server = sms_code_server.decode()


        if sms_code != sms_code_server:
            return http.HttpResponseForbidden('验证码输入有误')

        # 对openid进行解密

        openid = check_openid_signature(openid_sign)
        if openid is None:
            return http.HttpResponseForbidden("openid无效")


        try:

            user = User.objects.get(mobile=mobile)

        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
            pass

        else:

            if user.check_password(password) is False:
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})



        # 无论新老用户都放心大胆和openid绑定
        OAuthQQUser.objects.create(openid=openid, user=user)


        login(request, user)

        response = redirect(request.GET.get('state', '/'))

        response.set_cookie('username',user.username, max_age=settings.SESSION_COOKIE_AGE)

        return response





























