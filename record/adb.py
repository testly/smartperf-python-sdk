import platform
import re
import subprocess
import sys
from time import sleep
import os
from typing import Union, Type, List, Optional, Tuple, Dict, Match, Iterator, Final, Generator, Any
from constants import *
from functools import wraps
from inspect import isfunction

from exceptions import AdbDeviceConnectError, AdbError, NoDeviceSpecifyError, AdbTimeout


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


class AdbUtils:
    SUBPROCESS_FLAG: Final[int] = stream_kwargs()['creation_flags']

    def __init__(self, device_id: Optional[str] = None, adb_path: Optional[str] = None):
        """
        Args:
            device_id (str): 指定设备名
            adb_path (str): 指定adb路径
            host (str): 指定连接地址
            port (int): 指定连接端口
        """
        self.device_id = device_id
        self.adb_path = adb_path or self.builtin_adb_path()
        self.connect()

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

    def get_device_id(self, decode: bool = False) -> str:
        return decode and self.device_id.replace(':', '_') or self.device_id

    def start_server(self) -> None:
        """
        command 'adb start_server'
        Returns:
            None
        """
        self.cmd('start-server', devices=False)

    def kill_server(self) -> None:
        """
        command 'adb kill_server'
        Returns:
            None
        """
        self.cmd('kill-server', devices=False)

    @Retries(2, exceptions=(AdbDeviceConnectError,))
    def connect(self, force: Optional[bool] = False) -> None:
        """
        command 'adb connect <device_id>'
        Args:
            force: 不判断设备当前状态,强制连接
        Returns:
                连接成功返回True,连接失败返回False
        """
        if self.device_id and ':' in self.device_id and (force or self.status != 'devices'):
            ret = self.cmd(f"connect {self.device_id}", devices=False, skip_error=True)
            if 'failed' in ret:
                raise AdbDeviceConnectError(f'failed to connect to {self.device_id}')

    def push(self, local: str, remote: str) -> None:
        """
        command 'adb push <local> <remote>'
        Args:
            local: 发送文件的路径
            remote: 发送到设备上的路径
        Raises:
            RuntimeError:文件不存在
        Returns:
            None
        """
        if not os.path.isfile(local):
            raise RuntimeError(f"file: {local} does not exists")
        self.cmd(['push', local, remote], decode=False)

    def disconnect(self) -> None:
        """
        command 'adb -s <device_id> disconnect'
        Returns:
            None
        """
        if ':' in self.device_id:
            self.cmd(f"disconnect {self.device_id}", devices=False)

    def get_std_encoding(self, stream):
        """
        Get encoding of the stream
        Args:
            stream: stream
        Returns:
            encoding or file system encoding
        """
        return getattr(stream, "encoding", None) or sys.getfilesystemencoding()

    @property
    def status(self) -> Optional[str]:
        """
        command adb -s <device_id> get-state,返回当前设备状态
        Returns:
            当前设备状态
        """
        proc = self.start_cmd('get-state')
        stdout, stderr = proc.communicate()

        stdout = stdout.decode(self.get_std_encoding(stdout))
        stderr = stderr.decode(self.get_std_encoding(stdout))

        if proc.returncode == 0:
            return stdout.strip()
        elif "not found" in stderr:
            return None
        elif 'device offline' in stderr:
            return 'offline'
        else:
            raise AdbError(stdout, stderr)

    def split_cmd(self, cmds) -> list:
        """
        Split the commands to the list for subprocess
        Args:
            cmds (str): command
        Returns:
            command list
        """
        # cmds = shlex.split(cmds)  # disable auto removing \ on windows
        return cmds.split() if isinstance(cmds, str) else list(cmds)

    def start_cmd(self, cmds: Union[list, str], devices: bool = True) -> subprocess.Popen:
        """
        根据cmds创建一个Popen
        Args:
            cmds: cmd commands
            devices: 如果为True,则需要指定device-id,命令中会传入-s
        Raises:
            NoDeviceSpecifyError:没有指定设备运行cmd命令
        Returns:
            Popen管道
        """
        cmds = self.split_cmd(cmds)
        if devices:
            if not self.device_id:
                raise NoDeviceSpecifyError('must set device_id')
        print(' '.join(cmds))
        proc = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=self.SUBPROCESS_FLAG
        )
        return proc

    def cmd(self, cmds: Union[list, str], devices: Optional[bool] = True, decode: Optional[bool] = True,
            timeout: Optional[int] = None, skip_error: Optional[bool] = False):
        """
        创建cmd命令, 并返回命令返回值
        Args:
            cmds (list,str): 需要运行的参数
            devices (bool): 如果为True,则需要指定device-id,命令中会传入-s
            decode (bool): 是否解码stdout,stderr
            timeout (int): 设置命令超时时间
            skip_error (bool): 是否跳过报错
        Raises:
            AdbDeviceConnectError: 设备连接异常
            AdbTimeout:输入命令超时
        Returns:
            返回命令结果stdout
        """

        proc = self.start_cmd(cmds, devices)
        if timeout and isinstance(timeout, int):
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                _, stderr = proc.communicate()
                raise AdbTimeout(f"cmd command {' '.join(proc.args)} time out")
        else:
            stdout, stderr = proc.communicate()

        if decode:
            stdout = stdout.decode(self.get_std_encoding(stdout))
            stderr = stderr.decode(self.get_std_encoding(stderr))

        if proc.returncode > 0:
            pattern = AdbDeviceConnectError.CONNECT_ERROR
            if isinstance(stderr, bytes):
                pattern = pattern.encode("utf-8")
            if re.search(pattern, stderr):
                raise AdbDeviceConnectError(stderr)
            if not skip_error:
                raise AdbError(stdout, stderr)

        return stdout

    def pull(self, local: str, remote: str) -> None:
        """
        command 'adb pull <remote> <local>
        Args:
            local: 本地的路径
            remote: 设备上的路径
        Returns:
            None
        """
        self.cmd(['pull', remote, local], decode=False)

    def set_xml_push_local(self):
        """
        获取页面布局
        :return:
        """
        result = self.start_cmd("uiautomator dump /sdcard/ui.xml")
        if len(result) > 1:
            print(result)
            ui_file = join(pro_path_new(), "ui.xml")
            self.start_cmd(f"pull /sdcard/ui.xml {ui_file}")
