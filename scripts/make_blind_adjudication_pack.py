#!/usr/bin/env python3
import argparse,json,hashlib,random,re,shutil
from pathlib import Path
LABELS=[r'baseline',r'generic[_ -]?debugging',r'halo[_ -]?candidate',r'HALO',r'Baseline',r'Generic Debugging']
def scrub(txt):
 for pat in LABELS: txt=re.sub(pat,'[MODE]',txt,flags=re.I)
 return txt
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('runs_dir'); ap.add_argument('--output-dir',default='adjudication_pack'); ap.add_argument('--mapping-output',default='PRIVATE_adjudication_mapping.json'); ap.add_argument('--seed',type=int,default=3907); args=ap.parse_args()
 rng=random.Random(args.seed); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); mapping=[]
 for run in sorted(Path(args.runs_dir).glob('*')):
  if not run.is_dir(): continue
  anon='case_'+hashlib.sha256((run.name+str(rng.random())).encode()).hexdigest()[:10]
  dest=out/anon; dest.mkdir(exist_ok=True)
  for fname in ['diagnosis_report.md','patch.diff','eval_after.json','task_excerpt.md','trace_excerpt.md']:
   src=run/fname
   if src.exists():
    data=src.read_text(encoding='utf-8',errors='ignore')
    (dest/fname).write_text(scrub(data))
  mapping.append({'anon_id':anon,'run_dir':run.name})
 Path(args.mapping_output).write_text(json.dumps(mapping,indent=2))
 print(json.dumps({'cases':len(mapping),'output_dir':str(out),'private_mapping':args.mapping_output},indent=2))
if __name__=='__main__': main()
