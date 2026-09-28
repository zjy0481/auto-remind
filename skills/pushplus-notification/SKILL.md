---
name: pushplus-notification
description: 完成提醒。仅当用户明确调用本技能或要求使用完成提醒/PushPlus 通知时使用；在指定任务完成及必要验证结束后向用户本人发送一条微信通知。
license: MIT
metadata:
  author: perk-net
  version: 1.3.5
  apiVersion: "1.18"
  openApiVersion: "1.19"
  tags:
    - notification
    - pushplus
    - wechat
    - clawbot
    - cmcc
    - qqbot
    - messaging
---

# 完成提醒（PushPlus 官方 Skill 的本地定制版）

基于官方 v1.3.5，来源与改动见 [LOCAL-CHANGES.md](LOCAL-CHANGES.md)。下列完成提醒流程优先于后面的通用 curl 示例；其他能力仅在用户另外明确要求时使用。

## 当前任务完成提醒

1. 用户明确要求“在你完成该任务后，使用完成提醒通知我”即授权本次任务的一条完成通知，无需发送前再次确认。记录授权对应的任务范围和稳定 task_id（会话标识加本次任务标识；同一任务重试复用）。未授权的任务不发送。
2. 完成用户指定的整体工作及必要验证后，在最终回复前发送。中途汇报、子任务完成、等待输入、失败或取消不等于完成。用户撤销提醒时停止发送。
3. 将非敏感摘要写成 UTF-8 JSON 临时文件，字段为 task_id、task、summary；verification 和 artifact_url 可省略。验证字段只写实际证据；产物仅填适合手机访问的 http(s) 链接。模板由 [notification-template.txt](notification-template.txt) 管理。
4. 通过命令工具运行 `python -X utf8 "<本技能绝对目录>/scripts/send_notification.py" --input "<JSON绝对路径>"`，使用本机可用的 Python 3.9+ 解释器。目录从本 SKILL.md 位置解析，不依赖当前项目；JSON 用文件写入工具生成，避免把摘要拼进 Shell 命令。
5. `--dry-run` 仅预览，不发消息。实际发送固定为本人、微信、纯文本。脚本自行读取环境变量 PUSHPLUS_TOKEN，未设置时读取本技能目录 `.env`；不要在工具输出或上下文中读取/展示密钥。缺少配置时报告 `.env` 路径，主任务正常收尾。
6. accepted 只报告“通知已提交至 PushPlus”；unknown 表示到达情况未知，禁止自动重试或换 task_id 绕过去重。duplicate_skipped 时查看 previous_status，不能把之前失败/未知说成成功。rejected/configuration_error 单独说明提醒失败，不改变任务结果。`.state` 仅保存任务标识哈希与状态；有发送记录即跳过再次提交。

JSON 示例（不是发送授权）：

```json
{"task_id":"session-id:task-1","task":"登录异常修复","summary":"已修复登录后跳回首页的问题。","verification":"相关测试通过。"}
```

显式选择界面中的“完成提醒（PushPlus）”或 `$pushplus-notification` 最可靠。禁用隐式调用后，单纯自然语言提及未必让宿主加载技能；不要承诺任何场景下都能发现它。

## 官方通用能力参考


通过 pushplus HTTP API 向微信、微信 ClawBot、新消息ClawBot、QQ 机器人、邮箱、webhook、短信、App 等渠道推送消息。无需安装依赖，Shell + curl 即可。

依据：[消息接口文档 V1.18](https://www.pushplus.plus/doc/guide/api.html)。开放能力（查结果 / 群组 / 好友 / 黑名单 / 渠道 / ClawBot / 新消息ClawBot / QQ 机器人绑定 / 消息规则等）见 [reference.md](reference.md)。

## 前置条件

用户需提供 `PUSHPLUS_TOKEN`（用户 token 或消息 token），在 [pushplus.plus](https://www.pushplus.plus) 注册获取。调用发送接口前需完成实名认证。

完成提醒使用上面的本地脚本读取凭据。其他显式授权的操作也通过本机程序读取环境变量或本技能目录 `.env` 的 PUSHPLUS_* 配置，不把凭据输出到对话或命令参数。缺少配置时请用户在本机文件中填写。

## API 端点

| 功能 | 方法 | URL |
|------|------|-----|
| 发送消息 | GET/POST/PUT/DELETE | `https://www.pushplus.plus/send` |
| 多渠道发送 | GET/POST/PUT/DELETE | `https://www.pushplus.plus/batchSend` |

- Content-Type: `application/json`
- 参数均支持 url 参数和 body 参数
- token 可放在路径：`/send/{token}`、`/batchSend/{token}`
- GET 受 URL 长度限制，content 不宜过长；大段内容请用 POST
- 在线调试：https://api.pushplus.plus/

## 发送消息（/send）

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"TOKEN","title":"标题","content":"内容","template":"html","channel":"wechat"}'
```

### 请求参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | 是 | 无 | 用户 token 或消息 token；可放到路径 `/send/{token}` |
| `title` | 否 | 无 | 消息标题 |
| `content` | 是 | 无 | 具体消息内容，根据不同 template 支持不同格式 |
| `topic` | 否 | 无 | 群组编码，不填仅发送给自己；channel 为 webhook 时无效 |
| `template` | 否 | `html` | 发送模板 |
| `channel` | 否 | `wechat` | 发送渠道 |
| `option` | 否 | 无 | 渠道配置参数（原 webhook 参数） |
| `callbackUrl` | 否 | 无 | 发送结果回调地址 |
| `timestamp` | 否 | 无 | 毫秒时间戳，如 `1632993318000`；服务器时间戳大于此值则消息不会发送 |
| `to` | 否 | 无 | 好友令牌（微信公众号 / QQ 机器人）或企业微信用户 id；多人用逗号隔开；实名最多 10 人，会员 100 人 |
| `pre` | 否 | 无 | 预处理编码；仅供会员使用 |
| `pushId` | 否 | 无 | 推送表单/文档/表格。`template=form` 时必填，传表单编码（formCode）；`template=doc` 时必填，传文档编码（docCode）；`template=excel` 时必填，传表格编码（docCode） |

`option` 说明：原 webhook 参数。`cp`、`webhook`、`mail`、`qq` 渠道需填写个人中心渠道设置中已配置的**渠道编码**（非完整 URL）。邮件渠道 `option` 可选，不填则用官网邮件发送。`qq` 渠道不填 `option` 时发给自己，填写配置编码则发送到对应 QQ 群。

`topic` 与 `to` 勿同时填写；群组优先于好友。`to` 支持微信公众号、邮件、企业微信、QQ 机器人渠道。QQ 机器人发送到群（带 `option`）时不可同时填写 `topic` 或 `to`。

### 发送渠道（channel）

| 值 | 费用 | 说明 |
|----|------|------|
| `wechat` | 免费 | 微信公众号（默认） |
| `app` | 免费 | App；安卓 / 鸿蒙 / iOS |
| `extension` | 免费 | 浏览器扩展插件 / 桌面应用程序 |
| `webhook` | 免费 | 第三方 webhook（企微/钉钉/飞书/bark/Gotify/轻联/集简云/server酱/IFTTT/WxPusher 等）；需 `option` |
| `clawbot` | 免费 | 微信 ClawBot |
| `cmcc` | 免费 | 新消息ClawBot；仅支持中国移动用户；需先绑定 Channel API Key；不填 `option` |
| `qq` | 免费 | QQ 机器人；不填 `option` 发给自己，填配置编码发到对应 QQ 群；需先绑定 |
| `cp` | 免费 | 企业微信应用；需 `option` |
| `mail` | 免费 | 邮箱；`option` 可选 |
| `sms` | 收费 | 短信；成功 1 条扣 10 积分（0.1 元）；接收方需绑定手机 |
| `voice` | 收费 | 语音；接通 1 次扣 30 积分（0.3 元） |

### 发送模板（template）

| 值 | 说明 |
|----|------|
| `html` | 默认模板，支持 html 文本 |
| `txt` | 纯文本展示，不转义 html |
| `json` | 内容基于 json 格式展示 |
| `markdown` | 内容基于 markdown 格式展示 |
| `cloudMonitor` | 阿里云监控报警定制模板 |
| `jenkins` | jenkins 插件定制模板 |
| `route` | 路由器插件定制模板 |
| `pay` | 支付成功通知模板 |
| `form` | push 表单模板；**需同时传 `pushId`**（formCode）；[创建表单](https://www.pushplus.plus/push/pushform) |
| `doc` | push 文档模板；**需同时传 `pushId`**（docCode）；[创建文档](https://www.pushplus.plus/push/pushdoc) |
| `excel` | push 表格模板；**需同时传 `pushId`**（docCode）；[创建表格](https://www.pushplus.plus/push/pushtable) |

### 响应

```json
{
  "code": 200,
  "msg": "请求成功",
  "data": "3cbc5eab19fe512e80677540fbde332a"
}
```

接口为**异步**：`code=200` 仅表示服务端已收到请求，**不表示发送成功**。`data` 为消息流水号，可用于查询最终结果（开放接口 `sendMessageResult`）。若传了 `callbackUrl`，发送完成后会 POST 回调：

```json
{"event":"message_complate","messageInfo":{"shortCode":"...","sendStatus":2,"message":""}}
```

`sendStatus`：0 未发送 / 1 发送中 / 2 成功 / 3 失败。群组新增用户、新增好友也会回调到同一地址（`event` 分别为 `add_topic_user`、`add_friend`）。

## 多渠道发送（/batchSend）

与 `/send` 参数相同，差异：

| 参数 | 说明 |
|------|------|
| `channel` | 多个用逗号隔开，如 `"wechat,webhook,extension"` |
| `option` | 多个用逗号隔开，与 channel **一一对应**；某渠道无需 option 也要占位，如 `",bark,"` |

说明：
1. 本质是服务端循环调用发送消息接口
2. 按渠道数量计算请求次数（3 个渠道 = 3 次）
3. 响应 `data` 为数组，每项含 `shortCode`、`message`、`code`、`channel`

```json
{
  "code": 200,
  "msg": "执行成功",
  "data": [
    {
      "shortCode": "f9117123dc31434fa38917b7e4c6c3ff",
      "message": "请求成功，请用流水号查询最终发送结果",
      "code": 200,
      "channel": "wechat"
    }
  ]
}
```

## 使用流程

1. 获取 `PUSHPLUS_TOKEN`
2. 选择 `template` 与 `channel`（默认 `html` + `wechat`）
3. `webhook` / `cp` 确认已配置渠道编码并填入 `option`；`mail` 的 `option` 可选；`qq` 发给自己不填 `option`，发到群则填群配置编码；`cmcc` 不填 `option`，需先绑定
4. `template` 为 `form` / `doc` / `excel` 时确认已有对应 `pushId`（须先在官网创建）
5. 完成提醒沿用任务开始时的明确授权；其他发送操作按用户当前明确指定的收件人和内容执行，信息不完整时再澄清。
6. POST 请求；检查 `code` 是否为 200
7. 成功则反馈流水号（请求已受理）；失败根据 `msg` 说明
8. 需确认送达 / 管理群组好友黑名单 / 绑定 ClawBot、新消息ClawBot 或 QQ 机器人 / 配置消息规则 → 阅读 [reference.md](reference.md)

## 模板选择策略

| 场景 | 模板 |
|------|------|
| 简单文本 | `txt` |
| 报告 / 日志 | `markdown` |
| 富文本 / 邮件 | `html` |
| 结构化数据 | `json` |
| push 表单 | `form`（需 `pushId`=formCode） |
| push 文档 | `doc`（需 `pushId`=docCode） |
| push 表格 | `excel`（需 `pushId`=docCode） |

## 示例

### 最简 POST

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容"}'
```

### Markdown / JSON

```bash
# markdown
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"# 大标题\n##### 小标题\n1. 第一项\n2. 第二项","template":"markdown"}'

# json（content 为 JSON 字符串；template 放 body 才会解析 content）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"{\"name\":\"名称\",\"size\":\"大小\"}","template":"json"}'
```

### ClawBot

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"提醒","content":"任务已完成","template":"txt","channel":"clawbot"}'
```

### 新消息ClawBot

需先在手机 5G 消息「新消息ClawBot」应用号中获取 Channel API Key（`ak_` 或 `app_` 开头），再在个人中心绑定，或用开放接口 `/open/cmcc/bind`（见 [reference.md](reference.md)）。仅支持中国移动用户。不填 `option`。建议 `template=txt`，其他模板会转成纯文本摘要。

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"提醒","content":"任务已完成","template":"txt","channel":"cmcc"}'
```

### QQ 机器人

需先在个人中心 → 渠道配置 → QQ 机器人完成绑定（也可用开放接口，见 [reference.md](reference.md)）。

```bash
# 发给自己（不填 option）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"提醒","content":"任务已完成","template":"txt","channel":"qq"}'

# 发到 QQ 群（option 填已配置的群配置编码 qqCode）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"提醒","content":"# 构建完成\n- 耗时 12s","template":"markdown","channel":"qq","option":"qqgroup"}'
```

建议用 `txt` 或 `markdown`：`txt` 完整展示正文，`markdown` 走 QQ 原生 Markdown（不支持代码块和 HTML）；其他模板仅摘要展示，详情需点开链接。正文上限约 2000 字。

### Webhook / 企业微信应用

```bash
# webhook（option 为已配置的编码，如企业微信机器人）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","channel":"webhook","option":"pushplus"}'

# 企业微信应用
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","channel":"cp","option":"cp"}'
```

### 群组 / 好友

```bash
# 一对多（topic）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","topic":"code","template":"html"}'

# 好友（to）；勿与 topic 同时填
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","to":"好友令牌","template":"html"}'
```

### 邮件 / 短信

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"邮件标题","content":"邮件正文","channel":"mail","option":"163","template":"html"}'

curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"短信","content":"消息内容正文","channel":"sms"}'
```

### push 表单 / 文档 / 表格

须先在官网创建对应资源并取得编码，再作为 `pushId` 发送。

```bash
# 表单（pushId = formCode）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"push表单demo","content":"push表单demo","template":"form","pushId":"YpRUxav9"}'

# 文档（pushId = docCode）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"push文档","content":"push文档","template":"doc","pushId":"文档编码"}'

# 表格（pushId = docCode）
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"push表格","content":"push表格","template":"excel","pushId":"表格编码"}'
```

### 时间戳防过期

```bash
curl -s -X POST "https://www.pushplus.plus/send" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","timestamp":1632993318000}'
```

### 多渠道 batchSend

```bash
curl -s -X POST "https://www.pushplus.plus/batchSend" \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_TOKEN","title":"标题","content":"消息内容","topic":"code","template":"html","channel":"wechat,webhook,extension","option":",bark,"}'
```

## 注意事项

- content 中双引号转义为 `\"`，换行用 `\n`（markdown 亦然）
- GET 中文 content 需 UrlEncode；大段内容用 POST（GET 受 URL 长度限制）
- `template=json` 放在 body 时会解析 `content` 中的 JSON；若 `template=json` 放在 URL 上，则**整个 body 视为 content**（适合第三方 webhook 无法改 body 的场景）
- `topic` 与 `to` 不要同时填写
- `qq` 渠道发到群（带 `option`）时不可同时填 `topic` / `to`；`markdown` 不支持代码块与 HTML
- `form` / `doc` / `excel` 未传 `pushId` 会校验失败
- 收费渠道（`sms` / `voice`）发送前告知会消耗积分
- token 脱敏展示（如 `a1b2****ef90`）

## 安全要求

- **发送授权**：完成提醒沿用本次任务的明确授权；其他发送操作需要对应收件人和内容的用户授权。
- **凭证保护**：不在输出中展示完整 token / secretKey / accessKey。
- **最小读取**：从 `.env` 只提取 `PUSHPLUS_*` 相关行。
- **敏感内容警示**：含密码、密钥、PII 时警告将经第三方传输。
- **凭据存放**：允许用户在本技能 `.env` 中配置凭据；请求仅在内存构造，日志和发送状态中不保存凭据。
- **破坏性开放接口**：删消息/群组/好友/QQ 群配置/消息规则、拉黑、解绑 ClawBot / 新消息ClawBot 或 QQ 机器人等须先确认（见 reference.md）。

## 附加资源

- 开放接口：[reference.md](reference.md)
- [消息接口文档](https://www.pushplus.plus/doc/guide/api.html)
- [开放接口文档](https://www.pushplus.plus/doc/guide/openApi.html)
