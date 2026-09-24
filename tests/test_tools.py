#!/usr/bin/env python3
"""supply-chain-control-tower 工具层测试（seam：scripts/tools.py 的模块接口）。

运行：python3 -m pytest tests/test_tools.py -v  （或 python3 tests/test_tools.py）

规范说明（SDD 对齐）：
- 绿色部分 = 现有行为的回归锁（含上游 bug 修复的回归测试）
- **xfail 部分 = 挂给队友的修理位**（见 BOARD 的 Bug 队列 BUG-1/2/3）——修好即变绿，
  这就是留出的接手余量：测试即工单。
"""
import importlib.util
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(BASE, "skills", "supply-chain-control-tower", "scripts", "tools.py")

spec = importlib.util.spec_from_file_location("tools", TOOLS)
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


def _cli(*args):
    r = subprocess.run([sys.executable, TOOLS, *args], capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout


def test_forecast_deterministic_same_process():
    a = tools.get_forecast("13001", "San Francisco")
    b = tools.get_forecast("13001", "San Francisco")
    assert a["demand"].tolist() == b["demand"].tolist()
    assert int(a["demand"].iloc[0]) == 200  # 第 1 周恒 200（域知识锁）


def test_forecast_deterministic_cross_process():
    _, out1 = _cli("forecast", "--sku", "11001", "--location", "San Francisco", "--weeks", "8")
    _, out2 = _cli("forecast", "--sku", "11001", "--location", "San Francisco", "--weeks", "8")
    assert out1 == out2


def test_gap_math():
    """金答案回归锁：13001@SF 12 周 = 库存30 - 需求3298 = -3268。"""
    g = tools.stock_demand_difference(13001, "San Francisco", 12)
    assert g["current_stock"] == 30
    assert g["forecast_demand"] == 3298
    assert g["gap_stock_minus_demand"] == -3268


def test_solver_upstream_bug_fixed():
    """上游 f-string bug 的回归测试：库存必须真查（修复前恒 0）。"""
    g = tools.stock_demand_difference(12001, "Seattle", 1)
    assert g["current_stock"] == 100  # 上游 bug 会让这里是 0


def test_shipping_stable():
    assert tools.get_shipping_cost("Seattle", "San Francisco") == \
        tools.get_shipping_cost("Seattle", "San Francisco")


def test_gap_negative_case_exists():
    """负例存在性锁：短周期+高库存 → gap ≥ 0（NO_REORDER 场景）。"""
    g = tools.stock_demand_difference(13001, "Seattle", 1)
    assert g["gap_stock_minus_demand"] == 100


def test_kb_products():
    import pandas as pd
    sup = pd.read_csv(os.path.join(BASE, "skills", "supply-chain-control-tower/data/suppliers.csv"))
    assert len(sup[sup.sku == 12001]) == 2  # 双供应商比价场景存在性锁


# ---------- 以下 xfail = 队友修理位（对应 BOARD Bug 队列，修好去掉标记或直接变绿） ----------
import pytest  # noqa: E402


@pytest.mark.xfail(reason="BUG-1 修理位：record_found 字段", strict=False)
def test_gap_no_record_flag():
    """BUG-1：gap 无法区分「该仓无库存记录」与「库存 0」。
    期望：无记录时返回 record_found=false（而不是静默按 0 库存算出必补货）。
    修复位：tools.py stock_demand_difference + SKILL.md SOP 第 1 步。
    """
    g = tools.stock_demand_difference(11001, "Portland", 4)  # inventory 无此行
    assert g.get("record_found") is False


@pytest.mark.xfail(reason="BUG-2 修理位：SQL 错误 JSON 化", strict=False)
def test_sql_error_json_output():
    """BUG-2：坏 SQL 应输出结构化 JSON 错误（agent 可读可自纠），而非裸 traceback。
    期望：returncode==0 且 stdout 为含 error 字段的 JSON。
    """
    rc, out = _cli("inventory", "--sql", "SELEC * FROM inventory")
    assert rc == 0
    payload = json.loads(out)
    assert "error" in payload


@pytest.mark.xfail(reason="BUG-3 修理位：weeks 边界守卫", strict=False)
def test_chart_zero_weeks_guard():
    """BUG-3：chart --weeks 0/负数应被拒绝并提示，而非产出空图/空表。"""
    rc, out = _cli("chart", "--sku", "13001", "--location", "SF", "--weeks", "0", "--out", "/tmp/x.png")
    payload = json.loads(out)
    assert "error" in payload or rc != 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
