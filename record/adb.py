import platform
import re
import signal
import subprocess
import sys
import time
from subprocess import Popen, PIPE
from multiprocessing import Process
from time import sleep
import os
from typing import Type, Optional, Tuple, Final
from constants import *
from functools import wraps
from inspect import isfunction
import xml.etree.cElementTree as et

from constants import Config


class Retries:
    def __init__(self, max_tries: int, delay: Optional[int] = 1,
                 exceptions: Tuple[Type[Exception], ...] = (Exception,), hook=None):
        """
        通过装饰器实现的"重试"函数
        Args:
            max_tries: 最大可重试次数。超出次数后仍然失败,则弹出异常
            delay: 重试等待间隔
            exceptions: 需要检测的异常
            hook: 钩子函数
        """
        self.max_tries = max_tries
        self.delay = delay
        self.exceptions = exceptions
        self.hook = hook

    def __call__(self, func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            tries = list(range(self.max_tries))
            tries.reverse()
            for tries_remaining in tries:
                try:
                    return func(*args, **kwargs)
                except self.exceptions as err:
                    if tries_remaining > 0:
                        if isfunction(self.hook):
                            self.hook(tries_remaining, err)
                        sleep(self.delay)
                    else:
                        raise err

        return wrapped_function


def stream_kwargs() -> dict:
    creation_flags = 0
    startupinfo = None
    if sys.platform.startswith('win'):
        try:
            creation_flags = subprocess.CREATE_NO_WINDOW
        except AttributeError:
            creation_flags = 0x8000000
    return {
        'creation_flags': creation_flags,
        'startup_info': startupinfo,
    }


class AdbUtils(Config):
    SUBPROCESS_FLAG: Final[int] = stream_kwargs()['creation_flags']
    queries = 0
    video_path = ""

    def __init__(self, adb_path: Optional[str] = None):
        """
        Args:
        adb_path (str): 指定adb路径
        """
        self.device_id = self.get_device_id()
        print(self.device_id)
        self.adb_path = adb_path or self.builtin_adb_path()
        if self.check_adb_device():
            self.dump_file = join(pro_path_new(), "dump", self.xml_file)
            self.xml_root()

    def builtin_adb_path(self):
        """
        使用adb地址
        Returns:
        adb executable path
        """
        system = platform.system()
        machine = platform.machine()
        DEFAULT_ADB_PATH = {}
        adb_path = DEFAULT_ADB_PATH.get(f'{system}-{machine}')
        if not adb_path:
            adb_path = DEFAULT_ADB_PATH.get(system)
            print(adb_path)
        return adb_path

    def get_device_id(self):
        """
        获取设备id
        :return:
        """
        device = os.popen("adb devices").readlines()
        if len(device) > 1:
            device_id = device[1]
            return device_id.split()[0]

    def check_adb_device(self):
        """
        检查adb状态
        :return:
        """
        state = os.popen("adb get-state").readlines()
        if state and "device" in state[0]:
            return True
        else:
            os.popen("adb kill-server")
            os.popen("adb start-server")
            return self.check_adb_device()

    def click_pos(self, x_pos, y_pos):
        """
        单击地址
        :param x_pos:
        :param y_pos:
        :return:
        """
        os.popen(f'adb -s {self.device_id} shell input tap {x_pos} {y_pos}')

    def xml_root(self):
        """
        获取页面布局后进行操作
        attrib_name
        text_name
        :return:
        """
        time.sleep(5)
        os.popen(f'adb -s {self.device_id} shell uiautomator dump --compressed /{self.xml_path}')
        os.popen(f'adb -s {self.device_id} pull {self.xml_path} {self.dump_file}')
        if not os.path.exists(self.dump_file):
            raise Exception(f"dump文件不存在{self.dump_file}")
        source = et.parse(self.dump_file)
        self.root = source.getroot()

    def start_app(self, app_text: str, mp4_name: str):
        """
        启动app
        :param mp4_name:
        :param app_text:推荐使用应用名称 是最简单的 attribte就是用text
        :return:
        """
        print(f"请确保当前{app_text}不在后台并且没有被启动")
        if self.queries == self.queries_max:
            raise Exception(f"超过查询{self.queries_max}次")
        for node in self.root.iter("node"):
            print(node.attrib)
            if node.attrib["text"] == app_text:
                # os.popen(f"adb shell am force-stop {node.attrib['package']}")
                bounds = node.attrib["bounds"]
                pattern = re.compile(r"\d+")
                coord = pattern.findall(bounds)
                x_pos = (int(coord[2]) - int(coord[0])) / 2.0 + int(coord[0])
                y_pos = (int(coord[3]) - int(coord[1])) / 2.0 + int(coord[1])
                # 进行开始录屏
                self.start_record(mp4_name)
                time.sleep(.1)
                self.click_pos(x_pos, y_pos)
                return
        self.queries += 1
        return self.start_app(app_text, mp4_name)

    def record(self, mp4_path: str):
        """
        进行录屏
        @param mp4_path: 文件名称 格式默认为mp4
        @param size: 分辨率(目前未使用)
        @param rate: 比特率
        """
        try:
            if mp4_path.endswith('.mp4'):
                print("开始录屏")
                self.video_path = join(pro_path_new(), "res", mp4_path)
                subprocess.Popen(f"scrcpy -s {self.device_id} --no-display --record {self.video_path}", shell=True)
            else:
                raise Exception(f"{mp4_path}上传的格式不是Mp4")
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

    def is_video(self, input_path: str) -> bool:
        """
        判断是视频
        :return:
        """
        if input_path.rsplit(".", 1):
            suffix = input_path.rsplit(".", 1)[-1].upper()
            return suffix in self.suffix_set

    def get_file_size(self):
        """
        獲取文件尺寸
        """
        size = os.path.getsize(self.video_path)
        return self.format_size_to_kb(size)

    def format_size_to_kb(self, data):
        """
        處理文件大小轉換 kb
        """
        res_bytes = float(data)  # 默认字节
        if res_bytes:
            return res_bytes / 1024

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

    def start_record(self, mp4_file: str):
        """
        开线程 开始录制
        @param vedio_file: 文件名称 默认mp4
        @param out_path: 设备生成路径
        @param size: 分辨率   "1200x540"
        @param rate: 比特率  "2000000"
        """
        self.process = Process(target=self.record, args=(mp4_file,))
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
        time.sleep(3)
        fp_size = os.path.getsize(self.video_path) / 1024
        print(fp_size)
        if fp_size <= max_size:
            compress = f"ffmpeg -i {self.video_path} -vcodec {self.lib_name} -crf 5 -y {out_path}"
            result = os.system(compress)
            if result != 0:
                return result, "没有安装或者配置ffmpeg"
            return result, "保存视频成功"
        return None, "视频长度过长"
