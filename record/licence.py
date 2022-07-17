import os
import time
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

    def create_sdk(self, project_id: int, frame_interval: int, algorithm_id: int, dst_file: str):
        """
        新增任务 project_id
        TODO 算法ID需要一个映射表
        """
        file_name = os.path.basename(dst_file)
        ftime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        body = {
            "taskName": f"task_{ftime}_{file_name.replace('.mp4', '')}",  # 产品名称+时间格式s
            "frameInterval": frame_interval,
            "algorithmId": algorithm_id,
            "resourceUrl": f"http://smart-perf.oss-cn-shanghai.aliyuncs.com/long-temp/web/{file_name}",
            "projectId": project_id,
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(f"{self.url}/addTask", json=body)
        if res.status_code == 200:
            result = res.json()
            if result["success"]:
                data = result["data"]
                if data:return data

    def query_task_id(self, task_id):
        """
        查询任务
        """
        body = {
            "taskId": task_id,
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(f"{self.url}/getTask", json=body)
        if res.status_code == 200:
            result = res.json()
            if result["success"]:
                data = result["data"]
                if data: return data

    def query_report_detail(self, task_id):
        """
        报告详情基本信息接口
        """
        body = {
            "taskId": task_id,
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(f"{self.url}/getTaskReport", json=body)
        if res.status_code == 200:
            result = res.json()
            if result["success"]:
                data = result["data"]
                if data: return data

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

    def temp_auth_upload_file(self, oss_info: dict, dst_file: str):
        """
        临时授权上传文件
        :return:
        """
        auth = oss2.Auth(oss_info.get("accessKeyId"), oss_info.get("securityToken"))
        bucket = oss2.Bucket(auth, oss_info.get("endpoint"), 'smart-perf')
        # 填写Object完整路径
        file_name = os.path.basename(dst_file)
        object_name = f'long-temp/web/{file_name}'
        # 生成上传文件的签名URL，有效时间为60秒。
        # 生成签名URL时，OSS默认会对Object完整路径中的正斜线（/）进行转义，从而导致生成的签名URL无法直接使用。
        url = bucket.sign_url('PUT', object_name, 60, slash_safe=True)
        print('签名url的地址为：', url)
        # 使用签名URL上传本地文件。
        result = bucket.put_object_with_url_from_file(url, dst_file)
        if result:
            return result.status


if __name__ == '__main__':
    licence = Licence("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    pprint(licence.get_oss_licence())
    pprint(licence.get_user_privilege())
