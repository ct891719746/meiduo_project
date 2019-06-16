from django import http
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.shortcuts import render,redirect
from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins

import re

from .models import User
from meiduo_mall.utils.response_code import RETCODE



class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request:
        :return:
        """
        return render(request, 'register.html')

    def post(self,request):
        """注册业务逻辑"""

        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code = query_dict.get('sms_code')
        allow = query_dict.get('allow')  # 在表单中如果没有给单选框指定value值默认勾选就是“on" 否则就算None

        # 校验数据
        if all([username, password, password2, mobile,sms_code, allow]) is False:
            return http.HttpResponseForbidden('缺少必传参数')


        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9a-zA-Z]{8,20}$',password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('俩次输入的密码不一致')
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')

        # 获取redis中的短信验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断验证码师傅过期
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码过期')

        # 删除redis中已经被使用过的短信验证码L
        redis_conn.delete('sms_%s' %mobile)

        # 由bytes 类型转换为str类型
        sms_code_server = sms_code_server.decode()

        # 判断用户输入的验证码是否正确
        if sms_code != sms_code_server:
            return http.HttpResponseForbidden("请输入正确的验证码")







        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        login(request, user) # 把当前用户id存到session

        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        return response



class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        count = User.objects.filter(username=username).count()

        # 响应
        content = {'count':count, 'code': RETCODE.OK, 'errrmsg': 'OK'}
        return http.JsonResponse(content)


class MobileCountView(View):
    """判断手机号是否重复"""
    def get(self, request,mobile):
        count = User.objects.filter(mobile=mobile).count()

        content = {'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'}

        return http.JsonResponse(content)


class LoginView(View):
    """用户 登陆"""

    def get(self,request):
        """展示登陆页面"""

        return render(request, 'login.html')


    def post(self,request):
        """实现用户登陆"""


        # 接收请求体中表单数据
        query_dict  = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # # 先判断用户是否用的是手机号登陆，是的话就用mobile去查询user
        # if re.match(r'^1[3-9]\d{9}$',username):
        #     User.USERNAME_FIELD = 'mobile'

        # 认证
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # User.USERNAME_FIELD = 'username'

        # 状态保持
        login(request, user)

        # 判断用户是否勾选了记住登陆
        if remembered is None:
            request.session.set_expiry(0)
            # session过期时间指定为None默认是两周,指定为0是关闭浏览器删除
            # cookie如果指定过期时间为None 关闭浏览器删除, 如果指定0,它还没出生就没了



        # 若登陆成功重定向到首页
        # response = redirect('/')
        response = redirect(request.GET.get('next', '/'))

        response.set_cookie('username',user.username, max_age=(settings.SESSION_COOKIE_AGE if remembered else None))
        return response


class LogoutView(View):
    """退出登陆"""

    def get(self, request):

        # 清除状态保持数据
        logout(request)

        # 重定向到登陆页login
        response = redirect('/login/')

        # 清除cookie中的username
        response.delete_cookie('username')


        return response

# 方法1
# class InfoView(View):
#     """展示用户中心"""
#
#     def get(self,request):
#         user = request.user
#         # 判断用户是否登陆，如果登陆就现实个人中心界面
#         if user.is_authenticated:
#             return render(request, 'user_center_info.html')
#         else:
#             # 没有登陆则到登陆界面
#             return redirect('/login/?next=/info/')

# 方法2
# class InfoView(View):
#     """展示用户中心"""
#     @method_decorator(login_required)
#     def get(self,request):
#         # 判断用户是否登陆，如果登陆显示个人中心界面
#         return render(request, 'user_center_info.html')

# 方法3
class InfoView(mixins.LoginRequiredMixin,View):
    """展示用户中心"""
    # 判断用户是否登陆，如果登陆线索个人中心页面
    def get(self,request):
        return render(request, 'user_center_info.html')
