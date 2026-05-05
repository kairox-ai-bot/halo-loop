#!/usr/bin/env python3
import argparse,json,glob,statistics,random,sys
MODES=['baseline','generic_debugging','halo_candidate']
def load(p):
 with open(p) as f: return json.load(f)
def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def percentile(xs,p):
 xs=sorted(xs)
 if not xs: return None
 k=(len(xs)-1)*p; lo=int(k); hi=min(lo+1,len(xs)-1); return xs[lo]*(hi-k)+xs[hi]*(k-lo)
def bootstrap_ci(pairs,reps=5000,seed=3907):
 rng=random.Random(seed); n=len(pairs); vals=[]
 if n==0: return [None,None]
 for _ in range(reps):
  sample=[pairs[rng.randrange(n)] for __ in range(n)]
  vals.append(mean([h-c for h,c in sample]))
 return [percentile(vals,0.025), percentile(vals,0.975)]
def load_tasks(path):
 tasks={}
 with open(path) as f:
  for line in f:
   if line.strip():
    o=json.loads(line); tasks[o['task_id']]=o
 return tasks
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('result_glob'); ap.add_argument('--task-manifest',required=True); ap.add_argument('--primary-partition',default='locked_realistic'); ap.add_argument('--output',default='aggregate_scores.json'); ap.add_argument('--min-delta',type=float,default=0.10); ap.add_argument('--max-regression-delta',type=float,default=0.05); ap.add_argument('--max-cost-delta',type=float,default=0.20); ap.add_argument('--min-powered-n',type=int,default=80); args=ap.parse_args()
 tasks=load_tasks(args.task_manifest)
 primary={tid:t for tid,t in tasks.items() if t.get('partition')==args.primary_partition}
 all_records=[load(p) for p in glob.glob(args.result_glob)]
 records=[]; excluded=[]; contaminated=[]
 for r in all_records:
  tid=r['task_id']
  if tid not in primary: continue
  if r.get('contaminated'): contaminated.append(r); continue
  if r.get('excluded'): excluded.append(r); continue
  r.setdefault('partition', tasks[tid].get('partition')); r.setdefault('harness',tasks[tid].get('harness'))
  records.append(r)
 by_mode={m:[r for r in records if r['mode']==m] for m in MODES}
 summary={}
 for m,rs in by_mode.items():
  costs=[r.get('cost_usd',0) for r in rs]
  summary[m]={'n':len(rs),'success_rate':mean([1 if r.get('success_after') else 0 for r in rs]),'regression_rate':mean([1 if r.get('regression_count',0)>0 else 0 for r in rs]),'median_cost_usd':statistics.median(costs) if costs else 0,'total_regressions':sum(r.get('regression_count',0) for r in rs)}
 controls=['baseline','generic_debugging']; stronger=max(controls,key=lambda m:summary[m]['success_rate'])
 idx={(r['task_id'],r.get('seed',0),r['mode']):r for r in records}
 pairs=[]; missing_pairs=[]
 for tid in primary:
  seeds={seed for (task,seed,mode) in idx if task==tid}
  for seed in seeds:
   h=idx.get((tid,seed,'halo_candidate')); c=idx.get((tid,seed,stronger))
   if h and c: pairs.append((1 if h.get('success_after') else 0, 1 if c.get('success_after') else 0))
   else: missing_pairs.append({'task_id':tid,'seed':seed})
 delta=mean([h-c for h,c in pairs]) if pairs else 0.0; ci=bootstrap_ci(pairs)
 halo=summary['halo_candidate']; ctrl=summary[stronger]
 reg_delta=halo['regression_rate']-ctrl['regression_rate']
 cost_delta=(halo['median_cost_usd']-ctrl['median_cost_usd'])/ctrl['median_cost_usd'] if ctrl['median_cost_usd']>0 else (0 if halo['median_cost_usd']==0 else 999)
 powered=len(pairs)>=args.min_powered_n
 hard_failures=[]
 if contaminated: hard_failures.append('contaminated_records')
 if missing_pairs: hard_failures.append('missing_pairs')
 if len(primary)<args.min_powered_n: hard_failures.append('insufficient_primary_manifest_n')
 production_pass=bool(not hard_failures and powered and delta>=args.min_delta and ci[0] is not None and ci[0]>0 and reg_delta<=args.max_regression_delta and (cost_delta<=args.max_cost_delta or delta>=0.15))
 research_only=bool(not hard_failures and (not powered) and delta>0 and reg_delta<=args.max_regression_delta and (cost_delta<=args.max_cost_delta or delta>=0.15))
 out={'primary_partition':args.primary_partition,'primary_task_count':len(primary),'summary':summary,'stronger_control':stronger,'paired_n':len(pairs),'powered':powered,'halo_vs_stronger_delta':delta,'bootstrap_95_ci':ci,'regression_rate_delta':reg_delta,'median_cost_delta':cost_delta,'excluded_count':len(excluded),'contaminated_count':len(contaminated),'missing_pairs':missing_pairs[:20],'hard_failures':hard_failures,'production_pass':production_pass,'research_only_support':research_only,'decision':'production_pass' if production_pass else ('research_only' if research_only else 'fail')}
 open(args.output,'w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); sys.exit(0 if production_pass or research_only else 2)
if __name__=='__main__': main()
