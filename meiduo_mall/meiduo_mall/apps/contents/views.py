from django.shortcuts import render
from django.views import View

from .models import ContentCategory
from goods.models import GoodsCategory,GoodsChannel
from .utils import get_categories

class IndexView(View):
    """首页"""
    def get(self,request):


        contents = {}
        content_category_qs = ContentCategory.objects.all()
        for content_category in content_category_qs:

            contents[content_category.key] = content_category.content_set.filter(status=True).order_by('sequence')


        context = {
            'categories': get_categories(),
            'contents': contents


        }
        return render(request, 'index.html',context)


