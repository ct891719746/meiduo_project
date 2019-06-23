from django import http
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.shortcuts import render,redirect
from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import mixins
from django.core.mail import send_mail

import re,json
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU

from .models import User,Address
from .utils import generate_verify_email_url, check_verify_email_token



from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView



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



class EmailView(LoginRequiredView):
    """设置用户邮箱"""

    def put(self, request):

        # 接收请求体中的email，body{'email':'zzxx',}
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        email = json_dict.get('email')


        # 校验邮箱

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden("邮箱格式有误")


        # 获取当前用户的user模型对象
        user = request.user

        user.email = email
        user.save()

        # 生成邮箱激活url
        verify_url = generate_verify_email_url(user)
        # celery进行异步发送邮件
        send_verify_email.delay(email, verify_url)


        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': '添加邮箱成功'})



class EmailVerificationView(View):
    """激活邮箱"""

    def get(self,request):
        # 获取url查询参数
        token = request.GET.get('token')

        if token is None:
            return http.HttpResponseForbidden('缺少token参数')


        # 对token进行解密并查询到要激活邮箱的那个用户
        user = check_verify_email_token(token)

        # 如果没有查询到user，提前响应

        if user is None:
            return http.HttpResponseForbidden("token无效")

        user.email_active = True

        user.save()

        return redirect('/info/')


class AddressView(LoginRequiredView):
    """用户收货地址"""
    def get(self,request):
        user = request.user

        address_qs = Address.objects.filter(user=user,is_deleted=False)


        addresses_list = []
        for address_model in address_qs:
            addresses_list.append({
                'id': address_model.id,
                'title': address_model.title,
                'receiver': address_model.receiver,
                'province_id': address_model.province_id,
                'province': address_model.province.name,
                'city_id': address_model.city_id,
                'city': address_model.city.name,
                'district_id': address_model.district_id,
                'district': address_model.district.name,
                'place': address_model.place,
                'mobile': address_model.mobile,
                'tel': address_model.tel,
                'email': address_model.email
            })

        default_address_id = user.default_address_id

        context = {
            'addresses':addresses_list,
            'default_address_id': default_address_id
        }

        return render(request, 'user_center_site.html', context)



class CreateAddressView(LoginRequiredView):
    """新增收获地址"""

    def post(self,request):
        count = Address.objects.filter(user=request.user, is_deleted=False).count()

        if count >= 20:
            return http.JsonResponse({'code':RETCODE.THROTTLINGERR, 'errmsg':'收获地址数量超出限制'})



        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        # 新增收货地址
        address_model = Address.objects.create(
            user=request.user,
            title=title,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        # 如果当前用户还没有默认收货地址,就把当前新增的收货地址直接设置为它的默认地址
        if request.user.default_address is None:
            request.user.default_address = address_model
            request.user.save()

        # 把新增的收货地址再转换成字典响应回去
        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加收货地址成功', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """收货地址修改和删除"""

    def put(self, request, address_id):

        # 接收请求体 BOdy数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if all([title,receiver,province_id,city_id,district_id,place,mobile]) is False:
            return http.HttpResponseForbidden("缺少必传参数")

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden("mobile参数有误")

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('tel参数有误')

        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
                return http.HttpResponseForbidden('email参数有误')

        try:
            address_model = Address.objects.get(id=address_id, user=request.user, is_deleted=False)

        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        address_model.title = title
        address_model.receiver = receiver
        address_model.province_id = province_id
        address_model.city_id = city_id
        address_model.district_id = district_id
        address_model.place = place
        address_model.mobile = mobile
        address_model.tel = tel
        address_model.email = email
        address_model.save()

        address_dict = {
            'id': address_model.id,
            'title': address_model.title,
            'receiver': address_model.receiver,
            'province_id': address_model.province_id,
            'province': address_model.province.name,
            'city_id': address_model.city_id,
            'city': address_model.city.name,
            'district_id': address_model.district_id,
            'district': address_model.district.name,
            'place': address_model.place,
            'mobile': address_model.mobile,
            'tel': address_model.tel,
            'email': address_model.email
        }

        return http.JsonResponse({'code':RETCODE.OK, 'errmsg':'修改地址成功','address':address_dict})


    def delete(self,request,address_id):
        """删除收货地址"""
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden("address_id无效")

        address.is_deleted = True
        address.save()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'地址删除成功'})


class UpdateAddressTitleView(LoginRequiredView):
    """修改收货地址标题"""

    def put(self,request, address_id):
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')


        try:
            address = Address.objects.get(id=address_id)

        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')

        address.title = title
        address.save()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})


class DefaultAddressView(LoginRequiredView):
    """设置用户默认收货地址"""

    def put(self, request, address_id):
        try:
            address = Address.objects.get(id = address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id无效')


        user = request.user

        user.default_address = address
        user.save()

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})

class ChangePasswordView(LoginRequiredView):
    """修改用户密码"""

    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self,request):
        """修改密码逻辑"""

        query_dict = request.POST

        old_pwd = query_dict.get('old_pwd')
        new_pwd = query_dict.get('new_pwd')
        new_cpwd = query_dict.get('new_cpwd')


        if all([old_pwd,new_pwd,new_cpwd]) is False:

            return http.HttpResponseForbidden("缺少必传参数")

        user = request.user
        if user.check_password((old_pwd)) is False:
            return render(request, 'user_center_pass.html',{'origin_pwd_errmsg': '初始密码错误'})

        if not re.match(r'^[0-9a-zA-Z]{8,20}$',new_pwd):
            return http.HttpResponseForbidden("密码最少8位，最长20位")

        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('俩次输入的密码不一致')



        user.set_password(new_pwd)
        user.save()

        return redirect('/logout/')


class UserBrowseHistory(View):
    """用户浏览记录"""

    def post(self,request):
        """保存用户浏览记录"""
        # 接收参数
        if request.user.is_authenticated:
            json_dict = json.loads(request.body.decode())
            sku_id = json_dict.get('sku_id')


            try:
                sku = SKU.objects.get(id=sku_id)
            except SKU.DoesNotExist:
                return http.HttpResponseForbidden('sku_id不存在')



            # 创建redis　连接对象
            redis_conn = get_redis_connection('history')
            pl = redis_conn.pipeline()
            user = request.user
            key = 'history_%s' % user.id

            # 去重
            pl.lrem(key,0,sku_id)

            # 插开列表开头
            pl.lpush(key, sku_id)

            # 只保留前五个元素
            pl.lrem(key,0,4)
            pl.execute()


            # 响应
            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK'})


        else:
            return http.JsonResponse({'code':RETCODE.SESSIONERR,'errmsg':"用户未登录"})









