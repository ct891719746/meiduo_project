"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    # 用户注册
    url(r'^register/$',views.RegisterView.as_view()),
    #    判断用户名是否重复
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否重复
    url(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.MobileCountView.as_view()),
    # 用户登录
    url(r'^login/$', views.LoginView.as_view()),
    # 用户退出登陆
    url(r'logout/$', views.LoginView.as_view()),
    # 用户中心
    url(r'info/$', views.InfoView.as_view()),
    # 设置邮箱
    url(r'^emails/$', views.EmailView.as_view()),

    # 激活邮箱
    url(r'^emails/verification/$', views.EmailVerificationView.as_view()),

    # 收货地址
    url(r'^addresses/$', views.AddressView.as_view()),

    # 新增收获地址
    url(r'^addresses/create/$', views.CreateAddressView.as_view()),

    # 修改和删除收货地址

    url(r'addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 修改收货地址标题
    url(r'^addresses/(?P<address_id>\d+)/title/$',views.UpdateDestroyAddressView.as_view()),
    # 设置默认收货地址
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),

    # 修改用户密码

    url(r'password/$', views.ChangePasswordView.as_view()),
    # 商品历史浏览记录
    url(r'^browse_historise/$', views.UserBrowseHistory.as_view()),


]
