from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSplitter, QHBoxLayout,
                               QLineEdit, QPushButton, QCheckBox, QTreeWidget, QHeaderView,
                               QAbstractItemView, QStatusBar,QStackedWidget,QPushButton,QGraphicsBlurEffect) 

from PySide6.QtGui import QFont,QColor ,QPalette # ：导入QFont用于字体设置
from PySide6.QtCore import Qt, QSize
from utils.file_utils import create_char_icon
from widgets.navigation_tree import init_navigation_tree
from widgets.focus_style_filter import install_focus_style_filter  # 导入
from PySide6.QtWidgets import QApplication
from widgets.custom_tree_widget import FileListWidget

# 导入配置
from core import app_config


class UISetup:
    """UI 设置管理类"""

    def __init__(self, main_window, config_manager):
        """初始化 UI 设置管理器"""
        self.main_window = main_window
        # 保留 config_manager 引用，因为设置对话框需要修改配置
        self.config_manager = config_manager
        # 使用 app_config 读取配置
        self.config = app_config.get_all()
        self.translation = main_window.translation
        self.font_family = app_config.font_family
        # 初始化系统背景色
        if not main_window.sys_bg:
            main_window.sys_bg = QApplication.palette().color(QPalette.Window)
            # print(f"系统背景颜色: {main_window.sys_bg}")

        # 缓存常用参数，避免重复获取
        self.font_size = app_config.font_size
        self.status_font_size = app_config.status_font_size
        self.nav_tree_font_size = app_config.nav_tree_font_size
        self.file_list_font_size = app_config.file_list_font_size
        self.bg_alpha1 = app_config.nav_tree_bg_alpha
        self.bg_alpha2 = app_config.file_list_bg_alpha
        self.nav_tree_icon_size = app_config.nav_tree_icon_size
        self.file_list_icon_size = app_config.file_list_icon_size
        
        # 缓存系统背景色RGB值
        r, g, b, _ = self.main_window.sys_bg.getRgb()
        self.sys_bg_r = r
        self.sys_bg_g = g
        self.sys_bg_b = b
        
        # 缓存字体对象
        self.file_font = QFont()
        self.file_font.setPointSize(self.font_size)
    
    def setup_ui(self):
        """主窗口 UI 初始化入口函数"""
        self.setup_window()
        self.setup_main_layout()
        self.setup_top_widget()
        self.setup_status_bar()
        self.setup_splitter()  # 新增：传递 translation 参数
        self.main_window.file_list.header().setSectionsClickable(True) # 设置表头可点击
        # 设置选择模式为多选（关键修改）
        self.main_window.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def setup_window(self):
        """设置窗口基础属性"""
        self.main_window.setWindowTitle(self.translation.get("window_title", "极简文件管理器"))  # 从翻译文件获取标题
        init_width, init_height = self.config.get("initial_size", [800, 600])
        self.main_window.setGeometry(200, 100, init_width, init_height)
        self.main_window.setWindowIcon(create_char_icon('📂'))

    def setup_main_layout(self):
        """设置主容器布局"""
        main_widget = QWidget()
        self.main_window.setCentralWidget(main_widget)
        self.main_window.main_layout = QVBoxLayout(main_widget)
        self.main_window.bg_label = QLabel(self.main_window.centralWidget())
        self.main_window.bg_label.setScaledContents(True)
        self.main_window.bg_label.lower()

        # 调用独立方法初始化设置按钮
        # setup_settings_button(main_window)

    def setup_top_widget(self):
        """设置顶部功能区（修改：确保按钮属性正确绑定）"""
        top_widget = QWidget()
        top_widget.setFixedHeight(30)
        top_widget.setStyleSheet(f"background-color: rgba({self.sys_bg_r}, {self.sys_bg_g}, {self.sys_bg_b}, 108);")  # 半透明背景
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(1, 1, 1, 1)
        top_layout.setSpacing(9)
        
        control_height = 30  # 控制按钮高度
        self.main_window.address_bar = QLineEdit()
        # 地址栏提示（翻译缺失时显示"输入路径..."）
        self.main_window.address_bar.setPlaceholderText(self.translation.get("address_bar_placeholder", "输入路径..."))
        
        # 显式初始化 btn_new_folder 并绑定到 main_window
        self.main_window.btn_new_folder = QPushButton(self.translation.get("new_folder", "新建文件夹"))
        self.main_window.btn_new_folder.setFixedHeight(control_height)  # 按钮高度
        
        # 显示隐藏文件复选框（翻译缺失时显示"显示隐藏文件"）
        self.main_window.cb_hidden = QCheckBox(self.translation.get("cb_hidden", "显示隐藏文件"))
        self.main_window.cb_hidden.setFixedHeight(control_height)  # 复选框高度
        # 设置复选框初始状态与配置文件同步
        self.main_window.cb_hidden.setChecked(self.config.get("show_hidden_files", False))

        # 显示所有大小复选框（翻译缺失时显示"显示所有大小"）
        self.main_window.cb_show_sizes = QCheckBox(self.translation.get("cb_show_sizes", "显示所有大小"))
        self.main_window.cb_show_sizes.setFixedHeight(control_height)  # 复选框高度
        # 设置复选框初始状态与配置文件同步
        self.main_window.cb_show_sizes.setChecked(self.config.get("show_all_sizes", False))

        self.main_window.address_bar.setFixedHeight(control_height)  # 地址栏高度
        self.main_window.address_bar.installEventFilter(self.main_window.keyboard_handler)  # 让 KeyboardHandler 监听地址栏事件

        self.main_window.main_layout.addWidget(top_widget, stretch=-10)
        top_layout.addWidget(self.main_window.address_bar)
        top_layout.addWidget(self.main_window.cb_show_sizes)
        top_layout.addWidget(self.main_window.cb_hidden)
        # top_layout.addWidget(main_window.btn_new_folder)  # 确保按钮添加到布局
        top_layout.setContentsMargins(1,1, 1, 1)  # 设置边距

    def setup_splitter(self):
        """设置左右分栏布局（完整实现）"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧导航树
        self.main_window.nav_tree = QTreeWidget()
        self.main_window.nav_tree.setObjectName("nav_tree")
        # 关键修改：使用翻译设置导航树标题
        self.main_window.nav_tree.setHeaderLabel(self.translation.get("nav_tree_header", "分区"))  # 新增翻译
        
        # 修改：使用独立配置的图标大小
        self.main_window.nav_tree.setIconSize(QSize(self.nav_tree_icon_size, self.nav_tree_icon_size))  # 调大图标尺寸
        self.main_window.nav_tree.setFont(self.file_font)
        # 保存导航树的初始样式（）
        nav_initial_style = f"""
            QTreeWidget {{
                background-color: rgba({self.sys_bg_r}, {self.sys_bg_g}, {self.sys_bg_b}, {self.bg_alpha1});  
            }}
            QTreeWidget::item {{ 
                height: {self.nav_tree_icon_size}px;
                padding-left: 1px;
            }}
        """
        self.main_window.nav_tree.setStyleSheet(nav_initial_style)  # 应用初始样式
        splitter.addWidget(self.main_window.nav_tree)
        
        # 右侧内容容器（使用QStackedWidget管理切换）
        right_stack = QStackedWidget()
        splitter.addWidget(right_stack)
        
        # 右侧文件列表（半透明背景）
        # 主文件列表初始化（使用FileListWidget）
        self.main_window.file_list = FileListWidget(self.main_window)
        # self.main_window.file_list.setObjectName("file_list")
        # main_window.file_list.setHeaderLabels(["名称", "大小"])  
        # 关键修改：使用翻译设置文件列表表头
        self.main_window.file_list.setHeaderLabels([
            self.translation.get("name", "名称"),  # 新增翻译
            self.translation.get("size", "大小")   # 新增翻译
        ])
        self.main_window.file_list.setObjectName("file_list")  # 添加对象名称标识
        # main_window.file_list.setHeaderLabels(["名称", "大小"])
        # main_window.file_list.setColumnHidden(2, True)  # 隐藏“修改时间”列
        header = self.main_window.file_list.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)

        # 修改：使用独立配置的图标大小
        self.main_window.file_list.setIconSize(QSize(self.file_list_icon_size, self.file_list_icon_size))
        # ：使用QFont设置字体大小（替代原样式表中的font-size）
        file_list_font = QFont(self.font_family)
        file_list_font.setPointSize(self.config.get("file_list_font_size", 12))  # 从配置中获取字体大小
        self.main_window.file_list.setFont(file_list_font)
        # 保存文件列表的初始样式（关键修改）
        initial_style = f"""
            QTreeWidget {{
                background-color: rgba({self.sys_bg_r}, {self.sys_bg_g}, {self.sys_bg_b}, {self.bg_alpha2});
            }}
            QTreeWidget::item {{ 
                height: {self.file_list_icon_size}px;
                margin: 0.5px 0;
                padding: 0 2px;
            }}
        """
        self.main_window.file_list.setStyleSheet(initial_style)  # 应用初始样式
        # 启用平滑滚动
        self.main_window.file_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        # 设置快速滚动加速
        self.main_window.file_list.verticalScrollBar().setSingleStep(20)
        self.main_window.file_list.verticalScrollBar().setPageStep(400)
        right_stack.addWidget(self.main_window.file_list)  # 添加到栈式窗口
        splitter.addWidget(right_stack)
        
        # ：独立驱动器列表（默认隐藏）
        self.main_window.drive_list = QTreeWidget()
        self.main_window.drive_list.setObjectName("drive_list")
        # 关键修改：使用翻译设置驱动器列表表头
        self.main_window.drive_list.setHeaderLabels([
            self.translation.get("drive_list_name", "名称"),    # 新增翻译
            self.translation.get("drive_list_usage", "空间使用情况")  # 新增翻译
        ])
        
        # 继承file_list样式（可根据需求单独配置）
        self.main_window.drive_list.setFont(self.file_font)
        self.main_window.drive_list.setStyleSheet(self.main_window.file_list.styleSheet())  # 复用样式
        right_stack.addWidget(self.main_window.drive_list)  # 添加到栈式窗口

        # 保存栈式窗口引用以便切换
        self.main_window.right_stack = right_stack

        self.main_window.main_layout.addWidget(splitter)
        splitter.setSizes([int(self.main_window.width() * 0.35), int(self.main_window.width() * 0.65)])
        
        # # 初始化导航树（传递导航树实例和主窗口的图标集合）
        # init_navigation_tree(main_window.nav_tree, main_window.drive_icons)  # 传递图标参数
        
        # 触发首次文件列表更新（使用主窗口已初始化的 file_list_updater）
        # main_window.update_filelist()  # 关键修改：调用主窗口的更新方法

        # 初始化导航树（传递图标集合和翻译）
        init_navigation_tree(
            self.main_window.nav_tree,
            self.main_window.drive_icons,
            translation=self.translation  # 传递翻译字典
        )
        # 安装文件列表焦点过滤器（调用统一函数）
        install_focus_style_filter(self.main_window.file_list, initial_style, self.main_window.sys_bg)

        # 安装导航树焦点过滤器（调用统一函数）
        install_focus_style_filter(self.main_window.nav_tree, nav_initial_style, self.main_window.sys_bg)
        # ：启用触摸事件接收（适配触摸设备）
        # self.main_window.file_list.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

    def setup_status_bar(self):
        """设置状态栏和工具栏（修改：适配类方法）"""
        # 状态栏
        status_bar = QStatusBar()
        status_bar.setObjectName("status_bar")
        # status_bar.setStyleSheet(f"""
        #     QStatusBar {{
        #         background-color: rgba(0, 0, 0, 128);
        #         color: rgba(255, 255, 255, 200);
        #         font-size: {self.status_font_size}pt;
        #     }}
        # """)
        self.main_window.setStatusBar(status_bar)
        self.main_window.status_bar = status_bar
        self.main_window.status_bar.showMessage(self.translation.get("status_ready", "就绪提示"))

        # 创建工具栏（若未创建）
        if not hasattr(self.main_window, 'toolbar'):
            self.main_window.toolbar = self.main_window.addToolBar("主工具栏")
