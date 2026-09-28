# auto-remind

个人自用的 Codex 完成提醒 Skill，基于 PushPlus 官方 `pushplus-notification` v1.3.5 做少量修改。明确指定后，在任务完成及必要验证结束时，通过 PushPlus 向自己发送一条微信通知。

使用 Python 标准库发送 HTTP 请求，无需 MCP 服务或额外 Python 依赖。需要 Python 3.9+、能够执行本地命令的 Codex，以及可发送消息的 PushPlus Token。

## 仓库内容

| 路径 | 内容 |
| --- | --- |
| `skills/pushplus-notification/` | 可安装的定制版 Skill、发送脚本、模板和配置示例 |
| `vendor/pushplus-notification-1.3.5/` | 未修改的官方原包、解包文件及发布元数据 |
| `tests/` | 使用模拟传输的本地测试，不发送真实消息 |
| `docs/` | 渠道调研和方案说明，属于历史调研记录 |

上游来源及本地变更见 [定制记录](skills/pushplus-notification/LOCAL-CHANGES.md)。官方原包没有可执行发送脚本，只有 API 说明和 curl 示例。

## 用户级安装

在仓库根目录执行以下 PowerShell 命令。默认安装到 `~/.codex/skills`；设置了 `CODEX_HOME` 时使用该目录。

```powershell
$skillHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$skillTarget = Join-Path $skillHome 'skills/pushplus-notification'
if (Test-Path -LiteralPath $skillTarget) { throw '目标已存在，请先对比版本并保留 .env 和 .state。' }
New-Item -ItemType Directory -Force -Path (Split-Path $skillTarget) | Out-Null
Copy-Item -LiteralPath './skills/pushplus-notification' -Destination $skillTarget -Recurse
Copy-Item -LiteralPath (Join-Path $skillTarget '.env.example') -Destination (Join-Path $skillTarget '.env')
```

在**安装目录**的 `.env` 中填写自己的 Token：

```dotenv
PUSHPLUS_TOKEN=你的PushPlus消息Token或用户Token
```

发送脚本优先使用环境变量 `PUSHPLUS_TOKEN`，其次使用脚本所在 Skill 目录的 `.env`，不会从当前项目寻找凭据。仅发送消息不需要 `secretKey`。真实 `.env`、发送状态与 Python 缓存已加入 Git 忽略规则。

## 使用

在 Codex 中显式选择“完成提醒（PushPlus）”，或在请求中加入：

> （任务内容……）完成并验证后，使用 $pushplus-notification 通知我。

本技能关闭了隐式调用，单纯提及中文名称不保证宿主会加载。安装后下一轮可用；如果技能列表未刷新，重新启动 Codex。

本次明确要求即为完成通知授权，发送时无需再次确认。等待输入、子任务完成、失败及取消不会自动发送完成通知。

通知格式由 [notification-template.txt](skills/pushplus-notification/notification-template.txt) 管理：

```text
任务已完成｜任务名称
结果：简短结果
验证：实际验证情况（可省略）
产物：可访问链接（可省略）
可以回到电脑查看完整结果。
```

## 本地预览与测试

将下列内容保存为 UTF-8 JSON 文件 `notice.json`（不含 Token）：

```json
{"task_id":"demo:task-1","task":"示例任务","summary":"已完成要求的工作。","verification":"相关检查通过。"}
```

```powershell
python -X utf8 ./skills/pushplus-notification/scripts/send_notification.py --input ./notice.json --dry-run
python -X utf8 -m unittest discover -s tests -v
```

`--dry-run` 不读取 Token、不联网、不写发送记录。去掉它会真实发送消息；使用安装版时应改为安装目录中脚本的绝对路径。

脚本固定使用 `wechat` 和 `txt`，不接受群组或好友接收人参数。`accepted` 只代表 PushPlus 已受理，不代表手机已经收到。`.state/notifications.sqlite3` 记录 task_id 的哈希和状态，同一 task_id 的后续调用会跳过；网络超时、程序中断或响应不明确时不自动重发。这能减少重复通知，但不能保证绝不漏发或服务端恰好发送一次。

## 更新与来源

更新时对比定制记录，保留安装目录中的 `.env` 与 `.state`。不要直接用官方包覆盖本地定制版本。

官方 Skill 的作者及许可声明保留在原文件中：其 SKILL.md/README 标记 MIT；下载包未附独立 LICENSE 文件。本仓库保留上游原貌，不把本地改动描述为官方发布版本。
