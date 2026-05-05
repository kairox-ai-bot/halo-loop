#!/usr/bin/env python3
import argparse, re, json, hashlib, sys
from pathlib import Path
PATTERNS={
 'openai_key': ('high', r'sk-[A-Za-z0-9_-]{20,}'),
 'github_token': ('high', r'gh[pousr]_[A-Za-z0-9_]{20,}'),
 'aws_access_key': ('high', r'AKIA[0-9A-Z]{16}'),
 'cookie_header': ('high', r'(?i)\bcookie\s*[:=]'),
 'password_assignment': ('high', r'(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;}]+'),
 'email': ('medium', r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
 'phone_us': ('medium', r'(?<!\d)(?:\+1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}(?!\d)')
}
def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
 return h.hexdigest()
def files(root):
 p=Path(root)
 return [p] if p.is_file() else [x for x in p.rglob('*') if x.is_file()]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('--output', default='redaction_scan.json'); ap.add_argument('--allow-medium', action='store_true'); args=ap.parse_args()
 findings=[]; scanned=[]
 for fp in files(args.path):
  scanned.append(str(fp))
  try: lines=fp.read_text(encoding='utf-8',errors='ignore').splitlines()
  except Exception: continue
  for i,line in enumerate(lines,1):
   for name,(sev,pat) in PATTERNS.items():
    if re.search(pat,line): findings.append({'file':str(fp),'line':i,'pattern':name,'severity':sev})
 high=sum(1 for f in findings if f['severity']=='high'); med=sum(1 for f in findings if f['severity']=='medium')
 decision='quarantine' if high or (med and not args.allow_medium) else 'pass'
 out={'root':args.path,'files_scanned':len(scanned),'findings':findings,'high_count':high,'medium_count':med,'decision':decision}
 out['root_sha256']=sha256(args.path) if Path(args.path).is_file() else None
 open(args.output,'w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); sys.exit(0 if decision=='pass' else 2)
if __name__=='__main__': main()
