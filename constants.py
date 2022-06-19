from os.path import abspath, dirname, join

__all__ = ("pro_path_new", "join")


def pro_path_new() -> str:
    """返回当前项目根目录"""
    return abspath(dirname(__file__))
