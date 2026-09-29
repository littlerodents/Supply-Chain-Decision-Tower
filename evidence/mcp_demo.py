#!/usr/bin/env python3
import json, os, subprocess, sys, time

SERVER = os.environ.get("SCT_MCP_SERVER") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skill", "scripts", "mcp_server.py")
p = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                     env=dict(os.environ, PATH=os.path.expanduser("~/node26/bin") + ":" + os.environ.get("PATH", "")))

def rpc(method, params=None, rid=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None: msg["params"] = params
    if rid is not None: msg["id"] = rid
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
    return json.loads(p.stdout.readline())

def call(name, args):
    return rpc("tools/call", {"name": name, "arguments": args}, rid=int(time.time()*1000))

print("=" * 60)
print("MCP 演示：外部 Agent 调用供应链控制塔")
print("=" * 60)

print("\n[1] MCP 握手...")
init = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                          "clientInfo": {"name": "demo-client", "version": "1.0"}}, rid=1)
server = init["result"]["serverInfo"]
print(f"  ✅ 服务端: {server['name']} v{server['version']}")
notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
p.stdin.write(json.dumps(notify) + "\n"); p.stdin.flush()

print("\n[2] 可用工具列表...")
tools_list = rpc("tools/list", rid=2)["result"]["tools"]
for t in tools_list:
    print(f"  - {t['name']}: {t['description'][:60]}")

print("\n[3] gap 工具（ROP 驱动决策）...")
r = call("gap", {"sku": 13001, "location": "San Francisco", "weeks": 12})
g = json.loads(r["result"]["content"][0]["text"])
print(f"  库存={g['current_stock']} ROP={g.get('reorder_point','N/A')} 安全库存={g.get('safety_stock','N/A')}")
print(f"  rop_gap={g.get('rop_gap','N/A')} → {'需补货' if g.get('rop_gap',0)>0 else '无需补货'}")

print("\n[4] suppliers 工具（含运费翻转检测）...")
r = call("suppliers", {"sku": 14001})
s = json.loads(r["result"]["content"][0]["text"])
if isinstance(s, list):
    for b in s[:3]: print(f"  - {b['supplier']}: ${b['unit_cost']} @ {b['location']}")
else:
    for b in s.get("board", s)[:3]: print(f"  - {b['supplier']}: ${b['unit_cost']} @ {b['location']}")

print("\n[5] scan_portfolio 工具（全组合巡检）...")
r = call("scan_portfolio", {"weeks": 12})
scan = json.loads(r["result"]["content"][0]["text"])
print(f"  扫描 {scan['combos']} 组合: 短缺 {scan['shortage_count']} / 充足 {scan['ample_count']}")
print(f"  建议采购总额: ${scan['total_reorder_cost']:,.0f}")

print("\n[6] reorder_decision 工具（旗舰：双智能体决策）...")
print("  （推理中... 约 60-120 秒）")
t0 = time.time()
r = call("reorder_decision", {"question": "San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？"})
try:
    d = json.loads(r["result"]["content"][0]["text"])
except Exception:
    d = None
print(f"  耗时: {time.time()-t0:.0f}s")
if d is None:
    print("  ⏭️ 跳过：旗舰工具需要 Agent 运行时（openclaw + 本地模型）。按 REBUILD.md 第 1-3 步部署后重跑。")
else:
    print(f"  overall: {d.get('overall','N/A')}")
    dj = d.get("decision_agent",{}).get("decision_json")
    if dj: print(f"  决策: {dj.get('decision')} · 订量 {dj.get('order_qty')} · {dj.get('supplier')}")
    iv = d.get("independent_verification")
    if iv: print(f"  核算: {iv.get('verdict')}")
    aa = d.get("audit_agent")
    if aa: print(f"  审计: {aa.get('verdict')}")

print("\n" + "=" * 60)
print("全部通过标准 MCP 协议（stdio JSON-RPC）调用完成")
print("任何 MCP 客户端（Claude/coding agent/OpenClaw）可挂载使用")
p.terminate()
