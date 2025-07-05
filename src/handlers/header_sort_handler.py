from PySide6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from utils.sort_utils import sort_file_list  # 新增：导入排序工具
class HeaderSortHandler:
    def __init__(self, file_list_updater):
        self.fm = file_list_updater  # 关联文件列表更新器
        # 新增：列索引与排序键的映射（需与文件列表表头顺序一致）
        self.column_to_key = {
            0: "name",   # 第0列：名称
            1: "size",   # 第1列：大小
            2: "mtime"   # 第2列：修改时间
        }
        self.current_sort_column = 0  # 默认排序列（第0列）
        self.current_sort_key = "name"  # 默认排序键（与列映射同步）
        self.current_reverse = False   # 默认升序
        
        # 绑定表头事件（自动获取文件列表表头）
        self.file_list_header = self.fm.file_list.header()
        # print("Header sections:", self.file_list_header.count())
        # print("SectionsClickable:", self.file_list_header.sectionsClickable())
        self.file_list_header.sectionClicked.connect(self.on_header_clicked)
        self.file_list_header.sectionDoubleClicked.connect(self.on_header_double_clicked)

    def on_header_clicked(self, logical_index):
        """单击表头时切换排序顺序（支持所有列）"""
        # print(f"点击了第{logical_index}列")
        # 校验列是否在映射中（避免无效列）
        if logical_index not in self.column_to_key:
            # print("无效的排序列")
            return
        # print(f"当前列：{self.current_sort_column}，当前键：{self.current_sort_key}，当前方向：{self.current_reverse}")
        # 更新当前排序列和键
        self.current_sort_column = logical_index
        self.current_sort_key = self.column_to_key[logical_index]
        # print(f"点击了第{logical_index}列，排序键：{self.current_sort_key}")
        # 切换排序方向
        self.current_reverse = not self.current_reverse
        # 触发排序并更新表头
        self._update_header_text()
        self._update_sorted_list()
        
    def on_header_double_clicked(self, logical_index):
        """双击表头时显示排序方式选择对话框（支持所有列）"""
        if logical_index not in self.column_to_key:
            return
        
        dialog = QDialog(self.fm.fm)
        dialog.setWindowTitle("选择排序方式")
        layout = QVBoxLayout(dialog)
        
        # 单选按钮：根据当前列动态显示可选排序方式（示例固定为名称/大小/修改时间）
        rb_name = QRadioButton("按名称排序", dialog)
        rb_size = QRadioButton("按大小排序", dialog)
        rb_mtime = QRadioButton("按修改时间排序", dialog)
        # 关联当前排序键
        rb_name.setChecked(self.current_sort_key == "name")
        rb_size.setChecked(self.current_sort_key == "size")
        rb_mtime.setChecked(self.current_sort_key == "mtime")
        layout.addWidget(rb_name)
        layout.addWidget(rb_size)
        layout.addWidget(rb_mtime)
        
        # 按钮布局（确定+取消）
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定", dialog)
        btn_cancel = QPushButton("取消", dialog)
        btn_ok.clicked.connect(lambda: self._on_sort_selected(dialog, rb_name, rb_size, rb_mtime))
        btn_cancel.clicked.connect(dialog.close)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def _on_sort_selected(self, dialog, rb_name, rb_size, rb_mtime):
        """用户选择排序方式后的处理（同步更新列和键）"""
        if rb_name.isChecked():
            self.current_sort_key = "name"
            self.current_sort_column = 0  # 名称对应第0列
        elif rb_size.isChecked():
            self.current_sort_key = "size"
            self.current_sort_column = 1  # 大小对应第1列
        elif rb_mtime.isChecked():
            self.current_sort_key = "mtime"
            self.current_sort_column = 2  # 修改时间对应第2列
        dialog.close()

        # print(f"选择了{self.current_sort_column}列，排序键：{self.current_sort_key}，排序方向：{self.current_reverse}")
        self._update_header_text()
        self._update_sorted_list()
        # self.on_header_clicked(self.current_sort_column)

        

    def _update_sorted_list(self):
        """调用排序逻辑并刷新文件列表（增加数据校验）"""
        try:
            current_file_list = self.fm.file_list_data
            # 校验数据是否存在（避免空列表或字段缺失）
            if not current_file_list or self.current_sort_key not in current_file_list[0]:
                raise ValueError(f"无效排序键：{self.current_sort_key} 或文件列表数据为空")
            
            sorted_list = sort_file_list(
                current_file_list,
                sort_key=self.current_sort_key,
                reverse=self.current_reverse
            )
            # print(self.current_reverse)
            self.fm._update_filelist_from_sorted(sorted_list)
            # self.fm._update_filelist_from_thread(sorted_list)
        except Exception as e:
            # 错误提示（与工程现有错误处理风格一致）
            from handlers.m_event_handlers import show_error
            show_error(self.fm.fm, "排序失败", str(e))

    def _update_header_text(self):
        """更新当前排序列的表头文本（如“大小↑”）"""
        # self.fm.update_filelist()
        self.fm._setup_header_layout()
        direction = "↑" if not self.current_reverse else "↓"
        # 获取原始标题（假设self.original_header_titles是原始标题列表）
        if not hasattr(self, 'original_header_titles'):
            self.original_header_titles = [self.file_list_header.model().headerData(i, Qt.Horizontal) for i in range(self.file_list_header.count())]

        if self.current_sort_column < len(self.column_to_key):
            # print(f"当前排序列：{self.current_sort_column}, 原始标题：{self.original_header_titles}")
            original_title = self.original_header_titles[self.current_sort_column]
        else:
            original_title = "未知列"  # 兜底处理越界情况
        # 仅使用原始标题 + 当前方向符号
        self.fm.file_list.headerItem().setText(self.current_sort_column, f"{original_title}{direction}")