# 项目结构分析

## 目录树

```
pyfilemanager/
├── main.pyw                              # 入口
├── home/                                 # 主页内容
│   └── nocontent.txt
├── media/                                # 图标和背景图片资源
│   ├── {archive,code,doc,...}.png        # 文件类型图标
│   └── webpic/background*.webp           # 网络背景图缓存
├── logs/                                 # 日志文件
│   ├── app.log / core.log / database.log
│   ├── file_ops.log / handlers.log / image.log
│   ├── threads.log / ui.log
│   └── *.log.YYYY-MM-DD                  # 轮转日志
├── userdata/                             # 用户数据
│   ├── config/
│   │   ├── setting.json                  # 应用配置文件
│   │   ├── default.json                  # 默认配置
│   │   ├── setting_default.json          # 设置默认值
│   │   ├── shortcutslinux.json           # Linux快捷键配置
│   │   ├── shortcutswindows.json         # Windows快捷键配置
│   │   ├── tu.ini                        # 翻译工具配置
│   │   └── url.ini                       # URL配置
│   ├── languages/
│   │   ├── zh_CN.json                    # 中文翻译
│   │   └── en_US.json                    # 英文翻译
│   ├── db/
│   │   ├── file_tree.db                  # 文件树数据库
│   │   ├── folder_size.db                # 文件夹大小缓存
│   │   └── folder_size copy.db           # 备份
│   └── file-icon_type/
│       └── file-icon_type.json           # 文件类型图标映射
├── temp/                                 # 临时测试文件
├── test/                                 # 测试文件
├── .gitignore                            # Git 忽略规则
├── environment.yml                       # Conda 环境配置
├── .vscode/
│   ├── .gitignore
│   └── settings.json
├── {readme, README.md, README-en.md}     # 说明文档
├── 使用说明书.md / User_Manual.md         # 用户手册
├── LICENSE                               # 许可证
└── src/                                  # 源代码
    ├── __init__.py                       # 空
    ├── main_window2.py                   # FileManager 主窗口
    ├── pyproject.toml                    # 项目配置
    ├── requirements.txt                  # 依赖清单
    │
    ├── core/                             # 核心模块
    │   ├── __init__.py                   # 导出所有核心类
    │   ├── event_bus.py                  # EventBus（事件总线）
    │   ├── app_initializer.py            # AppInitializer（分阶段初始化）
    │   ├── service_locator.py            # ServiceLocator（服务定位器）
    │   ├── app_config.py                 # AppConfig（应用配置访问）
    │   ├── config_provider.py            # ConfigProvider（配置提供者）
    │   ├── action_context.py             # ActionContext（动作上下文）
    │   ├── event_decorators.py           # on_event/emit_event/EventMixin
    │   ├── interfaces.py                 # FileManagerInterface Protocol
    │   ├── sort_state_manager.py         # SortStateManager（排序状态）
    │   ├── sort_index_mapper.py          # SortIndexMapper（排序索引）
    │   └── shortcut_actions.py           # 快捷键动作定义
    │
    ├── handlers/                         # 事件处理器
    │   ├── __init__.py                   # 空
    │   ├── event_handlers/               # 主事件处理器
    │   │   ├── __init__.py               # 导出 NavigateHandler/FileOperationHandler/UIHandler
    │   │   ├── navigate_handler.py       # 导航事件
    │   │   ├── file_operation_handler.py # 文件操作事件
    │   │   └── ui_handler.py             # UI 更新事件（新增: 提示控制事件）
    │   ├── keyboard_handler.py           # 键盘事件
    │   ├── search_handler.py             # 搜索功能
    │   ├── file_operation.py             # 文件操作（打开等）
    │   ├── home_handler.py               # 主页导航
    │   ├── help_dialog_handler.py        # 帮助对话框
    │   ├── drag_drop_handler.py          # 拖放处理
    │   ├── m_event_handlers.py           # 鼠标/UI 事件绑定
    │   └── header_sort_handler.py        # 表头排序（重写~343行）
    │
    ├── widgets/                          # UI 组件
    │   ├── __init__.py                   # 导出 TipWidget/TipManager/Manage/快捷函数
    │   ├── ui_setup.py                   # UISetup（UI 布局初始化）
    │   ├── file_list_updater.py          # FileListUpdater（文件列表更新，~523行）
    │   ├── navigation_tree.py            # init_navigation_tree()
    │   ├── drive_list_manager.py         # DriveListManager
    │   ├── context_menu.py               # 右键菜单
    │   ├── properties_dialog.py          # 文件属性对话框
    │   ├── help_dialog.py                # 快捷键帮助对话框
    │   ├── error_manager.py              # 错误提示管理
    │   ├── tip_widget.py                 # TipWidget（重写~197行，支持ID管理）
    │   ├── shortcut_tip.py               # 快捷键提示小控件
    │   ├── collapsible_section.py        # 可折叠区域
    │   ├── focus_style_filter.py         # 焦点样式过滤器
    │   ├── custom_tree_widget.py         # FileListWidget
    │   ├── async_icon_loader.py          # 异步图标加载（仅 set_global_icon_cache 被使用）
    │   ├── settings_dialog_model.py      # 设置对话框兼容层
    │   ├── breadcrumb_bar.py             # BreadcrumbBar（面包屑地址栏，新增）
    │   ├── more_options_button.py        # MoreOptionsButton（三点菜单按钮，新增）
    │   ├── search_box.py                 # SearchBox（搜索框组件，新增）
    │   ├── theme_aware_widget.py         # 主题感知组件支持（新增）
    │   └── settings/                     # 设置对话框
    │       ├── __init__.py
    │       ├── base_dialog.py            # BaseSettingsDialog
    │       ├── settings_dialog.py        # SettingsDialog
    │       ├── settings_manager.py       # SettingsDialogManager
    │       ├── value_slider.py           # ValueSlider（数值滑块，新增）
    │       └── tabs/
    │           ├── __init__.py
    │           ├── general_tab.py        # GeneralTab
    │           ├── appearance_tab.py     # AppearanceTab
    │           ├── icon_manager_tab.py   # IconManagerTab
    │           ├── context_menu_tab.py   # ContextMenuTab
    │           ├── advanced_tab.py       # AdvancedTab
    │           └── scan_exclude_tab.py   # ScanExcludeTab（扫描排除，新增~250行）
    │
    ├── file_operator/                    # 文件操作模块
    │   ├── __init__.py                   # 导出所有接口和实现
    │   ├── interfaces.py                 # IFileOperator/IClipboard 等接口
    │   ├── file_operator.py              # FileOperator 实现
    │   ├── clipboard.py                  # FileClipboard
    │   ├── ui_adapter.py                 # FileOperatorUIAdapter
    │   ├── exceptions.py                 # 异常定义
    │   └── error_messages.py             # 错误消息解析
    │
    ├── image_manager/                    # 图标和图片管理
    │   ├── __init__.py                   # 空
    │   ├── icon_manager.py               # create_icon_set()
    │   ├── icon_settings_manager.py      # IconSettingsManager
    │   ├── background_manager.py         # BackgroundManager
    │   ├── get_pic.py                    # get_webp()
    │   └── ink_icon.py                   # get_shortcut_icon_pixmap()
    │
    ├── utils/                            # 工具模块
    │   ├── __init__.py                   # 空
    │   ├── file_utils.py                 # 文件类型判断/图标生成
    │   ├── size_utils.py                 # 大小格式化
    │   ├── time_utils.py                 # 时间格式化
    │   ├── drive_utils.py                # 驱动器检测
    │   ├── logging_config.py             # 日志配置
    │   ├── keyboard_registry2.py         # 快捷键注册
    │   ├── file_filter.py                # FileFilter（文件过滤逻辑，新增~334行）
    │   └── allocation_size_utils.py      # （未使用）磁盘分配大小
    │
    ├── threads/                          # 线程模块
    │   ├── __init__.py                   # 空
    │   ├── file_list_loader.py           # 文件列表异步加载
    │   ├── folder_size.py                # 文件夹大小计算（含扫描排除支持）
    │   └── webpic_loader.py              # 网络图片加载
    │
    ├── dbload_manager/                   # 数据库加载管理
    │   ├── __init__.py                   # 导出 FileTreeDatabase/FileTreeManager
    │   ├── file_tree_database.py         # FileTreeDatabase
    │   ├── file_tree_manager.py          # FileTreeManager
    │   └── db_tool/
    │       ├── db_tool.py                # （未使用）CLI工具
    │       └── db_tool2.py               # （未使用）CLI工具
    │
    ├── config_manager/
    │   └── config_manager.py             # ConfigManager
    │
    ├── language_manager/
    │   └── language_manager.py           # LanguageManager
    │
    ├── theme_manager/
    │   ├── __init__.py                   # 导出 ThemeManager/ThemePalettes/ThemeStyles
    │   ├── theme_manager.py              # ThemeManager
    │   ├── theme_palettes.py             # ThemePalettes（调色板定义，新增~178行）
    │   └── theme_styles.py               # ThemeStyles（QSS样式表生成，新增~317行）
    │
    ├── tip_manager/                      # 提示管理器模块（新增）
    │   ├── __init__.py                   # 导出 TipManager/tip_manager/TipManagerProxy/快捷函数
    │   ├── manager.py                    # TipManager（核心管理类，~117行）
    │   └── tip_manager_proxy.py          # TipManagerProxy（代理接口，~138行）
    │
    ├── toolbox/                          # 工具箱
    │   └── Everythingsearch/             # Windows Everything搜索集成
    │       ├── Everything.db
    │       ├── everything.exe
    │       └── Everything.ini
    │
    └── widget_manager/
        └── __init__.py                   # 空

```

***

## 已使用文件代码结构

> 标注了每个文件的类/函数及被引用情况

### `main.pyw`

- 函数: `__main__` 块
- 被引用: 入口，无人引用
- 导入: `ConfigManager`, `FileManager`

### `src/core/event_bus.py`

- **`EventBus`** (QObject): 导航/文件/选择/UI/视图/焦点/搜索/配置/主题/语言/应用 事件信号定义
  - 新增信号: `refresh`, `ui_close_all_tips`, `ui_close_tip_by_id`, `search_start`, `search_clear`, `language_changed`, `app_show_settings`, `app_show_help`
  - 方法: `emit_navigate_to()`, `emit_status_message()`, `emit_error()`, `emit_config_changed()`
- **`event_bus`**: 全局单例
- 被引用: `core.__init__`, `app_initializer`, `config_provider`, `event_decorators`, `shortcut_actions`, 多处 handlers, `theme_aware_widget`

### `src/core/app_initializer.py`

- **`InitializationError`** (Exception)
- **`InitPhase`**: 初始化阶段
- **`AppInitializer`**: 5阶段初始化(config→core→ui→modules→events)
  - 方法: `initialize()`, `_init_config()`, `_init_core_services()`, `_init_icon_system()`, `_init_ui()`, `_init_modules()`, `_init_events()`, `_setup_action_context()`, `get_phase_status()`
- 被引用: `main_window2.py` (local import)

### `src/core/service_locator.py`

- **`ServiceLocator`**: 服务注册/获取/工厂/清除
- **`inject()`**: 依赖注入装饰器
- **`get_service()`**: 便捷函数
- **`register_service()`**: 便捷函数
- 被引用: 多处通过 `core.__init__` 导出

### `src/core/app_config.py`

- **`AppConfig`**: 配置属性(theme, path, font, icon, alpha, log)
- **`app_config`**: 全局实例
- 被引用: 多处

### `src/core/config_provider.py`

- **`ConfigProvider`**: 配置加载/获取/设置/观察
- **`config_provider`**: 全局单例
- 被引用: `app_config`, `app_initializer`, 多处

### `src/core/action_context.py`

- **`FileSelection`** (dataclass): 文件选择状态
- **`Clipboard`** (dataclass): 剪贴板状态
- **`ActionContext`**: 动作执行上下文
- **`action_context`**: 全局实例
- 被引用: `app_initializer`, `core.__init__`

### `src/core/event_decorators.py`

- **`on_event()`**: 事件订阅装饰器
- **`emit_event()`**: 事件发布装饰器
- **`emit_after()`**: 执行后发射事件
- **`EventMixin`**: 事件混入类
  - 方法: `subscribe()`, `unsubscribe()`, `emit()`, `disconnect_all()`
- 被引用: `main_window2.py` (EventMixin), `core.__init__`

### `src/core/interfaces.py`

- **`FileManagerInterface`** (Protocol): 主窗口接口
- **`ConfigProviderInterface`** (Protocol): 配置提供者接口
- 被引用: `navigate_handler`, `file_operation_handler`, `ui_handler` 作为类型提示

### `src/core/sort_state_manager.py`

- **`SortState`** (dataclass): 排序状态
- **`SortStateManager`** (QObject): 排序状态管理器
- 被引用: `header_sort_handler`, `file_list_updater._update_filelist_from_thread` (local import)

### `src/core/sort_index_mapper.py`

- **`SortIndexMapper`**: 索引映射排序
- **`sort_file_list()`**: 排序函数
- **`get_sorted_indices()`**: 获取排序索引
- 被引用: `file_list_updater`, `header_sort_handler`

### `src/core/shortcut_actions.py`

- **`ShortcutAction`**: 基类
- **`NavigateUpAction`**, **`NavigateHomeAction`**, **`NavigateRefreshAction`** (导航)
- **`FileOpenAction`**, **`FileCopyAction`**, **`FileCutAction`**, **`FilePasteAction`**, **`FileDeleteAction`**, **`FileNewFolderAction`**, **`FileRenameAction`** (文件操作)
- **`SelectAllAction`** (选择)
- **`ToggleHiddenFilesAction`**, **`ToggleMTimeAction`** (视图)
- **`FocusAddressBarAction`**, **`FocusFileListAction`**, **`FocusNavTreeAction`** (焦点)
- **`ShowSearchAction`** (搜索)
- **`ShowSettingsAction`**, **`ShowHelpAction`**, **`SwitchLanguageAction`** (应用)
- **`ShortcutActionRegistry`**: 注册表，含 `_register_default_actions()`
- **`action_registry`**: 全局实例
- 被引用: 全部导出到 `core.__init__`，但 `action_registry` 本身未被任何代码调用执行

### `src/handlers/event_handlers/navigate_handler.py`

- **`NavigateHandler`**:
  - `on_navigate_to(path)`, `on_navigate_home()`, `navigate_parent_dir()`
- 被引用: `event_handlers.__init__`

### `src/handlers/event_handlers/file_operation_handler.py`

- **`FileOperationHandler`**:
  - `on_open_selected()`, `on_copy_files()`, `on_cut_files()`, `on_paste_files()`, `on_delete_files()`, `on_new_folder()`, `on_rename_file()`
- 被引用: `event_handlers.__init__`

### `src/handlers/event_handlers/ui_handler.py`

- **`UIHandler`**:
  - `on_update_statusbar()`, `on_show_error()`, `on_show_message()`, `on_toggle_hidden()`, `on_toggle_sizes()`, `on_toggle_mtime()`, `on_search_start()`, `on_search_clear()`, `toggle_shortcut_help_dialog()`, `show_settings_dialog()`, `on_close_all_tips()`, `on_close_tip_by_id()`
- 被引用: `event_handlers.__init__`

### `src/handlers/keyboard_handler.py`

- **`KeyboardHandler`** (QObject):
  - `register_shortcut()`, `handle_event()`, `eventFilter()`, `_update_shortcut_tips()`, `_key_combination_to_text()`
- 被引用: `app_initializer`

### `src/handlers/search_handler.py`

- **`SearchHandler`**: `start_search()`, `clear_search()`
- **`AdvancedSearchDialog`** (QDialog): Windows Everything搜索
- **`LinuxAdvancedSearchDialog`** (QDialog): Linux os.walk搜索
- 被引用: `app_initializer`

### `src/handlers/file_operation.py`

- **`FileOperationHandler`**: `open_selected_item()`
- 注意: 与 `event_handlers/file_operation_handler.py` 同名但不同类
- 被引用: `app_initializer`

### `src/handlers/home_handler.py`

- **`HomeHandler`**: `navigate_home()`
- 被引用: `app_initializer`

### `src/handlers/help_dialog_handler.py`

- **`HelpDialogHandler`**: `toggle_dialog()`
- 被引用: `app_initializer`

### `src/handlers/drag_drop_handler.py`

- **`DragDropHandler`** (QObject): 拖放处理
- 被引用: `app_initializer`

### `src/handlers/m_event_handlers.py`

- **`setup_event_bindings()`**: 主事件绑定
- **`on_tree_select()`**, **`handle_new_folder()`**, **`toggle_hidden_files()`**, **`toggle_show_all_sizes()`**, **`on_address_change()`**, **`on_item_double_click()`**, **`show_error()`**: UI事件处理函数
- 被引用: `app_initializer`

### `src/handlers/header_sort_handler.py`

- **`HeaderSortHandler`**: 表头排序(防抖)，已重写~343行
- 被引用: `file_list_updater`

### `src/widgets/ui_setup.py`

- **`UISetup`**: `setup_ui()`, `setup_window()`, `setup_main_layout()`, `setup_top_widget()`, `setup_splitter()`, `setup_status_bar()`
- 被引用: `app_initializer`

### `src/widgets/file_list_updater.py`

- **`FileListUpdater`**: `update_filelist()`, `filter_files()`, `clear_filter()`, `_update_filelist_from_thread()`, `_update_filelist_from_sorted()`, `_create_list_item_from_info()`, `_handle_scan_error()`, `_refresh_sort_after_size_calc()`
  - 新增: 文件夹监控、排序防抖刷新、扫描错误处理
  - 约523行
- 被引用: `app_initializer`

### `src/widgets/navigation_tree.py`

- **`init_navigation_tree()`**: 导航树初始化
- 被引用: `ui_setup`

### `src/widgets/drive_list_manager.py`

- **`DriveListManager`**: `update_drive_list()` (classmethod)
- 被引用: `navigate_handler`, `m_event_handlers`

### `src/widgets/context_menu.py`

- **`show_context_menu()`**: 显示右键菜单
- **`handle_new_folder()`**, **`handle_delete_file()`**, **`handle_open_in_explorer()`**, **`handle_open_current_directory()`**, **`show_error()`**: 菜单操作处理函数
- 被引用: `m_event_handlers`

### `src/widgets/properties_dialog.py`

- **`SizeCalculationThread`** (QThread): 异步大小计算
- **`FilePropertiesDialog`** (QDialog): `show_for_selected_item()` (static), `_setup_ui()`, `_load_file_info()`
- 被引用: `context_menu`

### `src/widgets/help_dialog.py`

- **`qt_keys_to_string()`**: 快捷键转换
- **`ShortcutHelpDialog`** (QDialog)
- 被引用: `help_dialog_handler`

### `src/widgets/error_manager.py`

- **`ErrorLevel`** (Enum): INFO/WARNING/ERROR/CRITICAL
- **`ErrorManager`**: `show()`, `info()`, `warning()`, `error()`, `critical()`
- 全局函数: `init_error_manager()`, `get_error_manager()`, `show_error_tip()`, `info()`, `warning()`, `error()`, `critical()`
- 被引用: `UIHandler`

### `src/widgets/tip_widget.py`

- **`TipWidget`** (QLabel): 重写~197行，支持ID管理、4种样式(success/error/warning/info)、工具提示窗口模式
  - 方法: `show_tip()`, `set_tip_style()`, `close()`, `fade_out()`
- 被引用: `tip_manager.manager`

### `src/widgets/shortcut_tip.py`

- **`ShortcutTipWidget`** (QWidget): 快捷键提示
- 被引用: `keyboard_handler`

### `src/widgets/collapsible_section.py`

- **`CollapsibleSection`** (QWidget): 可折叠区域
- 被引用: `appearance_tab`

### `src/widgets/focus_style_filter.py`

- **`FocusStyleFilter`** (QObject): 焦点样式
- **`install_focus_style_filter()`**: 安装过滤器
- 被引用: `ui_setup`

### `src/widgets/custom_tree_widget.py`

- **`FileListWidget`** (QTreeWidget): 支持空提示
- 被引用: `ui_setup`

### `src/widgets/async_icon_loader.py`

- **`set_global_icon_cache()`**: 设置全局图标缓存
- **`AsyncIconLoader`** (QObject): (未使用)
- **`get_async_icon_loader()`**, **`init_async_icon_loader()`**, **`shutdown_async_icon_loader()`**: (未使用)
- 被引用(仅`set_global_icon_cache()`): `app_initializer`

### `src/widgets/breadcrumb_bar.py` (新增)

- **`BreadcrumbBar`** (QWidget): 面包屑地址栏，支持点击路径段导航和可编辑路径输入
  - 信号: `path_clicked(str)`, `path_edited(str)`
  - 方法: `set_path()`, `start_edit()`, `finish_edit()`, `_setup_ui()`
  - 约309行
- 被引用: `ui_setup`

### `src/widgets/more_options_button.py` (新增)

- **`MoreOptionsButton`** (QPushButton): 三点菜单按钮，包含显示隐藏文件/显示大小/刷新
  - 信号: `toggle_hidden_files(bool)`, `toggle_show_sizes(bool)`, `refresh_requested()`
  - 方法: `_setup_menu()`, `_on_button_clicked()`
  - 约140行
- 被引用: `ui_setup`

### `src/widgets/search_box.py` (新增)

- **`SearchBox`** (QWidget): 动画搜索框组件
  - 信号: `search_text_changed(str)`, `search_confirmed(str)`, `search_closed()`
  - 方法: `show_search()`, `hide_search()`, `_on_text_changed()`, `_on_search_confirmed()`
  - 约167行
- 被引用: `ui_setup`

### `src/widgets/theme_aware_widget.py` (新增)

- **`setup_theme_aware_widget(widget, update_style_callback)`**: 函数式主题感知设置
- **`setup_tree_widget_theme(widget, bg_alpha, icon_size)`**: 树控件主题感知
- **`ThemeAwareWidget`** (QWidget): 主题感知基类（注释中提及）
- 被引用: `ui_setup`

### `src/widgets/settings_dialog_model.py`

- 兼容层，导出 `SettingsDialog`
- 被引用: `settings_manager`

### `src/widgets/settings/base_dialog.py`

- **`BaseSettingsDialog`** (QDialog): 设置基类
- 被引用: `settings_dialog`

### `src/widgets/settings/settings_dialog.py`

- **`SettingsDialog`** (BaseSettingsDialog): 含6个标签页(新增ScanExcludeTab)
- 被引用: `settings_dialog_model`

### `src/widgets/settings/settings_manager.py`

- **`SettingsDialogManager`** (QObject): 单例管理设置对话框
- 被引用: `app_initializer`

### `src/widgets/settings/value_slider.py` (新增)

- **`ValueSlider`** (QWidget): 数值滑块组件，替代QSpinBox
  - 信号: `valueChanged(int)`
  - 支持预设按钮、步长调节、实时数值显示
  - 约208行
- 被引用: `appearance_tab`, `general_tab`

### `src/widgets/settings/tabs/general_tab.py`

- **`GeneralTab`** (QWidget): 常规设置
- 被引用: `settings_dialog`

### `src/widgets/settings/tabs/appearance_tab.py`

- **`AppearanceTab`** (QWidget): 外观设置
- 被引用: `settings_dialog`

### `src/widgets/settings/tabs/icon_manager_tab.py`

- **`IconManagerTab`** (QWidget): 图标管理
- 被引用: `settings_dialog`

### `src/widgets/settings/tabs/context_menu_tab.py`

- **`ContextMenuTab`** (QWidget): 右键菜单设置
- 被引用: `settings_dialog`

### `src/widgets/settings/tabs/advanced_tab.py`

- **`AdvancedTab`** (QWidget): 高级设置
- 被引用: `settings_dialog`

### `src/widgets/settings/tabs/scan_exclude_tab.py` (新增)

- **`ScanExcludeTab`** (QWidget): 扫描排除规则设置标签页
  - 功能: 系统保护文件排除复选框 + 自定义排除路径列表管理
  - 约250行
- 被引用: `settings_dialog`

### `src/file_operator/interfaces.py`

- **`OperationType`** (Enum), **`OperationStatus`** (Enum)
- **`OperationResult`** (dataclass), **`FileInfo`** (dataclass)
- **`IFileOperation`**, **`IClipboard`**, **`IFileOperator`** (ABC)
- 被引用: `file_operator.__init__`, `file_operator`, `clipboard`, `ui_adapter`

### `src/file_operator/file_operator.py`

- **`FileOperator`** (IFileOperator): copy/move/delete/rename/create\_folder/clipboard
- 被引用: `file_operator.__init__`, `app_initializer`

### `src/file_operator/clipboard.py`

- **`ClipboardAction`** (Enum), **`ClipboardContent`** (dataclass)
- **`FileClipboard`** (IClipboard): copy/cut/paste/clear
- 被引用: `file_operator.__init__`, `file_operator`

### `src/file_operator/ui_adapter.py`

- **`FileOperatorUIAdapter`**: create\_folder\_with\_dialog/delete\_with\_confirmation/rename\_with\_dialog/copy\_to\_clipboard/cut\_to\_clipboard/paste\_from\_clipboard
- 被引用: `app_initializer`

### `src/file_operator/exceptions.py`

- **`FileOperatorError`**, **`FileNotFoundError`**, **`PermissionDeniedError`**, **`FileExistsError`**, **`OperationCancelledError`**, **`DiskFullError`**, **`PathTooLongError`**
- 被引用: `file_operator.__init__`, `file_operator`, `clipboard`

### `src/file_operator/error_messages.py`

- **`ErrorMessageResolver`**: 错误解析/成功消息/部分失败
- 全局函数: `set_language()`, `set_language_provider()`, `resolve_exception()`, `success_message()`, `partial_failure_message()`, `init_with_language_manager()`
- 被引用: `file_operator`, `app_initializer`

### `src/image_manager/icon_manager.py`

- **`create_icon_set()`**: 创建图标集
- 被引用: `app_initializer`, `main_window2`

### `src/image_manager/icon_settings_manager.py`

- **`IconSettingsManager`**: 系统图标设置
- **`get_icon_settings_manager()`**: 获取实例
- 被引用: `app_initializer`, `file_list_updater`, `base_dialog.apply_settings()`, `settings_dialog`

### `src/image_manager/background_manager.py`

- **`BackgroundManager`**: 背景图片管理
- 被引用: `app_initializer`

### `src/image_manager/get_pic.py`

- **`get_webp()`**, **`save_image()`**
- 被引用: `webpic_loader`

### `src/image_manager/ink_icon.py`

- **`get_file_icon()`**, **`get_shortcut_icon_pixmap()`**
- 被引用: `file_list_updater`, `async_icon_loader`

### `src/utils/file_utils.py`

- **`get_file_type()`**: O(1)文件类型判断
- **`create_char_icon()`**: 字符图标生成
- **`should_show()`**: 是否显示文件
- **`get_icon_char()`**: 根据类型获取emoji字符
- 被引用: 多处

### `src/utils/size_utils.py`

- **`format_size()`**, **`format_size_auto_precision()`**, **`parse_size()`**, `parse_size_strict()`, `compare_sizes()`, `get_size_unit()`, `convert_size()`, `is_valid_size_string()`
- 被引用: 多处

### `src/utils/time_utils.py`

- **`get_file_mtime()`**, **`format_mtime_timestamp()`**, **`format_mtime_timestamp_full()`**
- 被引用: 多处

### `src/utils/drive_utils.py`

- **`get_system_drives()`**: 跨平台获取驱动器
- **`get_simplified_drive_display()`**: 简化显示
- 被引用: `navigation_tree`, `drive_list_manager`

### `src/utils/logging_config.py`

- **`init_logging()`**: 初始化日志
- **`get_logger()`**: 获取日志器
- **`log_exception()`**: 带堆栈的异常记录
- **`log_performance()`**: 性能日志装饰器
- **`update_log_level()`**, **`get_log_stats()`**
- **`LogContext`**: 日志上下文管理器
- 被引用: 几乎所有模块

### `src/utils/keyboard_registry2.py`

- **`load_user_shortcuts()`**, **`parse_modifiers()`**
- **`default_shortcuts`**: 默认快捷键配置列表
- **`register_app_shortcuts()`**: 注册快捷键
- 被引用: `app_initializer`, `help_dialog_handler`

### `src/utils/file_filter.py` (新增)

- **`FileFilter`**: 统一的文件过滤逻辑
  - 方法: `get_scan_excludes()`, `should_exclude()`, `_get_file_attributes_from_direntry()`, `is_system_protected()`, `_check_custom_exclude()`
  - 支持: 系统保护文件排除/自定义路径排除/隐藏文件处理/跨平台适配
  - 约334行
- 被引用: `folder_size` (folder_size线程中使用)

### `src/threads/file_list_loader.py`

- **`FileListLoaderThread`** (QThread): 异步扫描目录
- **`FileListLoaderManager`** (QObject): 管理扫描线程
  - 信号: `list_loaded`, `error_occurred`
- 被引用: `file_list_updater`

### `src/threads/folder_size.py`

- **`FolderSizeThread`** (QThread): 文件夹大小计算（支持扫描排除）
- **`FolderSizeManager`** (QObject): 管理大小计算线程
  - 方法: `start_calculation()`, `set_max_threads()`, `stop_all_threads()`
  - 使用 `FileFilter` 进行排除过滤
- 被引用: `app_initializer`
- **`FolderSizeTreeThread`** (QThread): (未使用) 树结构大小计算
- **`FolderSizeSmartTreeThread`** (QThread): (未使用) 智能树计算
- **`DatabaseCacheWorker`** (QRunnable): 后台缓存写入

### `src/threads/webpic_loader.py`

- **`WebpLoader`** (QThread): 网络图片加载
- 被引用: `background_manager`

### `src/dbload_manager/file_tree_database.py`

- **`FileNode`** (dataclass): 文件节点
- **`FileTreeDatabase`**: SQLite文件树存储
  - 新增: 文件夹变化检测优化、级联缓存失效
- 被引用: `dbload_manager.__init__`, `file_tree_manager`

### `src/dbload_manager/file_tree_manager.py`

- **`CacheValidity`** (Enum): 缓存有效性
- **`FolderInfo`** (dataclass): 文件夹信息
- **`FileTreeManager`**: 业务逻辑层
  - 新增: 级联缓存失效、文件夹变化检测优化
- 被引用: `dbload_manager.__init__`, `app_initializer`, `file_list_updater`, `folder_size`

### `src/config_manager/config_manager.py`

- **`ConfigManager`**: JSON配置管理
  - 新增: `scan_exclude_system_protected`, `scan_exclude_custom` 配置项支持
- 被引用: `main.pyw`, `file_utils.py`

### `src/language_manager/language_manager.py`

- **`LanguageManager`**: 多语言支持
  - 新增: 扫描排除相关翻译 (zh_CN/en_US)
- 被引用: `app_initializer`

### `src/theme_manager/theme_manager.py`

- **`ThemeManager`** (QObject): 主题管理
  - 方法: `apply_theme()`, `get_actual_theme()`, `toggle_theme()`
- 被引用: `app_initializer`

### `src/theme_manager/theme_palettes.py` (新增)

- **`ThemePalettes`**: 主题调色板定义
  - 类属性: `DARK_COLORS`, `LIGHT_COLORS` (QColor字典)
  - 类方法: `get_colors(theme)`, `create_palette(theme)`
  - 约178行
- 被引用: `theme_styles`

### `src/theme_manager/theme_styles.py` (新增)

- **`ThemeStyles`**: 主题QSS样式表生成
  - 类方法: `get_stylesheet(theme)`, 生成完整QSS字符串
  - 约317行
- 被引用: `theme_manager`

### `src/tip_manager/manager.py` (新增)

- **`TipManager`**: 提示管理器核心类
  - 方法: `show_tip()`, `close_tip_by_id()`, `close_all()`, `_cleanup_tip()`, `_cleanup_destroyed_tips()`
  - 支持: ID去重管理、自动清理已销毁组件
  - 约117行
- **`tip_manager`**: 全局实例
- 被引用: `tip_manager.__init__`, `tip_manager_proxy`

### `src/tip_manager/tip_manager_proxy.py` (新增)

- **`TipManagerProxy`** (QObject): 提示管理器代理，提供类型化接口
  - 方法: `show_success()`, `show_error()`, `show_warning()`, `show_info()`, `show_tip()`, `close_all()`, `close_tip_by_id()`
  - 约138行
- 全局函数: `show_success()`, `show_error()`, `show_warning()`, `show_info()`, `show_tip()`, `close_all_tips()`, `close_tip_by_id()`
- 被引用: `tip_manager.__init__`, `widgets.__init__`, `error_manager`, `ui_adapter`, `settings_manager`, `main_window2`

### `src/main_window2.py`

- **`FileManager`** (QMainWindow, EventMixin): 主窗口
  - 新增事件订阅: `focus_search_box`, `search_start`, `search_clear`, `app_show_settings`, `app_show_help`
  - 新增方法: `_on_focus_address_bar()`, `_on_focus_search_box()`, `_on_search_start()`, `_on_search_clear()`, `show_settings_tip()`
  - 新增: `breadcrumb_bar`, `search_box` 组件支持
  - 新增: `on_settings_changed()` 响应主题/线程数变更
  - 约225行

***

## 未使用代码清单

### 一、完全未使用的文件（6个）

| 文件 | 说明 |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| `src/utils/allocation_size_utils.py` | 磁盘分配大小获取，定义了全套API但从未被项目引用 |
| `src/dbload_manager/db_tool/db_tool.py` | CLI数据库管理工具 |
| `src/dbload_manager/db_tool/db_tool2.py` | CLI数据库管理工具(扩展版) |
| `src/__init__.py` | 空文件 |
| `src/handlers/__init__.py` | 空文件 |
| `src/threads/__init__.py` | 空文件 |

### 二、已使用文件中未使用的类/函数

#### `src/core/shortcut_actions.py`

- **`ToggleHiddenFilesAction`**: `execute()` 为空，未在 `ShortcutActionRegistry._register_default_actions()` 中注册
- **`ShortcutActionRegistry.execute()`**: 从未被调用
- **`SwitchLanguageAction`**: `execute()` 为空
- **`action_registry`**: 全局实例创建后从未被使用

#### `src/core/action_context.py`

- **`FileSelection.get_selected()`**, `get_single_selection()`, `has_selection()`, `clear()`: 从未被外部调用
- **`Clipboard.is_cut()`**, `is_copy()`, `has_files()`, `clear()`, `set_copy()`, `set_cut()`: 从未被外部调用
- `action_context` 全局实例已设置完成但未被任何实际代码读取

#### `src/core/sort_state_manager.py`

- **`SortState.__eq__()`**: 从未实际用于比较
- **`SortStateManager.undo()`**, `can_undo()`, `reset()`: 从未被调用

#### `src/core/sort_index_mapper.py`

- **`get_sorted_indices()`**: 从未被调用

#### `src/core/event_bus.py`

- 以下信号定义后从未被任何代码 emit:
  - `file_open` (Signal(str))
  - `file_properties` (Signal(str))
  - `selection_changed` (Signal(list))
  - `select_none` (Signal())
  - `ui_update_filelist` (Signal())
  - `ui_update_navtree` (Signal())
  - `ui_show_confirm` (Signal(str, str, object))
  - `view_show_drives` (Signal())
  - `view_show_files` (Signal())
  - `focus_search_box` (Signal())
  - `config_reload` (Signal())
  - `app_quit` (Signal())
  - `refresh` (Signal()) — navigate_refresh 的别名，同样未被使用
- **`EventBus.emit_navigate_to()`**, `emit_status_message()`, `emit_error()`, `emit_config_changed()`: 从未被调用

#### `src/core/event_decorators.py`

- **`on_event()`**: 从未被用作装饰器
- **`emit_event()`**: 从未被用作装饰器
- **`emit_after()`**: 从未被用作装饰器

#### `src/widgets/async_icon_loader.py`

- **`AsyncIconLoader`** 完整类: 从未被实例化
- **`get_async_icon_loader()`**: 从未被调用
- **`init_async_icon_loader()`**: 从未被调用
- **`shutdown_async_icon_loader()`**: 从未被调用
- 只有 `set_global_icon_cache()` 被使用

#### `src/widgets/error_manager.py`（全局函数部分）

- `init_error_manager()`, `get_error_manager()`, `show_error_tip()`, `info()`, `warning()`, `error()`, `critical()`: 从未被任何文件导入

#### `src/threads/folder_size.py`

- **`FolderSizeTreeThread`** 完整类: 从未被启动
- **`FolderSizeSmartTreeThread`** 完整类: 从未被启动
- **`FolderSizeManager.start_tree_calculation()`**, `start_smart_tree_calculation()`, `stop_tree_calculation()`, `_cleanup_tree_thread()`: 从未被外部调用

#### `src/utils/file_utils.py`

- 模块级别创建了额外的 `ConfigManager` 实例(`config_manager = ConfigManager(...)`)：该实例仅用于初始化 `EXT_TO_TYPE` 映射，完成后不再需要

#### `src/file_operator/clipboard.py`

- **`ClipboardContent.is_valid()`**: 可能未使用
- 实际上 `FileClipboard.content` 属性从未被外部读取

#### `src/dbload_manager/file_tree_database.py`

- **`FileTreeDatabase.search_by_name()`**: 从未被调用
- **`FileTreeDatabase.get_ancestors()`**: 从未被调用
- **`FileTreeDatabase.get_subtree()`**: 从未被调用
- **`FileTreeDatabase.add_node()`**: 优先使用批量 `add_nodes_batch()`

#### `src/dbload_manager/file_tree_manager.py`

- **`FileTreeManager.calculate_folder_size_smart()`**: 从未被外部调用
- **`FileTreeManager.preload_folder_sizes()`**: 从未被外部调用
- **`FileTreeManager.get_child_folders_info()`**: 从未被外部调用
- **`FileTreeManager.get_folder_tree_stats()`**: 从未被外部调用
- **`FileTreeManager.update_folder_tree_sizes()`**: 从未被外部调用
- **`FileTreeManager.cleanup_stale_cache()`**: 从未被调用
- **`FileTreeManager.cascade_invalidate_cache()`**: 从未被调用
- **`FileTreeManager.get_subtree_size_info()`**: 仅被 `FolderSizeSmartTreeThread`(未使用) 调用
- **`FileTreeManager.update_folder_tree_sizes_smart()`**: 仅被 `FolderSizeSmartTreeThread`(未使用) 调用

#### `src/config_manager/config_manager.py`

- **`ConfigManager.load_translation()`**: 从未被调用（由 `LanguageManager` 使用自己的方式加载翻译）

#### `src/image_manager/background_manager.py`

- **`BackgroundManager._start_webp_loading()`**: 当 `random=True` 时调用，但 `random` 参数传递来自配置 `app_config.start_random`

#### `src/handlers/search_handler.py`

- **`is_admin()`**: 全局函数，仅用于 `AdvancedSearchDialog` 内部
- **`LinuxAdvancedSearchDialog`**: 实际创建但 Linux 上可能会使用

#### `src/widgets/drive_list_manager.py`

- Unix分支代码 (`import shutil`): 项目在 Windows 上运行时此分支从未执行

#### `src/utils/logging_config.py`

- **`get_log_stats()`**: 从未被调用

#### `src/utils/keyboard_registry2.py`

- 模块级代码 `load_user_shortcuts()` 和后续循环会在导入时立即执行（有副作用）

***

## 已清理的旧文件（之前标记为未使用，现已删除）

| 已删除文件 | 删除原因 |
| ---------------------------------------------- | ---------------------------------------------------------------------- |
| `src/widgets/paged_file_list.py` | 被 `FileListWidget` 替代 |
| `src/widgets/simple_virtual_list.py` | 被 `FileListWidget` 替代 |
| `src/widgets/settings/utils/settings_utils.py` | 工具函数从未被导入 |
| `src/utils/cache_manager.py` | `SizeCacheDB` 旧版代码 |
| `src/dbload_manager/database_manager.py` | 被 `FileTreeManager` 替代 |
| `src/dbload_manager/get_pic_ignore.py` | 独立下载脚本，无导入引用 |
