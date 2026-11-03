"""Replay model replies at the external CLI boundary through real Streamlit widgets.
No model/network calls. AppTest is a UI-runtime fixture, not a browser/live inference.
"""
import json
import re
import subprocess
import sys
from unittest.mock import patch
# Resolve pandas' read-only platform probe before guarding the model subprocess boundary.
import pandas
from streamlit.testing.v1 import AppTest

POS_Q = 'San Francisco 仓库 SKU 13001 未来 12 周够卖吗？需要补货吗？'
NEG_Q = 'Seattle 仓库 SKU 13001 未来 1 周够卖吗？需要补货吗？'
POS = dict(decision='REORDER', sku=13001, location='San Francisco', weeks=12,
           order_qty=3268, supplier='Nature Source Coffee', unit_cost=34.5,
           shipping_cost=2.0, total_cost=119282.0,
           rationale='未来12周预测需求3298，库存30，缺3268',
           tool_trace=['gap', 'suppliers', 'shipping'])

def fenced(d):
    return '```json\n' + json.dumps(d, ensure_ascii=False) + '\n```'

CASES = {
    'good_positive': (POS_Q, fenced(POS), True),
    'good_negative': (NEG_Q, 'Seattle 仓库 SKU 13001 当前库存 300，未来 1 周预测需求 200，库存盈余 100。\n\nNO_REORDER:100', True),
    'wrong_gap': (NEG_Q, 'NO_REORDER:999', False),
    'advice': (NEG_Q, '建议补货20件。\nNO_REORDER:100', False),
    'negative_quantity': (NEG_Q, fenced(dict(POS, location='Seattle', weeks=1,
                                           order_qty=-100, total_cost=-3650.0)), False),
    'missing_fields': (POS_Q, fenced({k:v for k,v in POS.items() if k not in ('rationale','tool_trace')}), False),
    'wrong_total': (POS_Q, fenced(dict(POS,total_cost=119284)), False),
    'missing_weeks': ('Seattle 仓库 SKU 13001 需要补货吗？', 'NO_REORDER:100', False),
    'shortage_as_negative': (POS_Q, 'NO_REORDER:100', False),
    'unknown_prose': (NEG_Q, '额外拿100件以防断货。\nNO_REORDER:100', False),
    'negated_advice': (NEG_Q, '无需补货。\nNO_REORDER:100', True),
    'ambiguous_scope': ('Seattle 与 San Francisco 仓库 SKU13001 未来1周够吗？', 'NO_REORDER:100', False),
    'default_auditor_off': (None, None, False),
    # Verbatim final reply from step-acceptance/neg1.json, retained as a regression control.
    'historical_negative': (NEG_Q, 'Seattle 仓库 SKU 13001 未来 1 周库存充足，**不需要补货**。\n\n- 当前库存：300\n- 未来 1 周预测需求：200\n- 缺口：+100（盈余）\n\nNO_REORDER:100', True),
    'empty_question': ('', 'NO_REORDER:100', False),
    'empty_reply': (NEG_Q, '', False),
    'double_marker': (NEG_Q, 'NO_REORDER:999\nNO_REORDER:100', False),
    'mixed_decisions': (NEG_Q, fenced(POS)+'\nNO_REORDER:100', False),
    'mixed_wrong_gap': (NEG_Q, fenced(POS)+'\nNO_REORDER:999', False),
    'wrong_context_positive': (NEG_Q, fenced(POS), False),
    'eight_field_positive': (POS_Q, fenced({k:v for k,v in POS.items() if k not in ('sku','location','weeks')}), True),
    'wrong_prefix_fact': (NEG_Q, '当前库存999。\nNO_REORDER:100', False),
    'zero_quantity': (POS_Q, fenced(dict(POS, order_qty=0,total_cost=0)), False),
    'boolean_quantity': (POS_Q, fenced(dict(POS, order_qty=True)), False),
    'fractional_quantity': (POS_Q, fenced(dict(POS, order_qty=3268.5)), False),
    'empty_rationale': (POS_Q, fenced(dict(POS, rationale='')), False),
    'empty_trace': (POS_Q, fenced(dict(POS, tool_trace=[])), False),
    'nan_money': (POS_Q, fenced(dict(POS, total_cost=float('nan'))), False),
    'zero_gap': (NEG_Q, 'NO_REORDER:0', True),
}
selected=sys.argv[2:] or list(CASES)
results=[]
for name in selected:
    question, reply, expected=CASES[name]
    calls=[]
    original_csv=None
    if name=='zero_gap':
        from pathlib import Path
        csv=Path(sys.argv[1]).parent.parent/'data/inventory.csv'
        assert csv.parent.parent.name.startswith('pi-panel-minfix-'), 'Never mutate production data for a fixture'
        original_csv=csv.read_bytes()
        inv=pandas.read_csv(csv)
        inv.loc[(inv.sku==13001)&(inv.location=='Seattle'),'quantity']=200
        inv.to_csv(csv,index=False)
    def external_fixture(cmd,*args,**kwargs):
        if not (isinstance(cmd,list) and str(cmd[0]).endswith('/openclaw') and cmd[1]=='agent'):
            raise AssertionError('Unexpected subprocess; test refuses external execution')
        if '--agent' in cmd:
            raise AssertionError('Unexpected auditor call in single-agent fixture')
        calls.append('MODEL_REPLY_FIXTURE_ONLY')
        return subprocess.CompletedProcess(cmd,0,json.dumps({'result':{'meta':{
            'finalAssistantVisibleText':reply,'agentMeta':{'provider':'fixture','model':'no-live-model','durationMs':1},
            'toolSummary':{'calls':0,'failures':0}}}}), '')
    try:
        with patch('subprocess.run',external_fixture):
            app=AppTest.from_file(sys.argv[1],default_timeout=20).run()
            assert not app.exception, [str(x.value) for x in app.exception]
            checkbox=next(x for x in app.checkbox if '串审计智能体' in x.label)
            if name=='default_auditor_off':
                actual=checkbox.value
                cards=[]
            else:
                checkbox.set_value(False)
                next(x for x in app.text_area if x.label=='问句').set_value(question)
                next(x for x in app.button if '提交（单次）' in x.label).click()
                app.run()
                assert not app.exception, [str(x.value) for x in app.exception]
                assert len(calls)==1, 'fixture did not exercise the reply path exactly once'
                cards=[x.value for x in app.markdown if "class='card'" in x.value and
                       ('独立核算' in x.value or '负例' in x.value or '未通过' in x.value)]
                actual=any("class='good'" in x for x in cards)
                assert cards, 'No verdict card was rendered'
            results.append({'case':name,'expected_success':expected,'actual_success':actual,
                            'pass':bool(actual==expected),'cards':cards,'fixture_calls':len(calls)})
    except Exception as e:
        results.append({'case':name,'pass':False,'harness_error':type(e).__name__+': '+str(e)[:1200]})
    finally:
        if original_csv is not None:
            csv.write_bytes(original_csv)
print(json.dumps({'mode':'ISOLATED_STREAMLIT_UI_REPLY_REPLAY','new_model_calls':0,'results':results},ensure_ascii=False,indent=2))
sys.exit(0 if all(r['pass'] for r in results) else 1)
