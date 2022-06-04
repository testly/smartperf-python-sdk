from record.start_app import StartApp
from record.record import AdbRecord


class SmartPerfSdk(StartApp, AdbRecord):

    def step1_start_app(self, package_name: str, activity_name: str):
        """
        第一个步骤启动app
        :param package_name:
        :param activity_name:
        :return:
        """
        self.start_app(package_name, activity_name)

    def step2_record_vedio(self, vedio_file: str, out_path: str, size: str = "1200x540", rate: str = "2000000"):
        """
        第二个步骤启动录屏
        :param vedio_file:
        :param out_path:
        :param size:
        :param rate:
        :return:
        """
        self.start_record(vedio_file, out_path, size, rate)

    def step3_upload_oss(self, max_size: float or int, out_path: str):
        """
        第三个步骤停止录屏和上传OSS
        upload_oss里面包含了 获取用户的Vip等级得到的信息
        需要许总那边传输给我
        :return:
        """
        self.stop_record()
        self.save_video(max_size, out_path)
        self.upload_oss()
