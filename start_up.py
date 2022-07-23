import time
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

    def start_record_and_upload_oss(self, app_text: str, mp4_name: str, project_id: int, algorithm_id: int):
        """
        屏幕划动到app的手机界面-->启动app-->启动录屏-->保存-->上传oss-->创建任务-->查询任务状态-->判断任务状态-->完成任务
        :param app_text:app的文本name
        :param mp4_name:存储mp4的名称，用于上传
        :param project_id: 从平台上面查询自己项目id
        :param algorithm_id: 从平台上面查询支持算法id
        :return:
        """
        self.start_app(app_text, mp4_name)
        video_duration = self.vip["videoDuration"]
        time.sleep(video_duration)
        self.stop_record()
        ok = self.temp_auth_upload_file(self.oss, self.video_path)
        print(ok)
        self.create_task_callback_result(self.video_path, project_id, algorithm_id)


if __name__ == '__main__':
    sdk = SmartPerfSdk()
    sdk.initialize_check("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    sdk.start_record_and_upload_oss("飞书", "feishu.mp4", project_id=27, algorithm_id=38)
