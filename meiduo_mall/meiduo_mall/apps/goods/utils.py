def get_breadcrumb(category):
    """传入指定三级类返回 一二三级"""
    breadcrumbs = {}
    # 包装三级数据
    breadcrumbs['cat3'] = category
    # 包装二级数据
    breadcrumbs['cat2'] = category.parent
    # 获取一级类别模型
    cat1 = category.parent.parent
    # 给一级属性添加一个url属性
    cat1.url = cat1.goodschannel_set.all()[0].url
    # 包装一级数据
    breadcrumbs['cat1'] = cat1
    # 响应面包屑导航大字典数据
    return breadcrumbs