import sys
import os
import zlib
import hashlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
                             QGroupBox, QGridLayout, QScrollArea, QSizePolicy, QDialog, QDialogButtonBox,
                             QFormLayout, QSpinBox, QCheckBox, QProgressBar, QSplitter, QToolBar, QAction,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QToolButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QIcon, QTextCursor, QTextCharFormat
import struct
import re

class MemoryMapWidget(QWidget):
    """内存映射可视化控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.boot_start = 0x8000000
        self.boot_size = 0x100000
        self.app_start = 0x8020000
        self.app_size = 0x20000
        self.boot_used = 0
        self.app_used = 0
        self.setMinimumHeight(150)
        
    def set_memory_info(self, boot_start, boot_size, app_start, app_size, boot_used, app_used):
        self.boot_start = boot_start
        self.boot_size = boot_size
        self.app_start = app_start
        self.app_size = app_size
        self.boot_used = boot_used
        self.app_used = app_used
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 计算可用空间
        width = self.width() - 20
        height = self.height() - 40
        
        # 计算总内存范围
        total_start = min(self.boot_start, self.app_start)
        total_end = max(self.boot_start + self.boot_size, self.app_start + self.app_size)
        total_size = total_end - total_start
        
        # 计算相对位置
        boot_start_rel = (self.boot_start - total_start) / total_size
        boot_size_rel = self.boot_size / total_size
        app_start_rel = (self.app_start - total_start) / total_size
        app_size_rel = self.app_size / total_size
        
        # 绘制整个内存区域
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(10, 10, width, height)
        
        # 绘制BOOT区域
        boot_x = int(10 + boot_start_rel * width)
        boot_width = int(boot_size_rel * width)
        boot_used_rel = min(self.boot_used / self.boot_size, 1.0)
        boot_used_width = int(boot_width * boot_used_rel)
        
        painter.fillRect(QRect(boot_x, 10, boot_width, height), QColor(200, 200, 255))
        painter.fillRect(QRect(boot_x, 10, boot_used_width, height), QColor(100, 100, 255))
        painter.drawRect(QRect(boot_x, 10, boot_width, height))
        
        # 绘制APP区域
        app_x = int(10 + app_start_rel * width)
        app_width = int(app_size_rel * width)
        app_used_rel = min(self.app_used / self.app_size, 1.0)
        app_used_width = int(app_width * app_used_rel)
        
        painter.fillRect(QRect(app_x, 10, app_width, height), QColor(255, 200, 200))
        painter.fillRect(QRect(app_x, 10, app_used_width, height), QColor(255, 100, 100))
        painter.drawRect(QRect(app_x, 10, app_width, height))
        
        # 添加标签
        painter.drawText(QRect(boot_x, height + 20, boot_width, 20), Qt.AlignCenter, f"BOOT: {self.boot_used}/{self.boot_size} bytes")
        painter.drawText(QRect(app_x, height + 20, app_width, 20), Qt.AlignCenter, f"APP: {self.app_used}/{self.app_size} bytes")
        
        # 添加地址标签
        painter.drawText(QRect(10, 10, 100, 20), Qt.AlignLeft, f"0x{total_start:08X}")
        painter.drawText(QRect(width - 80, 10, 100, 20), Qt.AlignRight, f"0x{total_end:08X}")

class FileLoaderThread(QThread):
    """文件加载线程，避免界面卡顿"""
    finished = pyqtSignal(str, bytes, str, int, int)  # 文件类型, 数据, 错误信息, 起始地址, 大小
    progress = pyqtSignal(int)  # 进度更新
    
    def __init__(self, file_path, file_type, start_addr, size):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self.start_addr = start_addr
        self.size = size
        
    def run(self):
        try:
            file_size = os.path.getsize(self.file_path)
            chunk_size = 1024 * 1024  # 1MB
            data = bytearray()
            
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    data.extend(chunk)
                    progress = len(data) / file_size * 100
                    self.progress.emit(int(progress))
            
            self.finished.emit(self.file_type, bytes(data), "", self.start_addr, self.size)
        except Exception as e:
            self.finished.emit(self.file_type, None, str(e), self.start_addr, self.size)

class HexViewer(QTextEdit):
    """十六进制查看器"""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.data = None
        self.base_address = 0
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor(255, 255, 0))  # 黄色高亮
        
    def setData(self, data, base_address=0):
        """显示二进制数据"""
        self.data = data
        self.base_address = base_address
        if data is None:
            self.clear()
            return
            
        hex_str = self.format_hex(data, base_address)
        self.setPlainText(hex_str)
        
    def format_hex(self, data, base_address):
        """将二进制数据格式化为十六进制字符串"""
        hex_str = ""
        for i in range(0, len(data), 16):
            line = data[i:i+16]
            hex_line = ' '.join(f'{b:02x}' for b in line)
            ascii_line = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line)
            addr = base_address + i
            hex_str += f"{addr:08x}: {hex_line:<48} {ascii_line}\n"
        return hex_str
    
    def search_address(self, address):
        """搜索并定位到指定地址"""
        if self.data is None:
            return False
            
        # 转换为文件内的偏移
        offset = address - self.base_address
        
        # 确保地址在有效范围内
        if offset < 0 or offset >= len(self.data):
            return False
            
        # 计算行号和列号
        line = offset // 16
        column = (offset % 16) * 3 + 10  # 地址部分占10字符，每个字节占3字符(2十六进制+1空格)
        
        # 移动到指定位置
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line):
            cursor.movePosition(QTextCursor.Down)
        
        # 高亮显示
        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, column)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 2)  # 选择2个字符(一个字节)
        
        self.setTextCursor(cursor)
        self.setFocus()
        
        return True

class AddressDialog(QDialog):
    """地址输入对话框"""
    def __init__(self, file_type, parent=None):
        super().__init__(parent)
        self.file_type = file_type
        self.setWindowTitle(f"设置{file_type}地址")
        self.setModal(True)
        self.initUI()
        
    def initUI(self):
        layout = QFormLayout(self)
        
        self.start_addr = QLineEdit("0x8000000" if self.file_type == "BOOT" else "0x8020000")
        self.size = QLineEdit("0x100000" if self.file_type == "BOOT" else "0x20000")
        
        layout.addRow("起始地址:", self.start_addr)
        layout.addRow("大小:", self.size)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_settings(self):
        try:
            start_addr = int(self.start_addr.text(), 16)
            size = int(self.size.text(), 16)
            return start_addr, size
        except ValueError:
            return None

class VectorTableDialog(QDialog):
    """中断向量表对话框"""
    def __init__(self, vector_table, parent=None):
        super().__init__(parent)
        self.setWindowTitle("中断向量表")
        self.setModal(True)
        self.resize(500, 400)
        self.initUI(vector_table)
        
    def initUI(self, vector_table):
        layout = QVBoxLayout(self)
        
        # 创建表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["偏移", "地址"])
        table.setRowCount(len(vector_table))
        
        # 填充表格
        for i, addr in enumerate(vector_table):
            table.setItem(i, 0, QTableWidgetItem(f"0x{i*4:03X}"))
            table.setItem(i, 1, QTableWidgetItem(f"0x{addr:08X}"))
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, self)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class BinMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.boot_start = 0x8000000
        self.boot_size = 0x100000
        self.app_start = 0x8020000
        self.app_size = 0x20000
        self.boot_data = None
        self.app_data = None
        self.merged_data = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('BIN文件合并工具-换电柜柜控板-V1.0（张江江）')
        self.setGeometry(100, 100, 1200, 900)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 设置动作
        settings_action = QAction("内存设置", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QGridLayout()
        
        # BOOT 文件选择
        self.boot_label = QLabel("BOOT BIN 文件:")
        self.boot_path = QLineEdit()
        self.boot_browse = QPushButton("浏览")
        self.boot_browse.clicked.connect(lambda: self.select_file("boot"))
        
        # BOOT 地址信息
        self.boot_addr_label = QLabel("地址:")
        self.boot_addr_value = QLabel("未设置")
        
        # BOOT 校验和信息
        self.boot_checksum_label = QLabel("校验和:")
        self.boot_checksum_value = QLabel("未计算")
        
        # APP 文件选择
        self.app_label = QLabel("APP1 BIN 文件:")
        self.app_path = QLineEdit()
        self.app_browse = QPushButton("浏览")
        self.app_browse.clicked.connect(lambda: self.select_file("app"))
        
        # APP 地址信息
        self.app_addr_label = QLabel("地址:")
        self.app_addr_value = QLabel("未设置")
        
        # APP 校验和信息
        self.app_checksum_label = QLabel("校验和:")
        self.app_checksum_value = QLabel("未计算")
        
        file_layout.addWidget(self.boot_label, 0, 0)
        file_layout.addWidget(self.boot_path, 0, 1)
        file_layout.addWidget(self.boot_browse, 0, 2)
        file_layout.addWidget(self.boot_addr_label, 1, 0)
        file_layout.addWidget(self.boot_addr_value, 1, 1, 1, 2)
        file_layout.addWidget(self.boot_checksum_label, 2, 0)
        file_layout.addWidget(self.boot_checksum_value, 2, 1, 1, 2)
        
        file_layout.addWidget(self.app_label, 3, 0)
        file_layout.addWidget(self.app_path, 3, 1)
        file_layout.addWidget(self.app_browse, 3, 2)
        file_layout.addWidget(self.app_addr_label, 4, 0)
        file_layout.addWidget(self.app_addr_value, 4, 1, 1, 2)
        file_layout.addWidget(self.app_checksum_label, 5, 0)
        file_layout.addWidget(self.app_checksum_value, 5, 1, 1, 2)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 内存映射显示
        self.memory_map = MemoryMapWidget()
        main_layout.addWidget(self.memory_map)
        
        # 更新内存映射显示
        self.update_memory_map()
        
        # 内容显示区域 - 使用选项卡
        content_group = QGroupBox("文件内容预览")
        content_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        # BOOT 内容显示
        boot_tab = QWidget()
        boot_layout = QVBoxLayout(boot_tab)
        
        # BOOT 搜索区域
        boot_search_layout = QHBoxLayout()
        self.boot_search_label = QLabel("搜索地址:")
        self.boot_search_input = QLineEdit()
        self.boot_search_input.setPlaceholderText("十六进制地址，如: 0x8000100")
        self.boot_search_btn = QPushButton("搜索")
        self.boot_search_btn.clicked.connect(lambda: self.search_address("boot"))
        
        boot_search_layout.addWidget(self.boot_search_label)
        boot_search_layout.addWidget(self.boot_search_input)
        boot_search_layout.addWidget(self.boot_search_btn)
        
        self.boot_content = HexViewer()
        
        boot_layout.addLayout(boot_search_layout)
        boot_layout.addWidget(self.boot_content)
        
        # APP 内容显示
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)
        
        # APP 搜索区域
        app_search_layout = QHBoxLayout()
        self.app_search_label = QLabel("搜索地址:")
        self.app_search_input = QLineEdit()
        self.app_search_input.setPlaceholderText("十六进制地址，如: 0x8020100")
        self.app_search_btn = QPushButton("搜索")
        self.app_search_btn.clicked.connect(lambda: self.search_address("app"))
        
        # APP 向量表按钮
        self.app_vector_btn = QPushButton("查看中断向量表")
        self.app_vector_btn.clicked.connect(self.show_app_vector_table)
        
        app_search_layout.addWidget(self.app_search_label)
        app_search_layout.addWidget(self.app_search_input)
        app_search_layout.addWidget(self.app_search_btn)
        app_search_layout.addWidget(self.app_vector_btn)
        
        self.app_content = HexViewer()
        
        app_layout.addLayout(app_search_layout)
        app_layout.addWidget(self.app_content)
        
        # 合并后内容显示
        merged_tab = QWidget()
        merged_layout = QVBoxLayout(merged_tab)
        
        # 合并后搜索区域
        merged_search_layout = QHBoxLayout()
        self.merged_search_label = QLabel("搜索地址:")
        self.merged_search_input = QLineEdit()
        self.merged_search_input.setPlaceholderText("十六进制地址，如: 0x8000100")
        self.merged_search_btn = QPushButton("搜索")
        self.merged_search_btn.clicked.connect(lambda: self.search_address("merged"))
        
        merged_search_layout.addWidget(self.merged_search_label)
        merged_search_layout.addWidget(self.merged_search_input)
        merged_search_layout.addWidget(self.merged_search_btn)
        
        self.merged_content = HexViewer()
        
        merged_layout.addLayout(merged_search_layout)
        merged_layout.addWidget(self.merged_content)
        
        self.tab_widget.addTab(boot_tab, "BOOT 内容")
        self.tab_widget.addTab(app_tab, "APP1 内容")
        self.tab_widget.addTab(merged_tab, "合并后内容")
        
        content_layout.addWidget(self.tab_widget)
        content_group.setLayout(content_layout)
        main_layout.addWidget(content_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.merge_btn = QPushButton("合并文件")
        self.merge_btn.clicked.connect(self.merge_files)
        self.merge_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        
        self.save_btn = QPushButton("另存为")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        
        button_layout.addWidget(self.merge_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 加载线程
        self.boot_loader = None
        self.app_loader = None
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = AddressDialog("SETTINGS", self)
        dialog.start_addr.setText(f"0x{self.boot_start:08X}")
        dialog.size.setText(f"0x{self.boot_size:08X}")
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            if settings:
                self.boot_start, self.boot_size = settings
                self.update_memory_map()
                self.statusBar().showMessage('内存设置已更新')
                
    def update_memory_map(self):
        """更新内存映射显示"""
        boot_used = len(self.boot_data) if self.boot_data else 0
        app_used = len(self.app_data) if self.app_data else 0
        self.memory_map.set_memory_info(
            self.boot_start, self.boot_size,
            self.app_start, self.app_size,
            boot_used, app_used
        )
        
    def select_file(self, file_type):
        """选择文件并设置地址"""
        file_path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type.upper()} BIN文件", "", "BIN Files (*.bin)")
        if file_path:
            # 显示地址设置对话框
            dialog = AddressDialog(file_type.upper(), self)
            if file_type == "boot":
                dialog.start_addr.setText(f"0x{self.boot_start:08X}")
                dialog.size.setText(f"0x{self.boot_size:08X}")
            else:
                dialog.start_addr.setText(f"0x{self.app_start:08X}")
                dialog.size.setText(f"0x{self.app_size:08X}")
                
            if dialog.exec_() == QDialog.Accepted:
                settings = dialog.get_settings()
                if settings:
                    start_addr, size = settings
                    
                    if file_type == "boot":
                        self.boot_path.setText(file_path)
                        self.boot_start = start_addr
                        self.boot_size = size
                        self.boot_addr_value.setText(f"0x{start_addr:08X} (大小: 0x{size:08X})")
                        self.statusBar().showMessage('正在加载BOOT文件...')
                        self.progress_bar.setVisible(True)
                        
                        # 使用线程加载文件
                        self.boot_loader = FileLoaderThread(file_path, "boot", start_addr, size)
                        self.boot_loader.finished.connect(self.on_file_loaded)
                        self.boot_loader.progress.connect(self.progress_bar.setValue)
                        self.boot_loader.start()
                    else:
                        self.app_path.setText(file_path)
                        self.app_start = start_addr
                        self.app_size = size
                        self.app_addr_value.setText(f"0x{start_addr:08X} (大小: 0x{size:08X})")
                        self.statusBar().showMessage('正在加载APP1文件...')
                        self.progress_bar.setVisible(True)
                        
                        # 使用线程加载文件
                        self.app_loader = FileLoaderThread(file_path, "app", start_addr, size)
                        self.app_loader.finished.connect(self.on_file_loaded)
                        self.app_loader.progress.connect(self.progress_bar.setValue)
                        self.app_loader.start()
            
    def on_file_loaded(self, file_type, data, error, start_addr, size):
        """文件加载完成回调"""
        self.progress_bar.setVisible(False)
        
        if error:
            QMessageBox.critical(self, "错误", f"加载{file_type.upper()}文件失败: {error}")
            self.statusBar().showMessage('文件加载失败')
            return
            
        if file_type == "boot":
            self.boot_data = data
            self.boot_content.setData(data, start_addr)
            
            # 计算并显示校验和
            crc32 = zlib.crc32(data) & 0xFFFFFFFF
            md5 = hashlib.md5(data).hexdigest()
            self.boot_checksum_value.setText(f"CRC32: 0x{crc32:08X}, MD5: {md5}")
            
            # 验证地址范围
            if len(data) > size:
                QMessageBox.warning(self, "警告", 
                                   f"BOOT文件大小({len(data)}字节)超过分配的空间({size}字节)")
            
            self.statusBar().showMessage(f'BOOT文件加载成功，大小: {len(data)} 字节')
        else:
            self.app_data = data
            self.app_content.setData(data, start_addr)
            
            # 计算并显示校验和
            crc32 = zlib.crc32(data) & 0xFFFFFFFF
            md5 = hashlib.md5(data).hexdigest()
            self.app_checksum_value.setText(f"CRC32: 0x{crc32:08X}, MD5: {md5}")
            
            # 验证地址范围
            if len(data) > size:
                QMessageBox.warning(self, "警告", 
                                   f"APP1文件大小({len(data)}字节)超过分配的空间({size}字节)")
            
            self.statusBar().showMessage(f'APP1文件加载成功，大小: {len(data)} 字节')
            
        self.update_memory_map()
        self.check_merge_ability()
            
    def check_merge_ability(self):
        """检查是否可以合并文件"""
        if self.boot_data is not None and self.app_data is not None:
            self.merge_btn.setEnabled(True)
            
    def merge_files(self):
        try:
            # 检查文件大小是否超过限制
            if len(self.boot_data) > self.boot_size:
                QMessageBox.warning(self, "警告", 
                                   f"BOOT文件大小({len(self.boot_data)}字节)超过分配的空间({self.boot_size}字节)")
                return
                
            if len(self.app_data) > self.app_size:
                QMessageBox.warning(self, "警告", 
                                   f"APP1文件大小({len(self.app_data)}字节)超过分配的空间({self.app_size}字节)")
                return
            
            # 创建合并后的数据
            # 从BOOT起始地址到APP结束地址
            total_size = (self.app_start - self.boot_start) + self.app_size
            self.merged_data = bytearray(total_size)
            
            # 填充0xFF（模拟擦除后的Flash）
            for i in range(total_size):
                self.merged_data[i] = 0xFF
                
            # 写入BOOT数据
            boot_offset = 0  # BOOT从地址0开始
            self.merged_data[boot_offset:boot_offset + len(self.boot_data)] = self.boot_data
            
            # 写入APP数据
            app_offset = self.app_start - self.boot_start  # 计算APP在合并文件中的偏移
            self.merged_data[app_offset:app_offset + len(self.app_data)] = self.app_data
            
            # 自动填充中断向量表
            self.fix_interrupt_vector_table()
            
            # 显示合并后的内容
            self.merged_content.setData(self.merged_data, self.boot_start)
            self.tab_widget.setCurrentIndex(2)  # 切换到合并后内容选项卡
            
            self.statusBar().showMessage(f'文件合并成功，总大小: {total_size} 字节')
            self.save_btn.setEnabled(True)
            QMessageBox.information(self, "成功", "文件合并完成！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并文件失败: {str(e)}")
            
    def fix_interrupt_vector_table(self):
        """修复APP的中断向量表"""
        if not self.app_data or len(self.app_data) < 512:  # 确保有足够的数据
            return
            
        # 检查是否需要修复向量表
        # 对于STM32，前两个字是初始堆栈指针和复位向量
        # 复位向量应该指向APP区域的复位处理程序
        
        # 读取当前的复位向量
        reset_vector = struct.unpack_from('<I', self.app_data, 4)[0]
        
        # 如果复位向量不在APP区域内，可能需要修复
        if not (self.app_start <= reset_vector < self.app_start + len(self.app_data)):
            # 计算新的复位向量（假设复位处理程序在APP起始地址+1处）
            new_reset_vector = self.app_start + 1
            
            # 更新合并数据中的向量表
            app_offset = self.app_start - self.boot_start
            struct.pack_into('<I', self.merged_data, app_offset + 4, new_reset_vector)
            
            self.statusBar().showMessage(f'已修复中断向量表，复位向量: 0x{new_reset_vector:08X}')
            
    def show_app_vector_table(self):
        """显示APP的中断向量表"""
        if not self.app_data or len(self.app_data) < 512:
            QMessageBox.warning(self, "警告", "APP数据不足或未加载，无法显示中断向量表")
            return
            
        # 提取前16个中断向量（通常足够显示主要的中断）
        vector_table = []
        for i in range(0, min(64, len(self.app_data) // 4)):
            try:
                vector = struct.unpack_from('<I', self.app_data, i * 4)[0]
                vector_table.append(vector)
            except:
                break
                
        dialog = VectorTableDialog(vector_table, self)
        dialog.exec_()
            
    def search_address(self, file_type):
        """搜索指定地址"""
        if file_type == "boot":
            viewer = self.boot_content
            input_field = self.boot_search_input
        elif file_type == "app":
            viewer = self.app_content
            input_field = self.app_search_input
        else:  # merged
            viewer = self.merged_content
            input_field = self.merged_search_input
            
        # 获取输入的地址
        addr_text = input_field.text().strip()
        if not addr_text:
            return
            
        try:
            # 解析地址
            if addr_text.startswith("0x"):
                address = int(addr_text, 16)
            else:
                address = int(addr_text)
                
            # 在查看器中搜索
            if viewer.search_address(address):
                self.statusBar().showMessage(f"已定位到地址: 0x{address:08X}")
            else:
                self.statusBar().showMessage(f"地址 0x{address:08X} 超出范围")
                
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的十六进制或十进制地址")
            
    def save_file(self):
        if self.merged_data is None:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "保存合并的BIN文件", "", "BIN Files (*.bin)")
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.merged_data)
                    
                # 计算合并文件的校验和
                crc32 = zlib.crc32(self.merged_data) & 0xFFFFFFFF
                md5 = hashlib.md5(self.merged_data).hexdigest()
                
                self.statusBar().showMessage(f'文件已保存: {file_path} | CRC32: 0x{crc32:08X}, MD5: {md5}')
                QMessageBox.information(self, "成功", f"文件保存成功!\nCRC32: 0x{crc32:08X}\nMD5: {md5}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BinMergerApp()
    window.show()
    sys.exit(app.exec_())