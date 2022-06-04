import platform
from functools import lru_cache
from subprocess import Popen, PIPE
import os


class StartApp:

    def __init__(self, serial=None):
        """
        :param serial: 通过_init_adb()被缓存起来
        """
        self._serial = serial
        self._adb = self.builtin_adb_path()
        self._adb_name = self._adb.adb_path
        if not self._adb_name:
            print("adb.exe文件缺少")
        self.findstr = 'findstr' if platform.system() == "Windows" else 'grep'
        self.device_id = {'only_dev': self._serial}

    def builtin_adb_path(self):
        """
        Return built-in adb executable path
        Returns:
        adb executable path
        """
        system = platform.system()
        machine = platform.machine()
        DEFAULT_ADB_PATH = {}
        adb_path = DEFAULT_ADB_PATH.get(f'{system}-{machine}')
        if not adb_path:
            adb_path = DEFAULT_ADB_PATH.get(system)
        if not adb_path:
            raise RuntimeError(f"No adb executable supports this platform({system}-{machine}).")
        # overwrite uiautomator adb
        if "ANDROID_HOME" in os.environ:
            del os.environ["ANDROID_HOME"]
        return adb_path

    @property
    def serial(self):
        return self._serial

    @serial.setter
    @lru_cache()
    def serial(self, ser):
        self._serial = ser

    @property
    def adb_name(self):
        return self._adb_name

    @property
    @lru_cache()
    def current_package_name(self):
        """获取当前运行app包名
        :return:
        """
        return self.current_package_info[0]

    @property
    @lru_cache()
    def current_package_info(self):
        """获取当前包信息"""
        result = self.adb_shell(f'dumpsys activity activities | {self.findstr} mResumedActivity')
        assert len(result) == 1, "手机屏幕没有激活AND没有解锁OR获取当前包信息错误"
        rs = result[0].split()
        for r in rs:
            if r.find('/') != -1:
                return r.split("/")

    @property
    @lru_cache()
    def current_activity_name(self):
        """获取当前运行activity
        :return:
        """
        return self.current_package_info[1]

    def _init_adb(self):
        """
        初始化adb
        :return:
        """
        if not self.serial:
            devices_info = self.devices()
            print(devices_info)
            if devices_info:
                for i in devices_info:
                    print(f"当前通过数据线连接的安卓设备有{i}")
                device = devices_info.pop(0)
                self.serial = device
            else:
                print("当前没有已连接的安卓设备")
        else:
            print(f"当前连接的安卓设备有:{self.serial}")

    def is_connect(self):
        """
        检查是否链接
        :return:
        """
        return self.serial in self.devices()

    def adb(self, *args) -> list:
        """adb命令执行入口
        :param args:
        :return:
        """
        if self.serial:
            cmd = " ".join([self.adb_name, '-s', self.serial] + list(args))
        else:
            cmd = " ".join([self.adb_name] + list(args))
        stdout, stderr = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE).communicate()
        result = [i.decode() for i in stdout.splitlines()]
        return [i for i in result if i and not i.startswith("* daemon")]  # 过滤掉空的行，以及adb启动消息

    def adb_shell(self, *args):
        """adb shell命令入口
        :param args:
        :return:
        """
        args = ['shell'] + list(args)
        return self.adb(*args)

    def devices(self) -> list:
        """获取手机"""
        result = self.device_id.get(self._serial, self.adb('devices'))
        return [i.split()[0] for i in result if not i.startswith('List') and not i.startswith("adb")] if len(
            result) > 1 else []

    def start_app(self, package_name: str, activity_name: str):
        """
        啓動app
        """
        lines = self.adb_shell(f"am start -W {package_name}/{activity_name}")
        for line in lines:
            result = line.decode(encoding='utf8')
            if "ThisTime" in result:
                # 对字符串进行分割处理提取出启动时间
                return result.strip().split(":")[-1].strip()
