def sort_file_list(file_list: list, sort_key: str = "name", reverse: bool = False) -> list:
    """
    通用文件列表排序函数
    :param file_list: 待排序的文件信息列表（每个元素是字典，包含"name"/"size"/"mtime"/"is_dir"等键）
    :param sort_key: 排序依据（可选值："name"名称/"size"大小/"mtime"修改时间）
    :param reverse: 是否降序（默认升序）
    :return: 排序后的文件列表
    """
    # 定义排序规则（文件夹优先 + 指定键排序）
    def sort_key_func(item):
        # 文件夹优先（is_dir为True时排前面）
        is_folder = 0 if item["is_dir"] else 1
        # 根据不同键返回排序值
        if sort_key == "size":
            key_value = item["size"]
        elif sort_key == "mtime":
            key_value = item["mtime"]
        else:  # 默认按名称排序
            # print(sort_key)
            key_value = item["name"].lower()  # 不区分大小写
        return (is_folder, key_value)
    # print(sort_key_func(file_list[0]))
    # 执行排序
    sorted_list = sorted(file_list, key=sort_key_func, reverse=reverse)
    # print(sorted_list)

    return sorted_list
