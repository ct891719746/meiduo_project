from celery import Celery

# 1.创建celery客户端对象

celery_app = Celery('meiduo')


# 2. 加载celery的配置，让生产者自己知道生产的人物存在什么位置

celery_app.config_from_object('celery_tasks.config')


# 3.自动注册人物（‘告诉生产者他能生产什么样的人物’）

celery_app.autodiscover_tasks(['celery_tasks.sms'])
