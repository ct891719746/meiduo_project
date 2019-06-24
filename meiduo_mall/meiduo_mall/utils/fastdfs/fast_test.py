from fdfs_client.client import Fdfs_client


# 创建fdfs客户端对象
client = Fdfs_client('./client.conf')

# 上传

ret = client.upload_appender_by_filename('/home/python/Desktop/02.jpg')

print(ret)
{
'Group name': 'group1',
 'Remote file_id': 'group1/M00/00/00/wKjPgF0MpAyEFSFCAAAAAPIeXSA010.jpg',
 'Status': 'Upload successed.',
 'Local file name': '/home/python/Desktop/02.jpg',
 'Uploaded size': '14.00KB',
 'Storage IP': '192.168.48.128'
}