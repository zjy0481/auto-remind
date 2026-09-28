"""Send one completion notice to yourself; Python standard library only."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from string import Template
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://www.pushplus.plus/send"


def read_token(root):
    token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if not token:
        path = root / ".env"
        if path.exists():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                key, sep, value = line.strip().partition("=")
                if sep and key.strip() == "PUSHPLUS_TOKEN":
                    token = value.strip()
                    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
                        token = token[1:-1]
    if not token or token == "YOUR_TOKEN":
        raise ValueError("请在 Skill 目录的 .env 中填写 PUSHPLUS_TOKEN。")
    return token


def build_message(data, root):
    if not isinstance(data, dict):
        raise ValueError("输入必须是 JSON 对象。")
    for field in ("task_id", "task", "summary"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError("task_id、task、summary 必须是非空字符串。")
    for field in ("verification", "artifact_url"):
        if field in data and not isinstance(data[field], str):
            raise ValueError("可选字段必须是字符串。")
    task = data["task"].strip()
    if len(task) > 80 or "\n" in task or "\r" in task:
        raise ValueError("任务名应为不超过 80 字的单行文本。")
    url = data.get("artifact_url", "").strip()
    if url and not url.startswith(("https://", "http://")):
        raise ValueError("产物链接必须是 http(s) 地址；省略电脑本地路径。")
    values = {
        "task": task,
        "summary": data["summary"].strip(),
        "verification_line": "验证：" + data["verification"].strip() if data.get("verification", "").strip() else "",
        "artifact_line": "产物：" + url if url else "",
    }
    rendered = Template((root / "notification-template.txt").read_text(encoding="utf-8-sig")).substitute(values)
    title, _, body = rendered.partition("\n")
    body = "\n".join(line for line in body.splitlines() if line.strip())
    if not title.strip() or len(title) > 100 or not body or len(body) > 20000:
        raise ValueError("模板生成的标题/正文为空或超过 PushPlus 普通用户长度限制。")
    return {"title": title, "content": body, "template": "txt", "channel": "wechat"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post(payload):
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
        return json.load(response)


def send(data, root=ROOT, transport=post):
    payload = build_message(data, root)
    payload["token"] = read_token(root)
    state = root / ".state"
    state.mkdir(exist_ok=True)
    key = hashlib.sha256(data["task_id"].strip().encode("utf-8")).hexdigest()
    with closing(sqlite3.connect(state / "notifications.sqlite3", timeout=10)) as db:
        db.execute("CREATE TABLE IF NOT EXISTS notices (id TEXT PRIMARY KEY, status TEXT NOT NULL)")
        # Reserve before the HTTP call: timeouts or crashes must not cause duplicate sends.
        inserted = db.execute("INSERT OR IGNORE INTO notices VALUES (?, 'attempting')", (key,)).rowcount
        db.commit()
        if not inserted:
            previous = db.execute("SELECT status FROM notices WHERE id=?", (key,)).fetchone()[0]
            return {"status": "duplicate_skipped", "previous_status": previous}
        try:
            response = transport(payload)
            if not isinstance(response, dict) or not isinstance(response.get("code"), int):
                result = {"status": "unknown", "message": "响应格式异常；不自动重发。"}
            elif response["code"] != 200:
                result = {"status": "rejected", "code": response["code"], "message": "PushPlus 拒绝请求，请按返回码检查配置。"}
            else:
                result = {"status": "accepted", "message": "PushPlus 已受理；不代表手机已收到。"}
                receipt = response.get("data")
                if isinstance(receipt, str) and receipt.isalnum() and len(receipt) <= 128 and payload["token"] not in receipt:
                    result["receipt"] = receipt
        except Exception:
            # Do not echo exceptions or upstream error text, which can contain credentials.
            result = {"status": "unknown", "message": "请求未得到有效结果，可能已被受理；不自动重发。"}
        db.execute("UPDATE notices SET status=? WHERE id=?", (result["status"], key))
        db.commit()
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="UTF-8 JSON 文件；省略时从标准输入读取")
    parser.add_argument("--dry-run", action="store_true", help="仅预览模板，不读取 Token、不联网、不记录发送状态")
    args = parser.parse_args()
    try:
        raw = Path(args.input).read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
        data = json.loads(raw)
        result = {"status": "preview", **build_message(data, ROOT)} if args.dry_run else send(data)
    except (ValueError, OSError, KeyError, sqlite3.Error):
        result = {"status": "configuration_error", "message": "请检查 JSON 字段、模板、Skill 目录权限及 .env 中的 PUSHPLUS_TOKEN；未确认发送。"}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in ("preview", "accepted", "duplicate_skipped") else 1


if __name__ == "__main__":
    sys.exit(main())
