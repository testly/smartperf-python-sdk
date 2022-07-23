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
                task_id = result["data"]
                if task_id: return task_id

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
                pprint(result)
                task_status = result["data"]
                if task_status: return task_status

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

    def get_task_frame_list_report(self, task_id):
        """
        报告详情目标帧接口
        """
        body = {
            "taskId": task_id,
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }
        res = post(f"{self.url}/getTaskFrameListReport", json=body)
        if res.status_code == 200:
            result = res.json()
            if result["success"]:
                result_data = result["data"]
                print("get_task_frame_list_report:", result_data)
                if result_data:
                    data = []
                    for r in result_data:
                        data.append({r["frameName"]: r["frameIndex"]})
                    return data

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

    def create_task_callback_result(self, dst_file: str, project_id: int, algorithm_id: int):
        """
        创建任务和回调结果
        1.创建任务
        2.获取任务id，轮询等待。
        3.查询任务 标记跳出循环，结束。
        """
        result = self.get_user_privilege()
        if result:
            frame_interval = result["frameInterval"]
            file_name = os.path.basename(dst_file)
            task_id = self.create_sdk(project_id, frame_interval, algorithm_id, file_name)
            print(f"平台创建任务id成功{task_id}")
            if task_id:
                state = False
                while not state:
                    for status in self.query_task_id(task_id):
                        if status['taskState'] == 2:
                            state = True
                            print("报告状态完成")
                detail = self.query_report_detail(task_id)
                if detail["taskState"] == 2:
                    result = self.get_task_frame_list_report(task_id)
                    pprint(result)


if __name__ == '__main__':
    licence = Licence("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    debug = False
    if debug: pprint(licence.get_oss_licence())
    if debug: pprint(licence.get_user_privilege())
    licence.create_task_callback_result(r"D:\smartperf-python-sdk-main\res\feishu.mp4", 27, 38)
