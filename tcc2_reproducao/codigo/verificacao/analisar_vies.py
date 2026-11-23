from pathlib import Path
import json,math,statistics as st
from decimal import Decimal, ROUND_HALF_UP
r=Path(__file__).resolve().parents[2];d=json.loads((r/'dados/ensaios_posicionamento_cm.json').read_text(encoding='utf8'));f=lambda x:format(Decimal(str(round(x,10))).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP),'.2f').replace('.',',');out=[];allstats={}
for key,name in [('sem_ajuste','Sem ajuste'),('com_ajuste','Com ajuste')]:
 arr=d[key];rows=[];allrel=[]
 for p in range(2,8):
  pts=arr[2*p-3];t=d['teorico'][p-1];es=[[v[j]-t[j] for j in range(2)] for v in pts];rel=[[es[b][j]-(arr[0][b][j]-d['teorico'][0][j]) for j in range(2)] for b in range(5)];norm=[math.hypot(*v) for v in es];rn=[math.hypot(*v) for v in rel];allrel+=rn
  rows.append(dict(pos=p,bx=st.mean(v[0] for v in es),by=st.mean(v[1] for v in es),min=min(norm),max=max(norm),relative_mean=st.mean(rn),relative_bias_x=st.mean(v[0] for v in rel),relative_bias_y=st.mean(v[1] for v in rel)))
 allstats[key]={'rows':rows,'relative_mean':st.mean(allrel)}
 out.append(r'\begin{table}[H]\centering\caption{Viés e amplitude do erro: '+name.lower()+r', em cm}\label{tab:vies-'+key+r'}\small\begin{tabular}{crrrrr}\toprule Posição & Viés X & Viés Y & Erro mín. & Erro máx. & Erro relativo médio\\\midrule')
 for a in rows:out.append(str(a['pos'])+' & '+' & '.join(f(a[k]) for k in ['bx','by','min','max','relative_mean'])+r'\\')
 out.append(r'\bottomrule\end{tabular}\par\smallskip{\footnotesize Fonte: Elaborado pelo autor a partir dos registros dos ensaios.}\end{table}')
(r/'dados/discussao_estatisticas.tex').write_text('\n'.join(out),encoding='utf8');(r/'dados/estatisticas_relativas.json').write_text(json.dumps(allstats,indent=2),encoding='utf8');print('Médias relativas:',*[v['relative_mean'] for v in allstats.values()])
