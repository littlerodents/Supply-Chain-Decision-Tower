#!/usr/bin/env python3
"""已验证库存管理经典算法插槽（Apache-2.0，同 tools.py 许可）。

定位：决策协议的"算法插槽"——gap 工具当前用周期聚合缺口（Σ需求−库存）；
本文件提供教科书级已验证算法，供决策路径升级（改 gap→ROP 判定）与
独立调用。未接入决策路径的原因见答辩文档：保证金答案与已验收证据链
完整性，deadline 前稳定优先。

公式（均可手验）：
  安全库存  SS  = z_α · σ_d · √L
  再订货点  ROP = μ_d · L + SS
  经济订量  EOQ = √(2DK/h)
  报童临界  Q*  = μ + z_{Cu/(Cu+Co)} · σ      （正态需求）

测试：test_algorithms.py（教科书用例，TDD 红→绿）。
"""
import argparse
import importlib.util
import json
import math
import os
import statistics
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))


def _z(p: float) -> float:
    """标准正态单侧分位数。"""
    return NormalDist().inv_cdf(p)


def safety_stock(sigma: float, lead_time_weeks: float, service_level: float) -> float:
    return _z(service_level) * sigma * math.sqrt(lead_time_weeks)


def reorder_point(mu: float, sigma: float, lead_time_weeks: float, service_level: float) -> float:
    return mu * lead_time_weeks + safety_stock(sigma, lead_time_weeks, service_level)


def eoq(annual_demand: float, order_cost: float, holding_cost: float) -> float:
    return math.sqrt(2 * annual_demand * order_cost / holding_cost)


def newsvendor(mu: float, sigma: float, underage: float, overage: float) -> float:
    ratio = underage / (underage + overage)
    return mu + _z(ratio) * sigma


def _tools():
    spec = importlib.util.spec_from_file_location("tools", os.path.join(HERE, "tools.py"))
    tools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools)
    return tools


def cmd_from_forecast(args):
    """用真实预测序列估 μ/σ，算安全库存与 ROP（周单位）。"""
    tools = _tools()
    df = tools.get_forecast(args.sku, args.location)
    demand = [float(x) for x in df["demand"].tolist()[: args.weeks]]
    mu, sigma = statistics.mean(demand), statistics.pstdev(demand)
    ss = safety_stock(sigma, args.lead_time_weeks, args.service_level)
    rop = reorder_point(mu, sigma, args.lead_time_weeks, args.service_level)
    print(json.dumps({
        "sku": args.sku, "location": args.location, "weeks_used": len(demand),
        "mu_weekly": round(mu, 2), "sigma_weekly": round(sigma, 2),
        "service_level": args.service_level, "lead_time_weeks": args.lead_time_weeks,
        "safety_stock": round(ss, 1), "reorder_point": round(rop, 1),
        "formula": {"safety_stock": "z*a*sigma*sqrt(L)", "rop": "mu*L+SS"},
    }, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="库存经典算法（JSON 输出）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("safety"); s.add_argument("--sigma", type=float, required=True)
    s.add_argument("--lead-time-weeks", type=float, default=1.0)
    s.add_argument("--service-level", type=float, default=0.95)

    r = sub.add_parser("rop"); r.add_argument("--mu", type=float, required=True)
    r.add_argument("--sigma", type=float, required=True)
    r.add_argument("--lead-time-weeks", type=float, default=1.0)
    r.add_argument("--service-level", type=float, default=0.95)

    e = sub.add_parser("eoq"); e.add_argument("--annual-demand", type=float, required=True)
    e.add_argument("--order-cost", type=float, required=True)
    e.add_argument("--holding-cost", type=float, required=True)

    n = sub.add_parser("newsvendor"); n.add_argument("--mu", type=float, required=True)
    n.add_argument("--sigma", type=float, required=True)
    n.add_argument("--underage", type=float, required=True)
    n.add_argument("--overage", type=float, required=True)

    f = sub.add_parser("from-forecast"); f.add_argument("--sku", type=int, required=True)
    f.add_argument("--location", required=True); f.add_argument("--weeks", type=int, default=12)
    f.add_argument("--lead-time-weeks", type=float, default=1.0)
    f.add_argument("--service-level", type=float, default=0.95)

    a = p.parse_args()
    if a.cmd == "safety":
        print(json.dumps({"safety_stock": round(safety_stock(a.sigma, a.lead_time_weeks, a.service_level), 2)}))
    elif a.cmd == "rop":
        print(json.dumps({"reorder_point": round(reorder_point(a.mu, a.sigma, a.lead_time_weeks, a.service_level), 2)}))
    elif a.cmd == "eoq":
        print(json.dumps({"eoq": round(eoq(a.annual_demand, a.order_cost, a.holding_cost), 2)}))
    elif a.cmd == "newsvendor":
        print(json.dumps({"newsvendor_q": round(newsvendor(a.mu, a.sigma, a.underage, a.overage), 2)}))
    elif a.cmd == "from-forecast":
        cmd_from_forecast(a)


if __name__ == "__main__":
    main()
