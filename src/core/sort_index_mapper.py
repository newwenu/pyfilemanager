import locale
import re
from typing import List, Dict, Callable

# 尝试设置中文本地化，如果失败则使用默认
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    pass


class SortIndexMapper:
    """
    排序索引映射器 - 使用索引映射优化排序性能

    核心优化：
    1. 不复制数据，只维护索引映射
    2. 排序时只排序索引，不移动源数据
    3. 通过索引映射访问排序后的数据
    """

    def __init__(self):
        self._source_list: List[Dict] = []
        self._folder_indices: List[int] = []  # 文件夹索引列表
        self._file_indices: List[int] = []    # 文件索引列表
        self._sorted_folder_indices: List[int] = []  # 排序后的文件夹索引
        self._sorted_file_indices: List[int] = []    # 排序后的文件索引

    def set_data(self, file_list: List[Dict]):
        """设置源数据 - 只保存引用，不复制"""
        self._source_list = file_list

        # 分离文件夹和文件的索引（不是数据）
        self._folder_indices = [
            i for i, item in enumerate(file_list)
            if item.get("is_dir", False)
        ]
        self._file_indices = [
            i for i, item in enumerate(file_list)
            if not item.get("is_dir", False)
        ]

    def sort(self, sort_key: str, reverse: bool = False,
             folders_grouped: bool = True, folders_before: bool = True) -> List[int]:
        """
        排序 - 返回排序后的索引列表

        :return: 排序后的索引列表，用于通过索引访问源数据
        """
        if not self._source_list:
            return []

        # 获取排序键函数
        key_func = self._get_sort_key_func(sort_key)

        # 对文件夹索引排序
        self._sorted_folder_indices = sorted(
            self._folder_indices,
            key=lambda idx: key_func(self._source_list[idx]),
            reverse=reverse
        )

        # 对文件索引排序
        self._sorted_file_indices = sorted(
            self._file_indices,
            key=lambda idx: key_func(self._source_list[idx]),
            reverse=reverse
        )

        # 根据 folders_before 合并索引
        if folders_grouped:
            if folders_before:
                return self._sorted_folder_indices + self._sorted_file_indices
            else:
                return self._sorted_file_indices + self._sorted_folder_indices
        else:
            # 不归并：混合排序所有索引
            all_indices = list(range(len(self._source_list)))
            return sorted(
                all_indices,
                key=lambda idx: key_func(self._source_list[idx]),
                reverse=reverse
            )

    def get_sorted_list(self, indices: List[int]) -> List[Dict]:
        """通过索引列表获取排序后的数据（按需生成）"""
        return [self._source_list[i] for i in indices]

    def _get_sort_key_func(self, sort_key: str) -> Callable:
        """获取排序键函数"""
        def sort_key_func(item: Dict):
            if sort_key == "size":
                return item.get("size", 0)
            elif sort_key == "mtime":
                return item.get("mtime", 0) or 0
            else:  # 默认按名称排序
                name = item.get("name", "")
                return self._natural_sort_key(name)

        return sort_key_func

    @staticmethod
    def _natural_sort_key(s: str) -> list:
        """自然排序键函数 - 支持数字和中文"""
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        return [convert(c) for c in re.split('([0-9]+)', s)]


# 全局排序索引映射器实例
_index_mapper = SortIndexMapper()


def sort_file_list(file_list: List[Dict], sort_key: str = "name", reverse: bool = False,
                   folders_grouped: bool = True, folders_before: bool = True) -> List[Dict]:
    """
    通用文件列表排序函数 - 使用索引映射优化性能

    :param file_list: 待排序的文件信息列表
    :param sort_key: 排序依据（"name"/"size"/"mtime"）
    :param reverse: 是否降序
    :param folders_grouped: 是否文件夹归并
    :param folders_before: 文件夹是否排在前面
    :return: 排序后的文件列表
    """
    _index_mapper.set_data(file_list)
    sorted_indices = _index_mapper.sort(sort_key, reverse, folders_grouped, folders_before)
    return _index_mapper.get_sorted_list(sorted_indices)


def get_sorted_indices(file_list: List[Dict], sort_key: str = "name", reverse: bool = False,
                       folders_grouped: bool = True, folders_before: bool = True) -> List[int]:
    """
    获取排序后的索引列表 - 用于增量更新UI

    :return: 排序后的索引列表
    """
    _index_mapper.set_data(file_list)
    return _index_mapper.sort(sort_key, reverse, folders_grouped, folders_before)
