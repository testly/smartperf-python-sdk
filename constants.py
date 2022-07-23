import six
import sys

if not six.PY3 or sys.version_info[1] < 6 or sys.version_info[1] > 10:
    raise Exception("Python版本最低是支持3.6-3.9")

from os.path import abspath, dirname, join


__all__ = ("pro_path_new", "join")


def pro_path_new() -> str:
    """返回当前项目根目录"""
    return abspath(dirname(__file__))


class Config:
    xml_file = "uidump.xml"
    tmp_path = "data/local/tmp/"
    xml_path = tmp_path + xml_file
    lib_name = "libx264"
    suffix_set = {"WMV", "ASF", "ASX", "RM", "RMVB", "MP4", "3GP", "MOV", "M4V", "AVI", "DAT", "MKV", "FIV",
                  "VOB"}
    queries_max = 3
