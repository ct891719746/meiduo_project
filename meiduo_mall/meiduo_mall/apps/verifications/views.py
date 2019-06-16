from django.views import View

from django_redis import get_redis_connection
from django import http
import logging
from . import constants
from random import randint

from meiduo_mall.libs.captcha.captcha import captcha
# from celery_tasks.sms.yuntongxun import CCP
from meiduo_mall.utils.response_code import RETCODE

from celery_tasks.sms.tasks import send_sms_code
logger = logging.getLogger('django')

class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):

        # 生成图形验证码
        name, image_code_text, image_bytes = captcha.generate_captcha()

        # 创建redis连接对象
        redis_conn = get_redis_connection(alias='verify_code')

        # 将图形验证码的字符 存储到redis中 用uuid作为key
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, image_code_text)

        # 响应 把生成好的图片验证码bytes数据作为响应体响应给前端
        return http.HttpResponse(image_bytes, content_type='image/jpg')


class SMSCodeView(View):
    """发送短信验证码"""
    def get(self, request, mobile):

        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')

        # 尝试性去获取此手机是否有发过短信的标记
        send_flag = redis_conn.get('send_flag_%s' % mobile)

        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': "频繁发送短信"})



        # 接收前端传入的数据
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        # 校验数据
        if all([image_code_client,uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')


        # 把redis中的图形验证码删除，让验证码之使用一次
        image_code_server = redis_conn.get('img_%s' % uuid)

        # 判断短信是否过期
        if image_code_server is None:
            return http.HttpResponseForbidden("图形验证码过期")

        # 注册时保证image_code_server 不会None然后再去调用decode
        image_code_server = image_code_server.decode()

        # 判断用户输入验证码是否正确，注意大小写转换
        if image_code_client.lower() != image_code_server.lower():
            return http.HttpResponseForbidden('验证码输入有误')

        # 随机生成一个6位数作验证码
        sms_code = '%06d' % randint(0,999999)
        logger.info(sms_code)
        # redis 管道技术
        pl = redis_conn.pipeline()
        # 将短信验证码存到redis，以备后期注册时校验
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 向redis 多存储一个此手机号已发送短信的标记，有效期为60秒
        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        pl.execute()


        # 给当前手机号发短信
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 生产任务
        send_sms_code.delay(mobile, sms_code)
        #响应
        return http.JsonResponse({'code':RETCODE.OK, 'errmsg': '发送短信验证码成功'})


        pass

