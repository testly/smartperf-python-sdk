from pprint import pprint
from requests import post
import oss2


class Licence:
    # mp4文件符合准入
    mp4_admit = False
    # oss文件符合准入
    oss_admit = False
    url = "http://console.smart-perf.com:7001/api/sdk"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret

    def get_user_privilege(self):
        """
        获取使用权限
        :return:
        """
        path = "/getVipPrivilege"
        body = {
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(self.url + path, json=body)
        if res.status_code == 200:
            result = res.json()
            data = result["data"]
            if result['success'] and data:
                return data
            else:
                raise Exception(f"接口返回数据{data}不全，需要检查{self.url + path}接口")

    def check_dict_size(self, data: dict):
        """
        检查字典内容
        :param data:
        :return:
        """
        temp = {}
        for k, v in data.items():
            if v:
                temp[k] = v
        return len(temp) == len(data)

    def get_oss_licence(self):
        """
        获取oss许可(测试ok)
        :return:
        """
        path = "/getOssLicence"
        body = {
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(self.url + path, json=body)
        if res.status_code == 200:
            result = res.json()
            data = result["data"]
            if result['success'] and data and self.check_dict_size(data):
                return data
            else:
                raise Exception(f"接口返回数据{data}不全，需要检查{self.url + path}接口")

    def temp_auth_upload_file(self, oss_info: dict, bucket: str, dst_file: str):
        """
        临时授权上传文件
        :return:
        """
        # 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
        auth = oss2.Auth(oss_info.get("accessKeyId"), oss_info.get("accessKeySecret"))
        bucket = oss2.Bucket(auth, oss_info.get("endpoint"), bucket)
        # 填写Object完整路径，例如exampledir/exampleobject.txt。Object完整路径中不能包含Bucket名称。
        object_name = 'exampledir/exampleobject.txt'
        # 生成上传文件的签名URL，有效时间为60秒。
        # 生成签名URL时，OSS默认会对Object完整路径中的正斜线（/）进行转义，从而导致生成的签名URL无法直接使用。
        # 设置slash_safe为True，OSS不会对Object完整路径中的正斜线（/）进行转义，此时生成的签名URL可以直接使用。
        url = bucket.sign_url('PUT', object_name, 60, slash_safe=True)
        print('签名url的地址为：', url)
        # 使用签名URL上传本地文件。
        # 如果未指定本地路径只设置了本地文件名称（例如examplefile.txt），则默认从示例程序所属项目对应本地路径中上传文件。
        result = bucket.put_object_with_url_from_file(url, dst_file)
        return result.status


if __name__ == '__main__':
    licence = Licence("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    # pprint(licence.get_oss_licence())
    pprint(licence.get_user_privilege())
