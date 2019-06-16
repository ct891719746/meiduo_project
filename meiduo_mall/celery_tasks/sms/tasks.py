from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks.sms import constants
from celery_tasks.main import celery_app


# 只有 用此装饰前期装饰过的函数才能酸得上一个celery任务

@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):

    # 给手机发短信
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES //60], 1)

