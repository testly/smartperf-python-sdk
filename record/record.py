"""
adb 录制视频 所有安卓版本都适用 录制时长有限制 默认最长3分钟
控制码率  adb shell screenrecord --size 1280*720 --bit-rate 6000000 /sdcard/demo.mp4
-bit-rate 指定视频的比特率为6Mbps,如果不指定,默认为4Mbps  比特率越大，文件越大，画面越清晰

--size分辨率 前端推荐用默认的。不使用参数就是默认的。 注意1280*720 这个分辨率不是所有手机都适用 需要根据自己手机更改 目前使用默认分辨率即可
ps:adb录制视频 只支持mp4格式
"""
import os
import signal
from subprocess import Popen, PIPE
from multiprocessing import Process


def format_size_to_kb(data):
    """
    處理文件大小轉換 kb
    """
    res_bytes = float(data)  # 默认字节
    if res_bytes:
        return res_bytes / 1024  # Kb


def is_video(input_path: str) -> bool:
    """
    判断是视频
    :return:
    """
    suffix_set = {"WMV", "ASF", "ASX", "RM", "RMVB", "MP4", "3GP", "MOV", "M4V", "AVI", "DAT", "MKV", "FIV",
                  "VOB"}
    suffix = input_path.rsplit(".", 1)[-1].upper()
    return suffix in suffix_set


class AdbRecord:
    """adb 录屏"""

    process = None
    filename = ""

    def __init__(self, serial: str, video_path: str, lib_name: str = "libx264"):
        self.serial = serial
        if is_video(video_path):
            self.video_path = video_path
        else:
            raise Exception(f"{self.video_path}不存在")
        self.lib_name = lib_name

    def record(self, mp4_filename: str, phone_path: str, size: str, rate: str):
        """
        录屏
        @param mp4_filename: 文件名称 格式默认为mp4
        @param phone_path: 设备生成位置
        @param size: 分辨率
        @param rate: 比特率
        """
        try:
            if mp4_filename.endswith('.mp4'):
                print("开始录屏")
                Popen("adb -s " + self.serial + f" shell screenrecord --size {size} --bit-rate {rate} " + phone_path +
                      os.sep + mp4_filename)
        except KeyboardInterrupt:
            pass

    def get_record_duration(self):
        """
        獲取錄屏長度
        """
        suffix = os.path.splitext(self.video_path)[-1]
        if suffix != '.mp4' and suffix != '.avi' and suffix != '.flv':
            raise Exception('不支持格式')
        ffprobe_cmd = f'ffprobe -i {self.video_path} -show_entries format=duration -v quiet -of csv="p=0"'
        p = Popen(ffprobe_cmd, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = p.communicate()
        print(f"subprocess 执行结果：out:{out} err:{err}")
        duration_info = float(str(out, 'utf-8').strip())
        return int(duration_info * 1000)

    def get_file_size(self):
        """
        獲取文件尺寸
        """
        size = os.path.getsize(self.video_path)
        return format_size_to_kb(size)

    def get_vip_info(self) -> dict:
        ...

    def limit_of_use(self):
        """
        使用限制
        視頻時長和文件大小
        """
        duration = self.get_record_duration()
        file_size = self.get_file_size()
        if file_size < 5000 or duration <= 10:
            # 上傳oss
            return True

    def upload_oss(self):
        """
        上傳oss文件
        """
        return self.limit_of_use()

    def start_record(self, vedio_file: str, out_path: str, size: str = "1200x540", rate: str = "2000000"):
        """
        开线程 开始录制
        @param vedio_file: 文件名称 默认mp4
        @param out_path: 设备生成路径
        @param size: 分辨率
        @param rate: 比特率
        """
        self.process = Process(target=self.record, args=(vedio_file, out_path, size, rate))
        self.process.daemon = True
        self.process.start()

    def stop_record(self):
        """关闭录制"""
        try:
            os.kill(0, signal.CTRL_C_EVENT)  # 对当前所有进程发送ctrl+c操作
            self.process.join()
        except KeyboardInterrupt:
            print("录制结束")

    def save_video(self, max_size: float or int, out_path: str):
        """
        保存视频
        max_size应该和vip等级有关
        :return:
        """
        fp_size = os.path.getsize(self.video_path) / 1024
        print(fp_size)
        if fp_size <= max_size:
            compress = f"ffmpeg -i {self.video_path} -vcodec {self.lib_name} -crf 5 -y {out_path}"
            result = os.system(compress)
            if result != 0:
                return result, "没有安装或者配置ffmpeg"
            return result, "保存视频成功"
        return None, "视频长度过长"

    def pull_video(self, video_path: str):
        """
        推送视频到
        @param video_path: 视频位置
        """
        try:
            Popen("adb -s " + self.serial + " pull /sdcard/ " + video_path + os.sep,
                  shell=True)
        except Exception as e:
            print(e)
