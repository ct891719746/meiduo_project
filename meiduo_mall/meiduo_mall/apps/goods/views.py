from django.shortcuts import render
from django.views import View
from django import http
from django.core.paginator import Paginator,EmptyPage

from contents.utils import get_categories
from meiduo_mall.utils.response_code import RETCODE
from .utils import get_breadcrumb
from .models import GoodsCategory,SKU


class ListView(View):
    """商品列表界面"""

    def get(self,request, category_id, page_num):
        """

        :param request:
        :param category_id:
        :param page_num:
        :return:
        """
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden("category_id不存在")
        # 获取前端传入的排序规则
        sort = request.GET.get('sort','default')

        sort_field = '-create_time'     # 默认的排序规则
        if sort == 'price':
            sort_field = '-price'
        elif sort == 'hot':
            sort_field = '-sales'

        sku_qs = category.sku_set.filter(is_launched=True).order_by(sort_field)

        # 创建分页器对象
        paginator = Paginator(sku_qs, 5)

        try:
            page_skus = paginator.page(page_num)

        except EmptyPage:
            return http.HttpResponseForbidden('超出指定页')

        # 获取他的总页数
        total_page = paginator.num_pages

        context = {
            'categories': get_categories(),               # 商品类别数据
            'breadcrumb':get_breadcrumb(category),        # 面包屑导航数据
            'sort': sort,                               # 排序字段
            'category':category,                     # 第三级分类
            'page_skus':page_skus,                   # 分页后数据
            'total_page':total_page,                # 总页数
            'page_num':page_num,                     # 当前页码
        }

        return render(request,'list.html',context)

class HotGoodsView(View):
    """商品热销排序"""

    def get(self,request, category_id):

        try:
            cat3 = GoodsCategory.objects.get(id=category_id)

        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # 查询指定三级类型下的销售最高的前两个sku
        sku_qs = cat3.sku_set.filter(is_launched=True).order_by('-sales')[:2]
        sku_list = []

        for sku_model in sku_qs:
            sku_list.append(
                {
                    'id':sku_model.id,
                    'price':sku_model.price,
                    'name':sku_model.name,
                    'default_image_url': sku_model.default_image.url
                }
            )

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','hot_skus':sku_list})



class DetailView(View):
    """商品详细界面"""
    def get(self,request,sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request,'404.html')

        # 获取当前sku对应的三级分类

        category = sku.category
        # 获取当前对象的SPU
        spu = sku.spu
          # 当前商品的规格选项列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)
            

        temp_sku_qs = spu.sku_set.all()
        # 选项仓库大字典
        spec_sku_map = {}

        for temp_sku in temp_sku_qs:
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id



        spu_spec_qs = spu.specs.order_by('id')

        for index, spec in enumerate(spu_spec_qs):
            pass






