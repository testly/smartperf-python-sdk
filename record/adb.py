import re
import subprocess
import sys
import time
from multiprocessing import Process
from time import sleep
import os
from constants import *
from functools import wraps
from inspect import isfunction
import xml.etree.cElementTree as et

from constants import Config


class Retries:
    def __init__(self, max_tries: int, delay: int = 1,
                 exceptions: tuple = (Exception,), hook=None):
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
    SUBPROCESS_FLAG = stream_kwargs()['creation_flags']
    queries = 0
    video_path = ""

    def __init__(self):
        """
        Args:
        adb_path (str): 指定adb路径
        """
        self.device_id = self.get_device_id()
        print(self.device_id)
        self.load_path()
        if self.check_adb_device():
            self.dump_file = join(pro_path_new(), "dump", self.xml_file)
            self.xml_root()

    def load_path(self):
        """
        使用adb地址
        Returns:
        adb executable path
        """
        os.environ['path'] += f'{join(pro_path_new(), "res")};'
        print(os.environ['path'])

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
        @param mp4_path: 文件名称 格式默认为mp4 size: 分辨率(目前未使用) rate: 比特率
        """
        try:
            if mp4_path.endswith('.mp4'):
                print("开始录屏")
                self.video_path = join(pro_path_new(), "res", mp4_path)
                res_path = join(pro_path_new(), "res")
                os.chdir(res_path)
                subprocess.Popen(f"scrcpy -s {self.device_id} --no-display --record {self.video_path}", shell=True)
            else:
                raise Exception(f"{mp4_path}上传的格式不是Mp4")
        except KeyboardInterrupt:
            pass

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

    def start_record(self, mp4_file: str):
        """
        开线程 开始录制
        size: 分辨率   "1200x540" rate: 比特率  "2000000"
        :param mp4_file:
        """
        self.p = Process(target=self.record, args=(mp4_file,))
        self.p.daemon = True
        self.p.start()

    def stop_record(self):
        """关闭录制"""
        try:
            self.p.join()
        except KeyboardInterrupt as e:
            print(f"录制结束={e}")
        finally:
            self.p.terminate()

