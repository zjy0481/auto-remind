# 本地定制记录

- 官方来源：https://www.pushplus.plus/doc/guide/skill.html
- 官方文档链接的发布页：https://clawhub.ai/pcstx/skills/pushplus-notification
- 安装来源：https://clawhub.ai/api/v1/download?slug=pushplus-notification&version=1.3.5
- 获取日期：2026-09-27；版本 1.3.5。
- 原始 ZIP SHA256：`1fbc6b2e2548a57130a66cbae79c85212d6c928632c1eee63ffb1d4391be8078`。
- 原包只有 SKILL.md、reference.md、README.md、skill-card.md、_meta.json，没有可执行发送脚本。
- 原始 ZIP 和解包备份保存在本项目 vendor/pushplus-notification-1.3.5。

本地修改：增加完成提醒流程、Python 标准库脚本、可编辑通知模板、.env.example、忽略规则及 Codex 显式调用元数据。安装时由配置示例创建本机 .env，真实配置不进入仓库。将上游非标准 frontmatter 环境变量字段移至正文说明，保留官方作者、版本及 API 元数据；保留通用 API 说明与参考文件。上游 README/skill-card 为原始资料，当前行为以 SKILL.md 开头的定制流程为准；定制版 README 提供当前使用说明。

任务开始时的明确通知要求即为本次完成通知授权，无需二次确认。固定给自己发微信，暂不自动提醒失败/中断。SQLite 记录发送尝试以防重复；它不提供服务端恰好一次保证，未知状态不自动重试。没有真实 Token 时只进行本地预览及模拟传输测试。

升级官方版本时先对比本地修改，保留用户已填写的 .env 和 .state；不要直接覆盖整个安装目录。
