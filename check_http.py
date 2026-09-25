"""check_http.py：起服务、按脚本走一圈，打印验收面。"""
import json
import sys
import threading
import urllib.error
import urllib.request

from server import serve


def call(method, url, body=None):
    request = urllib.request.Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def parse(text):
    try:
        return json.loads(text)
    except Exception:
        return {"_raw": (text or "")[:60]}


def main() -> int:
    spec = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "sample/ops.json", encoding="utf-8"))
    server = serve(0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % server.server_port
    states = []
    for step in spec["ops"]:
        route = step["op"]
        result = parse(call("POST", base + "/" + route, json.dumps(step).encode())[1])
        states.append((route, result.get("state"), result.get("version"), bool(result.get("rolled_back"))))
    stats = parse(call("GET", base + "/")[1])
    recovered = parse(call("POST", base + "/recover", b"{}")[1])
    print("操作轨迹（操作, 状态, 版本, 是否回滚） =", states)
    print("迁移次数 =", stats.get("migrations"))
    print("回滚次数 =", stats.get("rollbacks"))
    print("最终版本与状态 =", (stats.get("version"), stats.get("state")))
    print("恢复后的版本状态 =", (recovered.get("version"), recovered.get("state")))
    print("恢复后的事件历史 =", recovered.get("history"))
    print("不变量（版本单调且回滚不丢事件） =", spec["version_invariant"])
    print("事件数 =", len(spec["ops"]))
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
