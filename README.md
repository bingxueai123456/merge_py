# Bin Merger - 二进制文件合并工具

一个基于PyQt5的图形化二进制文件合并工具，支持将多个二进制文件合并为一个文件，并提供直观的内存布局可视化。

## 功能特性

- 🖥️ **图形化界面**: 基于PyQt5的现代化GUI界面
- 📁 **文件合并**: 支持多个二进制文件的智能合并
- 🎯 **内存布局可视化**: 直观显示BOOT和APP区域的内存使用情况
- ⚙️ **灵活配置**: 可自定义BOOT和APP区域的大小和起始位置
- 📊 **实时统计**: 显示文件大小、使用率等统计信息
- 🔧 **跨平台**: 支持Windows、macOS、Linux

## 项目结构

```
merger/
├── bin_merger.py          # 主程序文件
├── requirements.txt       # Python依赖包
├── .github/
│   └── workflows/
│       └── build-windows.yml  # GitHub Actions构建配置
└── README.md             # 项目说明文档
```

## 快速开始

### 本地运行

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd merger
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python bin_merger.py
   ```

### 使用说明

1. **选择文件**: 点击"选择文件"按钮选择要合并的二进制文件
2. **配置参数**: 设置BOOT和APP区域的大小和起始位置
3. **预览布局**: 查看内存布局的可视化预览
4. **执行合并**: 点击"合并文件"按钮生成合并后的文件

## 自动构建Windows可执行文件

本项目使用GitHub Actions自动构建Windows可执行文件，无需本地Windows环境。

### 构建流程

1. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "Add bin merger tool"
   git push origin main
   ```

2. **自动构建**
   - GitHub Actions会自动检测代码推送
   - 在Windows环境中安装依赖
   - 使用PyInstaller构建exe文件
   - 生成构建产物供下载

3. **下载构建结果**
   - 进入GitHub仓库的Actions页面
   - 选择最新的构建任务
   - 在Artifacts部分下载`bin_merger-windows.zip`

### 构建配置

构建配置位于`.github/workflows/build-windows.yml`，包含：

- **触发条件**: 推送到main分支或手动触发
- **运行环境**: Windows Latest
- **Python版本**: 3.11
- **依赖安装**: PyQt5, PyInstaller
- **构建命令**: `pyinstaller --onefile --windowed --name bin_merger bin_merger.py`
- **产物上传**: 自动上传exe文件作为构建产物

### 手动触发构建

1. 进入GitHub仓库页面
2. 点击"Actions"标签
3. 选择"Build Windows Executable"工作流
4. 点击"Run workflow"按钮
5. 等待构建完成并下载exe文件

## 技术栈

- **GUI框架**: PyQt5
- **构建工具**: PyInstaller
- **CI/CD**: GitHub Actions
- **目标平台**: Windows (通过GitHub Actions构建)

## 开发说明

### 本地开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 运行程序
python bin_merger.py
```

### 构建本地可执行文件

```bash
# 安装PyInstaller
pip install pyinstaller

# 构建可执行文件
pyinstaller --onefile --windowed --name bin_merger bin_merger.py

# 生成的文件位于 dist/bin_merger.exe (Windows) 或 dist/bin_merger (Linux/macOS)
```

## 贡献指南

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持二进制文件合并
- 图形化界面
- 内存布局可视化
- GitHub Actions自动构建

## 常见问题

### Q: 如何下载Windows可执行文件？
A: 推送代码到GitHub后，在Actions页面找到最新的构建任务，下载Artifacts中的exe文件。

### Q: 构建失败怎么办？
A: 检查GitHub Actions的构建日志，通常是因为依赖问题或代码错误。

### Q: 可以在其他平台构建吗？
A: 当前配置仅支持Windows构建，如需其他平台，可以修改`.github/workflows/build-windows.yml`文件。

### Q: 如何修改构建配置？
A: 编辑`.github/workflows/build-windows.yml`文件，可以修改Python版本、依赖包、构建参数等。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。
