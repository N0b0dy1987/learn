# Mir 自动脚本 WebUI

简单的 Flask 应用，提供一个网页界面来：

- 建立与 MuMu 模拟器（ADB serial: 127.0.0.1:16384）的连接检测
- 启动 / 停止后台脚本（目前为占位的模拟循环，后续添加识别与操作逻辑）

准备与运行:

1. 安装依赖：

```
pip install -r requirements.txt
```

2. 启动服务：

```
python app.py
```

3. 在浏览器打开 http://127.0.0.1:7860

说明：

- 如果连接失败，页面会弹窗提示错误信息。后续我可以继续实现画面采集、图像识别与寻路/打怪逻辑。

在家里运行（快速入门）
-------------------

下面的步骤适用于你把仓库从 GitHub 克隆到家里的电脑后进行第一次运行（Windows PowerShell）：

1. 克隆仓库并进入目录：

```powershell
git clone https://github.com/N0b0dy1987/learn.git
cd learn
```

2. 创建并激活虚拟环境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. 安装依赖：

```powershell
pip install -r requirements.txt
```

4. 创建本地配置文件 `config.json`（不要把它提交到仓库）

仓库中包含一个 `config.template.json`，你可以复制并修改：

```powershell
Copy-Item config.template.json config.json
notepad config.json
```

示例 `config.json` 内容（Windows 路径示例）：

```json
{
	"adb_path": "C:\\Program Files\\MuMu\\nx_main\\adb.exe"
}
```

将 `adb_path` 修改为你家里 MuMu 或 adb 可执行程序的实际路径。如果你的系统把 `adb` 放在 PATH 中，也可以把 `adb_path` 设为 `null`，后端会尝试使用系统 PATH 中的 adb。

5. 启动 WebUI：

```powershell
python app.py
```

然后在浏览器打开 http://127.0.0.1:7860，页面上可以保存 `adb_path` 配置、建立连接并抓屏调试。

注意事项：
- `config.json` 已加入 `.gitignore`，请不要把本地配置（含绝对路径）提交到远程仓库。使用 `config.template.json` 作为不同机器之间的配置模板。
- 如果你在家里使用不同版本的 MuMu，可能需要在 MuMu 内部启用 ADB 或调整 ADB 端口（常见端口：5555、16384）。
- 如果遇到权限或认证问题（例如 git push/pull），请确认已在本机配置 SSH key 或使用 GitHub 的个人访问令牌 (PAT)。

有疑问我可以继续把常用的开发命令写进 README（比如如何运行单元测试、如何添加新的识别模板等）。
