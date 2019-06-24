import base64
import json
import pickle
from django_redis import get_redis_connection
from django import http
from django.shortcuts import render
from django.views import View
from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE


class CartsView(View):
    """购物车"""

    def post(self,request):
        """购物车添加"""

        # 接收请求体数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected',True)

        # 校验
        if all([sku_id,count]) is False:
            return http.HttpResponseForbidden("缺少必传参数")

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("商品不存在")


        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数错误')

        if isinstance(selected,bool) is False:
            return http.HttpResponseForbidden('参数有误')









        # 判断用户是否登录
        # 登录用户存储购物车数据到redis
        """
        set集合: {sku_id}  存储被勾选商品的id
        hash字典: {sku_id_1: 2, 'sku_id_2: 1}
        """
        # 未登录用户存储购物车数据到cookie
        """
        {
            sku_id_1: {'count': 1, 'selected': True}
        }
        """
        user = request.user
        if user.is_authenticated:
            # 登录用户存储购物车数据到redis
            # 创建redis连接
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipline()

            # 调用hincrby()  添加和增量
            pl.hincrby('cart_%s' % user.id,sku_id,count)

            # 如果当前商品是勾选把当前sku_id添加到set集合  sadd
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
                pl.execute()
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '商品添加至购物车成功'})
        else:
            # 未登录用户存储购物车数据到cookie
            # 获取cookie中redis购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断cookie中是否有购物车数据
            if cart_str:

                # 如果取到了cookie购物车数据,将字符串转回字典
                cart_str_bytes = cart_str.encode()
                cart_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_bytes)

                # 判断当前要添加到商品是否已经添加过,如果添加过,对count做增量
                if sku_id in cart_dict:
                    origin_count = cart_dict[sku_id]['count']
                    count += origin_count
                    # 如果本次添加的是一个新商品,就增加到大字典
                    cart_dict[sku_id] = {
                        'count': count,
                        'selected': selected
                    }

            # 如果没有cookie购物车数据, 准备一个大字典
            else:
                cart_dict = {}

            # 如果本次添加的是一个新商品,就增加到大字典
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 将购物车大字典,再转回到字符串
            cart_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_bytes)
            cart_dict = cart_str_bytes.encode()
            response = http.JsonResponse({'code': RETCODE.OK,'errmsg': '添加商品到购物车成功'})

            # 设置cookie
            response.set_cookie('carts',cart_str)

            return response

