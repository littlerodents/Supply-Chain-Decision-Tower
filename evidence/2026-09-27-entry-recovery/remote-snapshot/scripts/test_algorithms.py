#!/usr/bin/env python3
"""algorithms.py 的教科书用例测试（TDD：先写测试，红→绿）。

运行：python3 scripts/test_algorithms.py && echo ALL-GREEN
用例数字全部来自运筹学/库存管理教科书标准公式，可手验。
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("alg", os.path.join(HERE, "algorithms.py"))
alg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alg)


def close(a, b, tol=0.02):
    assert abs(a - b) <= tol, f"{a} != {b} (tol {tol})"


# 1) 安全库存 SS = z_α · σ_d · √L：z(0.95)=1.645, σ=50, L=4 → 1.645·50·2 = 164.50
close(alg.safety_stock(sigma=50, lead_time_weeks=4, service_level=0.95), 164.50)

# 2) 再订货点 ROP = μ_d·L + SS：μ=200, L=4, SS=164.50 → 800+164.50 = 964.50
close(alg.reorder_point(mu=200, sigma=50, lead_time_weeks=4, service_level=0.95), 964.50)

# 3) EOQ Q* = √(2DK/h)：D=12000, K=50, h=3 → √400000 = 632.46
close(alg.eoq(annual_demand=12000, order_cost=50, holding_cost=3), 632.46)

# 4) 报童临界比：Cu=8, Co=2 → ratio=0.8, z(0.8)=0.8416; μ=100, σ=20 → 100+16.83 = 116.83
close(alg.newsvendor(mu=100, sigma=20, underage=8, overage=2), 116.83, tol=0.02)

# 5) z 值表自检：95%→1.645, 80%→0.8416
close(alg._z(0.95), 1.645)
close(alg._z(0.80), 0.8416, tol=0.001)

print("ALL-GREEN: 5 组教科书用例通过")
sys.exit(0)
