# DeepSeek API 配置与测试操作清单（拿到 Key 后照着做）

> 用途：拿到真实 API Key 后，完成 Claude Code + DeepSeek 的连接配置、连通性测试与截图打码。
> 红线：**任何截图、记录、报告里都不出现真实密钥**，只保留 `sk-****` 形式。

## 第 0 步 · 获取 API Key
1. 打开 https://platform.deepseek.com ，用手机号注册/登录。
2. 左侧进入 **API Keys**（API 密钥）→ 点 **创建 API Key**。
3. 命名（如 `claude-code`）→ 创建 → **立即复制**（只显示一次）。
4. 密钥格式为 `sk-` 开头的一串字母数字，粘贴前先存到只有你知道的地方。

## 第 1 步 · 配置 CC Switch
1. 打开 CC Switch，在左侧选择 **Claude Code**。
2. 点 **新增服务商 / Add Provider**，选择或输入 **DeepSeek**。
3. 填写配置：
   - **Base URL**：`https://api.deepseek.com/anthropic`（注意是 api.deepseek.com，不是 platform.deepseek.com）
   - **API Key**：粘贴刚复制的真实密钥
   - **模型名 / Model**：`deepseek-flash`（或 `deepseek-v4-pro`）
4. **启用（Enable）** 该配置，确认当前生效的是 DeepSeek。
5. 若 CC Switch 提供"扩展跟随切换"选项，按说明开启，让 VS Code 内的 Claude Code 扩展也用它。

## 第 2 步 · 重启并确认
1. 完全退出并重新打开 VS Code（必要时重载窗口：命令面板 → Reload Window）。
2. 打开 Claude Code 扩展，确认它使用的是刚配置的 DeepSeek 服务（查看请求记录/配置项）。

## 第 3 步 · 连通性测试
1. 在实验文件夹打开 VS Code，向 Agent 发送：`请在当前文件夹创建 connection_ok.txt，内容自拟，然后读取并展示内容`。
2. 到文件管理器确认 `connection_ok.txt` **确实存在**、内容正确。
3. 让 Agent 再次回读，确认它读到的是磁盘上的实际内容。

## 第 4 步 · 截图打码
1. 截取：CC Switch 配置页、请求/响应记录、`connection_ok.txt` 文件内容。
2. **打码**：用涂鸦/马赛克遮住 `sk-` 之后的所有字符，只显示 `sk-****`。
3. 核对：不能只凭模型自述"连的是 DeepSeek"，要对照配置页与请求记录里的服务商/模型名。

## 第 5 步 · 存档
- 把打码后的截图放进提交文件夹（例如 `outputs/screenshots/`）。
- 报告与 README 中的密钥一律写 `sk-****`。
