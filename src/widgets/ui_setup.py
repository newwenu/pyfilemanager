from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSplitter, QHBoxLayout,
                               QLineEdit, QPushButton, QCheckBox, QTreeWidget, QHeaderView,
                               QAbstractItemView, QStatusBar,QStackedWidget,QPushButton,QGraphicsBlurEffect) 

from PySide6.QtGui import QFont,QColor ,QPalette # ：导入QFont用于字体设置
from PySide6.QtCore import Qt, QSize
from utils.file_utils import create_char_icon
from widgets.navigation_tree import init_navigation_tree
from widgets.focus_style_filter import install_focus_style_filter  # 导入
from widgets.rounded_button import AntiAliasRoundedButton  # ：导入自定义按钮类

from widgets.custom_tree_widget import FileListWidget
def setup_ui(main_window, config_manager):
    """主窗口 UI 初始化入口函数"""
    config = config_manager.config
    translation = main_window.translation
    setup_window(main_window, config, translation)
    setup_main_layout(main_window)
    setup_top_widget(main_window, config, translation)
    setup_status_bar(main_window, translation)
    setup_splitter(main_window, config, translation)  # 新增：传递 translation 参数
    main_window.file_list.header().setSectionsClickable(True) # 设置表头可点击
    # 设置选择模式为多选（关键修改）
    main_window.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

def setup_window(main_window, config, translation: dict):
    """设置窗口基础属性"""
    # main_window.setWindowTitle("极简文件管理器")
    main_window.setWindowTitle(translation.get("window_title", "极简文件管理器"))  # 从翻译文件获取标题
    init_width, init_height = config.get("initial_size", [800, 600])
    main_window.setGeometry(200, 100, init_width, init_height)
    main_window.setWindowIcon(create_char_icon('📂'))

def setup_main_layout(main_window):
    """设置主容器布局"""
    main_widget = QWidget()
    main_window.setCentralWidget(main_widget)
    main_window.main_layout = QVBoxLayout(main_widget)
    main_window.bg_label = QLabel(main_window.centralWidget())
    main_window.bg_label.setScaledContents(True)
    main_window.bg_label.lower()

    # 调用独立方法初始化设置按钮
    # setup_settings_button(main_window)

def setup_top_widget(main_window, config, translation: dict):
    """设置顶部功能区（修改：确保按钮属性正确绑定）"""
    top_widget = QWidget()
    top_widget.setFixedHeight(30)
    r, g, b, _ = main_window.sys_bg.getRgb()
    top_widget.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, 108);")  # 半透明背景
    top_layout = QHBoxLayout(top_widget)
    top_layout.setContentsMargins(1, 1, 1, 1)
    top_layout.setSpacing(9)
    
    control_height = 30  # 控制按钮高度
    main_window.address_bar = QLineEdit()
    # 地址栏提示（翻译缺失时显示"输入路径..."）
    main_window.address_bar.setPlaceholderText(translation.get("address_bar_placeholder", "输入路径..."))
    
    # 显式初始化 btn_new_folder 并绑定到 main_window
    main_window.btn_new_folder = QPushButton(translation.get("new_folder", "新建文件夹"))
    main_window.btn_new_folder.setFixedHeight(control_height)  # 按钮高度
    
    # 显示隐藏文件复选框（翻译缺失时显示"显示隐藏文件"）
    main_window.cb_hidden = QCheckBox(translation.get("cb_hidden", "显示隐藏文件"))
    main_window.cb_hidden.setFixedHeight(control_height)  # 复选框高度

    # 显示所有大小复选框（翻译缺失时显示"显示所有大小"）
    main_window.cb_show_sizes = QCheckBox(translation.get("cb_show_sizes", "显示所有大小"))
    main_window.cb_show_sizes.setFixedHeight(control_height)  # 复选框高度

    main_window.address_bar.setFixedHeight(control_height)  # 地址栏高度
    main_window.address_bar.installEventFilter(main_window.keyboard_handler)  # 让 KeyboardHandler 监听地址栏事件

    main_window.main_layout.addWidget(top_widget, stretch=-10)
    top_layout.addWidget(main_window.address_bar)
    top_layout.addWidget(main_window.cb_show_sizes)
    top_layout.addWidget(main_window.cb_hidden)
    # top_layout.addWidget(main_window.btn_new_folder)  # 确保按钮添加到布局
    top_layout.setContentsMargins(1, 1, 1, 1)  # 设置边距

def setup_splitter(main_window, config, translation: dict):
    """设置左右分栏布局（完整实现）"""
    font_size = config.get("font_size", 12)
    splitter = QSplitter(Qt.Orientation.Horizontal)

    # 读取配置文件中的透明度值（默认值为 128）
    bg_alpha1 = config.get("nav_tree_bg_alpha", 128)
    bg_alpha2 = config.get("file_list_bg_alpha", 128)
    # ：从配置中读取独立图标大小参数（默认值保持原逻辑）
    nav_tree_icon_size = config.get("nav_tree_icon_size", font_size * 2.5)
    file_list_icon_size = config.get("file_list_icon_size", font_size * 1.6)
    file_font = QFont()
    file_font.setPointSize(font_size)  # 从配置中获取字体大小
    
    # 左侧导航树
    main_window.nav_tree = QTreeWidget()
    main_window.nav_tree.setObjectName("nav_tree")
    # 关键修改：使用翻译设置导航树标题
    main_window.nav_tree.setHeaderLabel(translation.get("nav_tree_header", "分区"))  # 新增翻译
    
    # 修改：使用独立配置的图标大小
    main_window.nav_tree.setIconSize(QSize(nav_tree_icon_size, nav_tree_icon_size))  # 调大图标尺寸
    main_window.nav_tree.setFont(file_font)
    r,b,g,_ = main_window.sys_bg.getRgb()
    # 保存导航树的初始样式（）
    nav_initial_style = f"""
        QTreeWidget {{
            background-color: rgba({r}, {g}, {b}, {bg_alpha1});  
        }}
        QTreeWidget::item {{ 
            height: {nav_tree_icon_size}px;
            padding-left: 1px;
        }}
    """
    main_window.nav_tree.setStyleSheet(nav_initial_style)  # 应用初始样式
    splitter.addWidget(main_window.nav_tree)
# 右侧内容容器（使用QStackedWidget管理切换）
    right_stack = QStackedWidget()
    splitter.addWidget(right_stack)
    # 右侧文件列表（半透明背景）
    # 主文件列表初始化（关键修改）
    main_window.file_list = FileListWidget()  # 自定义的文件列表控件
    # main_window.file_list.setHeaderLabels(["名称", "大小"])  
    # 关键修改：使用翻译设置文件列表表头
    main_window.file_list.setHeaderLabels([
        translation.get("name", "名称"),  # 新增翻译
        translation.get("size", "大小")   # 新增翻译
    ])
    main_window.file_list.setObjectName("file_list")  # 添加对象名称标识
    # main_window.file_list.setHeaderLabels(["名称", "大小"])
    # main_window.file_list.setColumnHidden(2, True)  # 隐藏“修改时间”列
    header = main_window.file_list.header()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)

    # 修改：使用独立配置的图标大小
    main_window.file_list.setIconSize(QSize(file_list_icon_size, file_list_icon_size))
    # ：使用QFont设置字体大小（替代原样式表中的font-size）
    file_font = QFont('等线')
    file_font.setPointSize(config.get("file_list_font_size", 12))  # 从配置中获取字体大小
    main_window.file_list.setFont(file_font)
    # 样式表中移除原font-size: 12pt; 改为通过QFont控制
    # main_window.file_list.setStyleSheet(f"""
    #     QTreeWidget {{
    #         background-color: rgba(0,0,0, {bg_alpha2});
    #     }}
    #     QTreeWidget::item {{ 
    #         height: {file_list_icon_size}px;
    #         margin: 1px 0;
    #         padding: 0 2px;
    #     }}
    # """)
    # 保存文件列表的初始样式（关键修改）
    initial_style = f"""
        QTreeWidget {{
            background-color: rgba({r}, {g}, {b}, {bg_alpha2});
        }}
        QTreeWidget::item {{ 
            height: {file_list_icon_size}px;
            margin: 1px 0;
            padding: 0 2px;
        }}
    """
    main_window.file_list.setStyleSheet(initial_style)  # 应用初始样式
    # 启用平滑滚动
    main_window.file_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    # 设置快速滚动加速
    main_window.file_list.verticalScrollBar().setSingleStep(20)
    main_window.file_list.verticalScrollBar().setPageStep(400)
    right_stack.addWidget(main_window.file_list)  # 添加到栈式窗口
    splitter.addWidget(right_stack)
    # ：独立驱动器列表（默认隐藏）
    main_window.drive_list = QTreeWidget()
    main_window.drive_list.setObjectName("drive_list")
    # 关键修改：使用翻译设置驱动器列表表头
    main_window.drive_list.setHeaderLabels([
        translation.get("drive_list_name", "名称"),    # 新增翻译
        translation.get("drive_list_usage", "空间使用情况")  # 新增翻译
    ])
    
    # 继承file_list样式（可根据需求单独配置）
    main_window.drive_list.setFont(file_font)
    main_window.drive_list.setStyleSheet(main_window.file_list.styleSheet())  # 复用样式
    right_stack.addWidget(main_window.drive_list)  # 添加到栈式窗口

    # 保存栈式窗口引用以便切换
    main_window.right_stack = right_stack

    main_window.main_layout.addWidget(splitter)
    splitter.setSizes([int(main_window.width() * 0.35), int(main_window.width() * 0.65)])
    # # 初始化导航树（传递导航树实例和主窗口的图标集合）
    # init_navigation_tree(main_window.nav_tree, main_window.drive_icons)  # 传递图标参数
    
    # 触发首次文件列表更新（使用主窗口已初始化的 file_list_updater）
    # main_window.update_filelist()  # 关键修改：调用主窗口的更新方法

    # 初始化导航树（传递图标集合和翻译）
    init_navigation_tree(
        main_window.nav_tree,
        main_window.drive_icons,
        translation=translation  # 传递翻译字典
    )
    # 安装文件列表焦点过滤器（调用统一函数）
    install_focus_style_filter(main_window.file_list, initial_style,main_window.sys_bg)

    # 安装导航树焦点过滤器（调用统一函数）
    install_focus_style_filter(main_window.nav_tree, nav_initial_style,main_window.sys_bg)
    # ：启用触摸事件接收（适配触摸设备）
    # main_window.file_list.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
def setup_status_bar(main_window, translation: dict):  # 新增 translation 参数
    """设置状态栏（修改：使用翻译文本）"""
    main_window.status_bar = QStatusBar()
    main_window.setStatusBar(main_window.status_bar)
    main_window.status_bar.showMessage(translation.get("status_ready", "就绪提示"))  # 就绪提示

    # ：创建工具栏（若未创建）
    if not hasattr(main_window, 'toolbar'):
        main_window.toolbar = main_window.addToolBar("主工具栏")
def setup_settings_button(main_window):
    """独立方法：初始化设置按钮（齿轮图标）及其交互逻辑"""
    # 使用自定义抗锯齿按钮类
    main_window.settings_btn = AntiAliasRoundedButton(main_window)
    main_window.settings_btn.setText("⚙")  # 齿轮图标
    main_window.settings_btn.setFixedSize(48, 48)  # 固定尺寸
    main_window.settings_btn.setCursor(Qt.PointingHandCursor)  # 手型光标
    
    # 设置字体和文字颜色
    btn_font = QFont()
    btn_font.setPointSize(24)
    main_window.settings_btn.setFont(btn_font)
    
    palette = main_window.settings_btn.palette()
    text_color = QColor(255, 255, 255, 220)
    palette.setColor(QPalette.ButtonText, text_color)
    main_window.settings_btn.setPalette(palette)

    # 设置模糊效果（增强质感）
    blur_effect = QGraphicsBlurEffect()
    blur_effect.setBlurRadius(8)
    blur_effect.setBlurHints(QGraphicsBlurEffect.QualityHint)
    main_window.settings_btn.setGraphicsEffect(blur_effect)

    # 初始位置（后续通过resizeEvent调整）
    main_window.settings_btn.move(main_window.width() - 60, main_window.height() - 60)
    main_window.settings_btn.raise_()  # 确保显示在最上层

    # 拖动功能实现
    def mouse_press(event):
        if event.button() == Qt.LeftButton:
            main_window.settings_btn.drag_offset = event.globalPos() - main_window.settings_btn.pos()
            main_window.settings_btn.setCursor(Qt.ClosedHandCursor)

    def mouse_move(event):
        if hasattr(main_window.settings_btn, 'drag_offset'):
            new_pos = event.globalPos() - main_window.settings_btn.drag_offset
            window_rect = main_window.rect()
            btn_rect = main_window.settings_btn.rect()
            new_x = max(0, min(new_pos.x(), window_rect.width() - btn_rect.width()))
            new_y = max(0, min(new_pos.y(), window_rect.height() - btn_rect.height()))
            main_window.settings_btn.move(new_x, new_y)

    def mouse_release(event):
        if hasattr(main_window.settings_btn, 'drag_offset'):
            del main_window.settings_btn.drag_offset
            main_window.settings_btn.setCursor(Qt.PointingHandCursor)