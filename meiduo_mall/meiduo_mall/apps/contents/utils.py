from goods.models import GoodsChannel


def get_categories():
    """返回i商品类别数据"""
    categories = {}
    goods_channels_qs = GoodsChannel.objects.order_by('group_id','sequence')

    # 遍历商品频道查询集
    for channels_model in goods_channels_qs:


        # 获取当前组号
        group_id = channels_model.group_id


        # 判断组号在字典的key中是否存在,不存在,再去准备新字典
        if group_id not in categories:
            categories[group_id] = {
                'channels':[],
                'sub_cats':[]

            }

        # 通过商品频道获取到一一对应的一级类别模型
        cat1 = channels_model.category

        # 为一级类别多定义一个url属性
        cat1.url = channels_model.url

        # 把一级类别添加到当前组中
        categories[group_id]['channels'].append(cat1)


        # 获取指定一级下面的所有二级
        cat2_qs = cat1.subs.all()
        for cat2 in cat2_qs:
            cat3_qs = cat2.subs.all()
            cat2.sub_cats = cat3_qs
            categories[group_id]['sub_cats'].append(cat2)


    return categories