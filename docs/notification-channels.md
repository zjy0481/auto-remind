# 手机通知渠道调研

> 调研日期：2026-09-27。只核查官方文档、官方仓库和官方隐私/条款页面；没有发送真实通知。额度、价格和平台适配会变化，以下是本次查到的官方口径。

## 结论

结合三星 S25 Ultra、主要用于 Codex、任务完成后只发一条通知的场景：

1. **首选 PushPlus 微信，App 作为备选**。用户已有 PushPlus 使用经验，微信渠道无需额外安装接收应用。若微信提醒或正文展示不满意，再验证 PushPlus App：它支持 Android、iOS 和鸿蒙，但官方适配表没有列出三星专属厂商通道；排障文档把海外品牌或国际版手机归为 FCM，并提示需要手机网络能够访问 FCM。因此不能仅凭“S25 Ultra”保证 App 到达，必须按实际 ROM、Google 服务和网络做一次低敏测试。
2. **Server酱 Turbo 是微信备选**。官方当前口径是每天 5 条免费、微信服务号等多通道；免费微信卡片默认只显示标题，正文展示和留存时间需要接受其限制或购买会员。
3. **ntfy 作为跨平台备选**。Android/iOS 都有官方 App，也能自托管；Android 投递取决于 FCM 或前台服务。官方明确说明未启用即时投递时可能延迟数分钟甚至数小时。本次没有实测 ntfy 在中国大陆网络环境的连通性，也没有据此做保证。
4. **Bark 排除**。官方项目定位是 iOS App，通知依赖 APNs，不适合三星 Android。

初版工具建议只接入 PushPlus。每次用户显式调用后，任务真正完成时发送一条摘要；摘要默认只包含完成状态、任务名和可选结果链接，不复制完整对话或敏感文件。失败提醒留作另行选择的扩展。令牌、SendKey、Bark key 和 ntfy topic 应从环境变量或本地密钥存储读取。

## 对比

| 渠道 | 手机端和到达形式 | 免费/限制（官方当前口径） | 状态语义 | 结论 |
|---|---|---|---|---|
| PushPlus App | Android、iOS、鸿蒙；App 系统通知 | 未实名发送额度 0；实名 App 每日 200；会员 2,000；会员页面标价 10 元/月 | **明确异步**：HTTP 200 只代表收到请求，返回流水号，可查询或回调 | 最值得先验证；三星到达依赖实际 FCM/ROM |
| PushPlus 微信 | 微信公众号会话，模板消息/客服消息 | 默认微信额度同上；普通模板通常只显示标题或需点开详情 | 同上 | 微信展示限制明显 |
| Server酱 Turbo | 微信服务号、企业微信、群机器人、Bark 等 | 免费 5 条/天、50 条/分钟、免费内容保留 1 天；会员最高 1,000 条/天 | code=0 代表 API 成功；本次查阅未见独立手机到达回执 | 微信优先时合适 |
| Server酱³ | iOS/Android 自有 App，主流厂商/FCM 系统推送 | 测试期间免费；正式版按 Turbo 标准，需再次核价；官方机型清单没有三星专属通道 | 官方验证要求 code=0 且 App 收到 | PushPlus App 之外的备选 |
| Bark | 官方 iOS App + APNs | App 官方称免费、无广告；未查到本次所需的公共服务日配额 | 请求成功后立即推送；无手机回执 | 三星场景排除 |
| ntfy | Android、iOS、PWA；topic 订阅通知 | 无账号可免费；ntfy.sh 每日 250 条；默认每访客 60 请求突发、每 5 秒补 1 个；正文 4,096 字节 | HTTP 返回消息 id，表示服务已发布，不是手机显示回执 | 跨平台/自托管备选 |

## PushPlus

### API 和异步状态

官方消息接口是 POST https://www.pushplus.plus/send，正文包括 token、title、content，可选 channel 和 template。支持 html、txt、markdown、json 等模板。

当前接口是异步的：code=200 只表示服务端收到并通过同步校验，不代表微信或手机已经送达。返回 data 中的消息流水号可用于查询最终结果；也可传 callbackUrl 接收异步结果。查询状态为 0 未投递、1 发送中、2 已发送、3 发送失败。

工具应区分 accepted（PushPlus 接受请求）与 delivered/failed（查询或回调得到的渠道结果）。不要把 HTTP 200 直接显示为“手机已收到”。

来源：[消息接口文档](https://pushplus.plus/doc/guide/api.html)、[开放接口与发送结果查询](https://pushplus.plus/doc/guide/openApi.html)。

### Android、三星和微信

只有 channel=app 才会在 pushplus App 产生手机通知；微信、短信、邮件、语音和 webhook 不会在 App 弹通知。官方 App 页面列出苹果、荣耀、小米、OPPO、vivo、华为安卓、原生鸿蒙、魅族和 Google，未列三星。

官方排障页说，海外品牌或国际版手机的通知走 Android 原生 FCM，需要手机网络能够访问 FCM；同时要打开 App 通知权限。S25 Ultra 的具体 ROM 是否有 Google 服务、网络是否能访问 FCM，需实测。

App 本机消息永久保存在手机中，历史消息可查看 30 天；一个账号的 App 同时只能登录一台设备。也可以把微信渠道消息转发到 App，官方称不需要再请求一次 App 渠道，也不计算 App 渠道次数。

来源：[App 渠道说明](https://pushplus.plus/doc/channel/app.html)、[App 无弹框排障](https://pushplus.plus/doc/help/app.html)。

PushPlus 的 wechat 是微信公众号渠道，不是给个人微信号任意发私聊。官方说明微信模板由微信审核，不能自由改字段；服务号模板默认不展示具体正文，通常需要点开链接查看。发送“激活消息”后，后续 24 小时内最多 5 条可用客服消息方式直接展示；会员模板可显示更多内容；绑定自己的认证服务号可自定义模板，官方页面写明认证每年 300 元。

来源：[微信模板说明](https://pushplus.plus/doc/help/template.html)、[公众号展示内容](https://pushplus.plus/doc/help/showmessage.html)。

### 额度、收费和隐私

官方额度页面当前列出：

- 未实名认证用户的微信和 App 发送额度都是 0；实名用户为 200 次/日，会员为 2,000 次/日。
- 普通用户接口频率为 1 分钟 5 次，相同内容 1 小时最多 3 条；历史消息保留 30 天。
- 自 2024 年 8 月起，未实名认证用户不能调用发送消息接口，接口返回 905。
- 会员页面当前标价 10 元/月；短信每条 0.1 元，语音每次 0.3 元。App 和微信公众号标为免费，但仍受实名认证和额度规则约束。

微信实名用户达到 200 次/日后会当天停止推送，继续过量还可能触发更长时间限制；该工具的“一任务一条”频率通常足够，但应处理 905、900 等错误码，不要无脑重试。

实名认证协议要求姓名、身份证号、手机号和短信验证码等资料；协议写明平台保留认证资料，并承诺在法定/约定事由外不公开或为商业目的透露非公开内容，同时采取必要安全技术保护资料。本次查阅的 PushPlus 官方文档没有提供消息端到端加密方案，因此建议只发送短摘要和链接。

来源：[系统功能额度](https://pushplus.plus/doc/guide/use.html)、[会员功能](https://pushplus.plus/doc/function/vip.html)、[短信/语音收费](https://pushplus.plus/doc/channel/)、[返回码](https://pushplus.plus/doc/guide/code.html)、[隐私协议](https://pushplus.plus/doc/introduce/privacy.html)。

## Server酱

当前官方文档把产品分成两个独立系统：Turbo 使用 SCT 类 SendKey，主打微信和多通道；Server酱³ 使用 sctp 类 SendKey，主打独立 App，两种 key 不通用。

Turbo 的典型端点是 POST https://sctapi.ftqq.com/{SendKey}.send，参数为 title 和 desp。SC3 的官方示例端点是 https://<uid>.push.ft07.com/send/{SendKey}.send。成功响应 JSON 的 code 为 0；官方验证步骤还要求微信或 App 实际收到消息。

本次查阅的官方页面没有看到像 PushPlus 那样的消息流水号查询、送达状态或回调接口。因此工具应把 code=0 记录为“服务接受/处理成功”，不能宣称手机已显示。

Turbo 通道包括微信服务号、测试号、企业微信应用、企业微信群机器人、钉钉/飞书群机器人、Bark iOS、PushDeer 和自定义 webhook。免费微信服务号卡片只显示标题；会员通常可显示标题和内容，但官方特别注明服务号通道展开内容易被举报。

官方 FAQ 当前口径是：Turbo 每天最多 5 条、每分钟最多 50 条，免费内容保留 1 天、会员 3 天；会员每天最多 1,000 条。当前页面列出的促销价为 8 元/月、39 元/12 个月、180 元/60 个月，需以订阅页实际值为准。SC3 测试期间免费，正式版收费标准与 Turbo 一致，实际开通前应再次核对。

官方 SDK 说明支持 noip=1（SCT 专用）隐藏调用 IP；官方文档明确要求不要把 SendKey 写进代码、日志或 git。公开资料没有端到端加密说明，应把正文视为经过 Server酱及其落点处理的数据。

来源：[首页/API](https://sct.ftqq.com/docs/)、[SendKey](https://sct.ftqq.com/docs/getting-started/sendkey/)、[通道对比](https://sct.ftqq.com/docs/getting-started/channels/)、[额度与 FAQ](https://sct.ftqq.com/docs/getting-started/faq/)、[官方 SDK](https://github.com/easychen/serverchan-sdk)。

## Bark（排除项）

Bark 官方 App 是 iOS App，通知依赖 APNs；最小 API 支持 GET/POST，路径为 /{key}/{body}、/{key}/{title}/{body} 或 /{key}/{title}/{subtitle}/{body}，也支持 JSON POST。官方说请求成功后会立即收到推送，但没有手机显示回执或异步查询状态。

官方项目称 App 免费、无广告至少运营到 2031 年 7 月，并支持自建服务端和推送加密。默认链路会经过发送端、Bark 服务端、APNs 和设备；官方建议自建 HTTPS 服务端或使用自定义密钥加密推送。由于项目定位是 iOS App，三星 Android 场景不纳入实现。

来源：[Bark 官网](https://bark.day.app/)、[中文 README](https://github.com/Finb/Bark/blob/master/README.zh.md)、[服务端 API V2](https://raw.githubusercontent.com/Finb/bark-server/master/docs/API_V2.md)、[隐私](https://github.com/Finb/Bark/blob/master/docs/privacy.md)、[加密](https://github.com/Finb/Bark/blob/master/docs/encryption.md)。

## ntfy（跨平台备选）

发布只需向 https://ntfy.sh/<topic> 发 HTTP POST 或 PUT，正文是消息内容，Title、Priority、Tags 等通过请求头设置。发布响应包含消息 id 和时间，可用于更新同一条通知；它表示服务已经发布消息，不是手机显示回执。

官方提供 Android App（Google Play、F-Droid、GitHub APK）和 iOS App Store 版本，也有 PWA。Google Play 版本在主站 ntfy.sh 使用 FCM；F-Droid 版本不使用 Firebase，而是以前台服务维持连接。官方明确写明，关闭即时投递后 Android 消息可能延迟数分钟甚至数小时；启用即时投递会看到常驻前台通知。这个前台服务/电池取舍需要结合用户偏好验证。

ntfy.sh 无账号可免费使用。官方发布页列出 ntfy.sh 每日消息上限 250、每访客默认 60 请求突发额度并每 5 秒补 1 个、正文 4,096 字节、附件 2 MB/访客总量 20 MB。付费计划主要增加额度和 topic 预留，价格以官方主页实时值为准。

topic 默认公开，未注册时 topic 名实际上就是访问凭据，应使用不可猜的随机名；需要更强控制时使用账号/访问控制或自建服务。官方隐私政策写明消息默认缓存 12 小时、附件 3 小时；App Store/Google Play 移动端使用 FCM 时，消息元数据和内容可能经过 Google FCM。可以用 Cache: no 禁止服务端缓存，Firebase: no 禁止转发到 FCM，但 Android 可能因此延迟。自建 ntfy 的 iOS 即时推送仍需要向 ntfy.sh 或配置了 APNs/FCM 的上游转发 poll request。

来源：[发布消息](https://docs.ntfy.sh/publish/)、[手机端](https://docs.ntfy.sh/subscribe/phone/)、[隐私政策](https://docs.ntfy.sh/privacy/)、[服务端配置](https://docs.ntfy.sh/config/)、[官方定价](https://ntfy.sh/)。

## 初版落地边界

建议接口只有：notify(title, summary, result_url?) -> accepted / failed。

默认使用 PushPlus 微信的请求参数：token、title、content、template=txt、channel=wechat；若改用 App 则设置 channel=app。使用 HTTPS，设置连接/读取超时，处理业务错误与 HTTP 错误，任务真正完成后只发一次，并记录返回的流水号。需要最终渠道状态时，再按官方查询接口轮询或配置 callbackUrl。

通知发送结果应写成“PushPlus 服务已接受请求”，不要仅依据接口受理就写成“手机已收到”。若 PushPlus 微信体验不满足需要，再评估 App 或 Server酱 Turbo；若未来需要跨平台、自托管或更细的 topic/权限控制，再评估 ntfy。
