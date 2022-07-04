import time

from record.adb import AdbUtils
from record.licence import Licence


class SmartPerfSdk(AdbUtils, Licence):
    """
    平台上需要获取 ak
    """

    def __init__(self, app_key, app_secret):
        super().__init__(app_key, app_secret)

    def initialize_check(self):
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

    def stop_upload_oss(self, bucket: str):
        """
        第三个步骤停止录屏和上传OSS
        upload_oss里面包含了 获取用户的Vip等级得到的信息
        需要许总那边传输给我
        :return:
        """
        self.stop_record()
        ok = self.temp_auth_upload_file(self.oss, bucket, self.video_path)
        print(ok)

    def return_test_result(self):
        ...


if __name__ == '__main__':
    sdk = SmartPerfSdk("zTOPdfzM", "317696f41febc60ac51fb553301a2508")
    sdk.start_app_record_video("飞书", "feishu.mp4")
    time.sleep(20)
    sdk.stop_upload_oss("exampleobject")
