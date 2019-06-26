import pickle, base64
from django_redis import get_redis_connection


"""
{
sku_id_1: {‘count’: 10, ‘selected’: False},
sku_id_12: {‘count’: 10, ‘selected’: False}

}
"""


def merge_cart_cookie_to_redis(request,response):
    """购物车合并"""
    cart_str = request.COOKIES.get('carts')
    # 先尝试获取cookie中购物车数据
    # 如果没有cookie购物车数据,后续代码都不用再执行
    if cart_str is None:
        return

    # 将cookie字符串转换成字典
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    # 创建redis连接对象
    redis_conn = get_redis_connection('carts')
    user = request.user  # 获取当前登录用户对象
    # 遍历cookie大字典
    for sku_id,sku_dict in cart_dict.items():
        # 将sku_id和count向redis的hash中添加,存在就覆盖,不存在就是新增
        redis_conn.hset('carts_%s' % user.id,sku_id,cart_dict['count'])
        # 判断selected 动态把sku_id添加或删除set
        if sku_dict['selected']:
            redis_conn.sadd('selected_%s' % user.id, sku_id)
        else:
            redis_conn.srem('selected_%s' % user.id, sku_id)

    # 将cookie购物车数据清除
    response.delete_cookie('carts')
