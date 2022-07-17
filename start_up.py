import time
from pprint import pprint

from record.adb import AdbUtils
from record.licence import Licence


class SmartPerfSdk(AdbUtils, Licence):
    """
    平台上需要获取 ak
    """

    def initialize_check(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.get_user_privilege()
        self.oss = self.get_oss_licence()
        self.vip = self.get_user_privilege()

    def start_app_record_video(self, app_text: str, mp4_name: str):
        """
        启动并且启动录屏
        这里需要调用权限接口
        :param mp4_name:
        :param app_text:
        :return:
        """
        self.start_app(app_text, mp4_name)

    def stop_upload_oss(self):
        """
        第三个步骤停止录屏和上传OSS
        upload_oss里面包含了 获取用户的Vip等级得到的信息
        需要许总那边传输给我
        :return:
        """
        self.stop_record()
        # 获取mp4长度和vip获取下来的比较 python使用moviepy
        video_duration = self.vip["videoDuration"]
        # if self.get_record_duration() >= video_duration:
        #     return "视频过长"
        ok = self.temp_auth_upload_file(self.oss, self.video_path)
        print(ok)

    def create_task_callback_result(self, project_id, algorithm_id):
        """
        创建任务和回调结果
        1.创建任务
        2.获取任务id，轮询等待。
        3.查询任务 标记跳出循环，结束。
        """
        # vip等级获取的拆帧间隔
        frame_interval = self.vip["frameInterval"]
        task_id = self.create_sdk(project_id, frame_interval, algorithm_id, self.video_path)
        if task_id:
            data = self.query_report_detail(task_id)
            pprint(data)


if __name__ == '__main__':
    sdk = SmartPerfSdk()
    sdk.initialize_check("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    sdk.start_app_record_video("飞书", "feishu.mp4")
    time.sleep(20)
    sdk.stop_upload_oss()
    sdk.create_task_callback_result(27, 38)
