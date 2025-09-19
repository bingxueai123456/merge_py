# GitHub Actions 设置指南

## 问题解决

### 403权限错误解决方案

如果遇到"GitHub release failed with status: 403"错误，有以下解决方案：

#### 方案1：使用简化版本（推荐）

使用 `build-windows-simple.yml` 配置文件，只上传Artifact，不创建Release：

```yaml
# 只上传构建产物，不创建Release
- name: Upload Windows executable
  uses: actions/upload-artifact@v4
  with:
    name: bin_merger-windows
    path: dist/bin_merger.exe
```

#### 方案2：设置仓库权限

1. 进入GitHub仓库设置
2. 点击 "Actions" → "General"
3. 在 "Workflow permissions" 部分：
   - 选择 "Read and write permissions"
   - 勾选 "Allow GitHub Actions to create and approve pull requests"

#### 方案3：使用Personal Access Token

1. 创建Personal Access Token：
   - GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 选择权限：`repo` (完整仓库访问)
   - 生成token并复制

2. 在仓库中添加Secret：
   - 仓库 Settings → Secrets and variables → Actions
   - 添加新secret：`RELEASE_TOKEN`
   - 值：刚才生成的Personal Access Token

3. 修改workflow文件：
   ```yaml
   env:
     GITHUB_TOKEN: ${{ secrets.RELEASE_TOKEN }}
   ```

## 当前配置

项目现在有两个workflow文件：

1. **build-windows.yml** - 完整版本（包含Release创建）
2. **build-windows-simple.yml** - 简化版本（仅上传Artifact）

## 推荐使用

建议使用 `build-windows-simple.yml`，因为：
- 避免权限问题
- 构建产物仍然可以下载
- 更简单可靠

## 下载构建结果

1. 进入GitHub仓库的Actions页面
2. 选择最新的构建任务
3. 在 "Artifacts" 部分下载 `bin_merger-windows.zip`
4. 解压后得到 `bin_merger.exe` 文件
