from django.core.files.storage import Storage


class FastDFSStorage(Storage):
    """自定义文件存储类"""

    def _open(self,name, mode= 'rb'):
        """
        当要dakai文件时会调用此方法
        :param name:
        :param mode:
        :return:
        """
        pass

    def _save(self,name,content):
        """
        当要上传文件时就会调用此方法

        :param name:
        :param content:
        :return:

        """
        pass

    def url(self,name):
        """

        当对突破字段调用url属性时就会自动调用此方法，获取文件和图片的绝对路径
        :param name:
        :return:
        """

        return 'http://192.168.48.128:8888/' + name
