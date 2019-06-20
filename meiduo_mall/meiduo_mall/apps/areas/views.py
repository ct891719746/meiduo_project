from django import http
from django.core.cache import cache
from django.shortcuts import render

from django.views import View

from meiduo_mall.utils.response_code import RETCODE
from .models import Area


class AreasView(View):
    """省市区数据查询"""

    def get(self, request):

        # 获取查询参数area_id
        area_id = request.GET.get('area_id')


        # 如果前端没有传area_id代表要查询所有的省

        if area_id is None:

            province_list = cache.get('province_list')
            if province_list is None:


                province_qs = Area.objects.filter(parent=None)

                # 遍历查询集，将里面的每一个模型对象转换成字典对象，再包装到列表中
                province_list = []
                for province_model in province_qs:
                    province_list.append(
                        {
                            'id': province_model.id,
                            'name': province_model.name
                        }
                    )
                    # 从mysql查询出来之后立即设置缓存 缓存一个小时
                    cache.set('peovince_list', province_list, 3600)


                return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:

            sub_data = cache.get('sub_areas_%s' % area_id)
            if sub_data is None:
                subs_qs = Area.objects.filter(parent_id=area_id)

                try:
                    parent_model = Area.objects.get(id = area_id)

                except Area.DoesNotExist:
                    return http.HttpResponseForbidden('area_id不存在')


                sub_list = []
                for sub_model in subs_qs:
                    sub_list.append(
                        {
                            'id': sub_model.id,
                            'name': sub_model.name
                        }
                    )

                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': sub_list
                }
                cache.set('sub_area_%s' % area_id, sub_data, 3600)


            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data':sub_data})
