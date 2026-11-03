"""Isolated red-team of deployed validators; no Streamlit execution or model calls."""
import ast
import datetime
import hashlib
import importlib.util
import json
import re
from decimal import Decimal
from pathlib import Path
import pandas as pd

out = Path(__file__).parent
snap = out / 'remote-snapshot'
source = (out / 'panel-revision2.py').read_text()
tree = ast.parse(source)
spec = importlib.util.spec_from_file_location('deployed_tools', snap / 'scripts/tools.py')
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)
g = {'pd': pd, 'tools': tools, 'json': json,
     '_inv': pd.read_csv(snap / 'data/inventory.csv'),
     '_sup': pd.read_csv(snap / 'data/suppliers.csv')}
names = {'has_inventory', 'supplier_board', 'last_json_block', 'f', 'verify_decision'}
selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
assert len(selected) == 5
old = ast.parse((snap / 'panel/app.py').read_text())
assert {n.name: ast.dump(n) for n in selected} == {
    n.name: ast.dump(n) for n in old.body if isinstance(n, ast.FunctionDef) and n.name in names}
exec(compile(ast.Module(body=selected, type_ignores=[]), 'deployed-panel-selected-functions', 'exec'), g)
positive = {'decision': 'REORDER', 'sku': 13001, 'location': 'San Francisco', 'weeks': 12,
            'order_qty': 3268, 'supplier': 'Nature Source Coffee', 'unit_cost': 34.5,
            'shipping_cost': 2.0, 'total_cost': 119282.0,
            'rationale': '工具核算夹具', 'tool_trace': ['gap', 'suppliers', 'shipping']}
cases = []


def check(name, payload, want):
    v = g['verify_decision'](payload)
    cases.append({'name': name, 'expected': want, 'actual': v['verdict'],
                  'checks': v['checks'], 'input': payload})


check('valid_positive_control', positive, 'PASS')
check('wrong_total_control', {**positive, 'total_cost': 119284}, 'FAIL')
check('missing_required_rationale_and_trace',
      {k: v for k, v in positive.items() if k not in ('rationale', 'tool_trace')}, 'FAIL')
neg = tools.stock_demand_difference(13001, 'Seattle', 1)
best = g['supplier_board'](13001, 'Seattle').iloc[0]
check('negative_order_quantity_accepted', {
    'decision': 'REORDER', 'sku': 13001, 'location': 'Seattle', 'weeks': 1,
    'order_qty': -neg['gap_stock_minus_demand'], 'supplier': best['supplier'],
    'unit_cost': float(best['unit_cost']), 'shipping_cost': float(best['shipping_to_dest']),
    'total_cost': round(-neg['gap_stock_minus_demand'] * float(best['total_unit_cost']), 2)}, 'FAIL')
branch = next(n.test for n in ast.walk(tree) if isinstance(n, ast.If)
              and 're.fullmatch' in ast.unparse(n.test) and 'NO_REORDER' in ast.unparse(n.test))
for name, text, want in [
    ('correct_negative_control', '库存300，需求200。\nNO_REORDER:100', 'PASS'),
    ('wrong_negative_gap', 'NO_REORDER:999', 'FAIL'),
    ('negative_with_reorder_advice', '建议补货20件。\nNO_REORDER:100', 'FAIL'),
]:
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    passed = bool(eval(compile(ast.Expression(branch), 'deployed-negative-branch', 'eval'),
                       {'lines': lines, 're': re}))
    cases.append({'name': name, 'expected': want, 'actual': 'PASS' if passed else 'FAIL', 'input': text})
facts = {
    'positive': tools.stock_demand_difference(13001, 'San Francisco', 12),
    'negative': neg, 'missing_record_exists': g['has_inventory'](13001, 'Portland'),
    'forecast_counts': {str(n): len(tools.get_forecast('13001', 'San Francisco').head(n)) for n in (1, 12, 26)},
    'inventory_rows': len(g['_inv']), 'supplier_rows': len(g['_sup']),
}
report = {
    'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds'),
    'method': 'AST-selected deployed validator functions and negative-success condition; isolated local snapshot, no UI response injection and no model calls',
    'first_harness_attempt': 'JSON serialization failed on numpy.bool_; fixed only evidence serialization and reran. No product changes.',
    'panel_sha256': hashlib.sha256(source.encode()).hexdigest(),
    'same_validators_in_both_remote_revisions': True,
    'facts': facts, 'cases': cases,
    'false_passes': sum(c['expected'] == 'FAIL' and c['actual'] == 'PASS' for c in cases),
}
(out / 'validator-redteam.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=lambda v: v.item()))
for c in cases:
    print(c['name'], c['expected'], c['actual'])
print('FALSE_PASSES', report['false_passes'])
assert report['false_passes'] == 4
assert facts['positive']['gap_stock_minus_demand'] == -3268 and neg['gap_stock_minus_demand'] == 100
assert Decimal('3268') * (Decimal('34.50') + Decimal('2.00')) == Decimal('119282.00')
print('DEPLOYED_DATA_LOCKED_CASES_MATCH')
