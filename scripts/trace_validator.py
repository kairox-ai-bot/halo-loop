#!/usr/bin/env python3
import argparse, json, hashlib, sys
from datetime import datetime
REQUIRED=['trace_id','span_id','parent_span_id','trace_state','name','kind','start_time','end_time','status','resource','scope','attributes']
KINDS={'LLM','TOOL','AGENT','CHAIN','GUARDRAIL','SPAN'}
def sha256(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
 return h.hexdigest()
def parse_time(x):
 try: return datetime.fromisoformat(x.replace('Z','+00:00')) if isinstance(x,str) else None
 except Exception: return None
def load_json(path):
 with open(path) as f: return json.load(f)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('trace_jsonl'); ap.add_argument('--corpus-id',default='unknown'); ap.add_argument('--task-manifest'); ap.add_argument('--task-id-attr',default='task.id'); ap.add_argument('--redaction-report'); ap.add_argument('--dev-allow-missing-gates',action='store_true'); ap.add_argument('--requires-tools',action='store_true'); ap.add_argument('--requires-llm',action='store_true'); ap.add_argument('--requires-errors',action='store_true'); ap.add_argument('--requires-cost',action='store_true'); ap.add_argument('--output',default='trace_readiness.json'); args=ap.parse_args()
 total=parse_ok=req_ok=schema_ok=project_ok=kind_ok=parent_ok=time_ok=status_ok=0
 tool_total=tool_visible=llm_total=llm_visible=err_total=err_visible=token_total=token_visible=0
 trace_ids=set(); span_ids_by_trace={}; parents=[]; task_ids_in_trace=set()
 with open(args.trace_jsonl,encoding='utf-8') as f:
  for line in f:
   if not line.strip(): continue
   total+=1
   try: s=json.loads(line); parse_ok+=1
   except Exception: continue
   if all(k in s for k in REQUIRED): req_ok+=1
   attrs=s.get('attributes') or {}
   if attrs.get('inference.export.schema_version')==1: schema_ok+=1
   if attrs.get('inference.project_id'): project_ok+=1
   obs=attrs.get('inference.observation_kind')
   if obs in KINDS: kind_ok+=1
   if attrs.get(args.task_id_attr): task_ids_in_trace.add(str(attrs.get(args.task_id_attr)))
   tid=s.get('trace_id'); sid=s.get('span_id'); pid=s.get('parent_span_id')
   if tid and sid: trace_ids.add(tid); span_ids_by_trace.setdefault(tid,set()).add(sid); parents.append((tid,pid))
   st=parse_time(s.get('start_time')); et=parse_time(s.get('end_time'))
   if st and et and st<=et: time_ok+=1
   status=s.get('status') or {}
   if 'code' in status: status_ok+=1
   if obs=='TOOL':
    tool_total+=1
    if attrs.get('tool.name') and (attrs.get('input.value') is not None or attrs.get('tool.parameters') is not None): tool_visible+=1
   if obs=='LLM':
    llm_total+=1
    if (attrs.get('llm.model_name') or attrs.get('inference.llm.model_name')) and (attrs.get('llm.input_messages') is not None or attrs.get('llm.output_messages') is not None): llm_visible+=1
    token_total+=1
    if any(k in attrs for k in ['llm.token_count.prompt','llm.token_count.completion','inference.llm.input_tokens','inference.llm.output_tokens']): token_visible+=1
   code=str(status.get('code','')).upper()
   if code in {'ERROR','STATUS_CODE_ERROR','2'}:
    err_total+=1
    if status.get('message') or attrs.get('error.message') or attrs.get('output.value'): err_visible+=1
 for tid,pid in parents:
  if not pid or pid in span_ids_by_trace.get(tid,set()): parent_ok+=1
 def ratio(n,d,required=False):
  if d==0: return 0.0 if required else 1.0
  return n/d
 task_count=None; join=0.0; missing=[]
 if not args.task_manifest and not args.dev_allow_missing_gates:
  print(json.dumps({'decision':'fail','failures':['missing_task_manifest']})); sys.exit(2)
 if args.task_manifest:
  tasks=[]
  with open(args.task_manifest) as f:
   for line in f:
    if line.strip(): tasks.append(json.loads(line)['task_id'])
  task_count=len(tasks); missing=[t for t in tasks if t not in task_ids_in_trace]; join=1-len(missing)/task_count if task_count else 1.0
 redaction_decision='not_provided'
 if not args.redaction_report and not args.dev_allow_missing_gates:
  print(json.dumps({'decision':'fail','failures':['missing_redaction_report']})); sys.exit(2)
 if args.redaction_report:
  redaction_decision=load_json(args.redaction_report).get('decision','quarantine')
 checks={'json_parse_success':ratio(parse_ok,total,True),'required_fields':ratio(req_ok,total,True),'schema_version':ratio(schema_ok,total,True),'project_id':ratio(project_ok,total,True),'observation_kind':ratio(kind_ok,total,True),'parent_links':ratio(parent_ok,len(parents),True),'timestamps':ratio(time_ok,total,True),'status_code':ratio(status_ok,total,True),'task_trace_join':join,'tool_reconstruction':ratio(tool_visible,tool_total,args.requires_tools),'llm_visibility':ratio(llm_visible,llm_total,args.requires_llm),'error_visibility':ratio(err_visible,err_total,args.requires_errors),'token_visibility':ratio(token_visible,token_total,args.requires_cost)}
 thresholds={'json_parse_success':1,'required_fields':1,'schema_version':1,'project_id':1,'observation_kind':1,'parent_links':0.99,'timestamps':0.995,'status_code':1,'task_trace_join':0.98,'tool_reconstruction':0.95,'llm_visibility':0.95,'error_visibility':0.95,'token_visibility':0.90}
 failures=[k for k,t in thresholds.items() if checks[k]<t]
 if redaction_decision=='quarantine': failures.append('redaction_quarantine')
 if redaction_decision=='not_provided' and not args.dev_allow_missing_gates: failures.append('redaction_not_provided')
 decision='quarantine' if redaction_decision=='quarantine' else ('pass' if not failures else 'fail')
 out={'corpus_id':args.corpus_id,'trace_file_sha256':sha256(args.trace_jsonl),'span_count':total,'trace_count':len(trace_ids),'task_count':task_count,'checks':checks,'failures':failures,'excluded_tasks':missing,'redaction_decision':redaction_decision,'decision':decision}
 open(args.output,'w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); sys.exit(0 if decision=='pass' else 2)
if __name__=='__main__': main()
