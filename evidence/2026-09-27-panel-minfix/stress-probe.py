import ast,importlib.util,json,pathlib,re,time,pandas as pd
root=pathlib.Path.cwd()/'skills/supply-chain-control-tower'
src=pathlib.Path('evidence/2026-09-27-panel-minfix/app-candidate.py').read_text()
spec=importlib.util.spec_from_file_location('fixture_tools',root/'scripts/tools.py');tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
ns={'re':re,'tools':tools,'_inv':pd.read_csv(root/'data/inventory.csv'),'_products':{p['sku']:p['brand'] for p in json.loads((root/'data/products.json').read_text())['products']},'_BRAND_CN':{}}
parsed=ast.parse(src);defs=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ('has_inventory','question_scope','verify_no_reorder')]
exec(compile(ast.Module(body=defs,type_ignores=[]),'source-guard','exec'),ns)
print('READY_TO_EXERCISE_ACTUAL_GUARD',flush=True)
t=time.monotonic();r=ns['verify_no_reorder'](','*64+'建议补货20件。\nNO_REORDER:100','Seattle 仓库 SKU13001 未来1周要补货吗？')
print(json.dumps({'verdict':r['verdict'],'elapsed_s':time.monotonic()-t}));assert r['verdict']!='PASS'
