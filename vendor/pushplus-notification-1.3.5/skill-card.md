## Description:

pushplus sends notifications through the PushPlus HTTP API to WeChat, ClawBot, QQ bot, email, webhook, SMS, app, and related channels, with optional Open API workflows for result lookup and account or channel management.

This skill is ready for commercial/non-commercial use.

## Publisher:

[pcstx](https://clawhub.ai/user/pcstx)

### License/Terms of Use:

MIT-0

## Use Case:

Developers and agent users use this skill to send reviewed notifications, alerts, reminders, and delivery-status checks from an agent through PushPlus channels. Operators can also use it for account, topic, blacklist, bot-binding, and forwarding-rule workflows when they intentionally provide AccessKey credentials.

### Deployment Geography for Use:

Global, with the cmcc new-message ClawBot channel limited to China Mobile users.

## Known Risks and Mitigations:

Risk: Crafted message text in shell-based request examples could execute local commands.

Mitigation: Review message content before execution, use a manual install path or pinned installer, and avoid pasting arbitrary user text directly into shell templates.

Risk: Notifications can transmit secrets or personal data to PushPlus and downstream channels.

Mitigation: Send only reviewed content and avoid including credentials, personal data, or other sensitive material in notification bodies.

Risk: AccessKey credentials allow higher-privilege account-management actions such as managing friends, blacklists, bot bindings, and forwarding rules.

Mitigation: Grant or use AccessKey credentials only when those management actions are intended, and confirm destructive actions before execution.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/pcstx/skills/pushplus-notification)
- [Artifact README](artifact/README.md)
- [Open API reference](artifact/reference.md)
- [PushPlus official site](https://www.pushplus.plus)
- [PushPlus message API V1.18](https://www.pushplus.plus/doc/guide/api.html)
- [PushPlus Open API V1.19](https://www.pushplus.plus/doc/guide/openApi.html)

## Skill Output:

**Output Type(s):** [Text, Markdown, Shell commands, Configuration guidance, API calls]

**Output Format:** [Markdown guidance with curl command examples and JSON request or response bodies]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Requires PUSHPLUS_TOKEN for sending notifications; AccessKey credentials are optional and higher-privilege for account management workflows.]

## Skill Version(s):

1.3.5 (source: server release metadata and skill frontmatter)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
