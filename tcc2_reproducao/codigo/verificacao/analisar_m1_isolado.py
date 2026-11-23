"""Reproduz os indicadores do ensaio complementar. Nao altera a campanha original."""
from pathlib import Path
import json
import math
import statistics as st

r=Path(__file__).resolve().parents[2]
out=r/'dados/m1_isolado'
d=json.loads((out/'leituras.json').read_text(encoding='utf8'))
f=lambda x: f'{x:.2f}'.replace('.',',')
stats={}
lines=[r'\begin{table}[H]\centering',
       r'\caption{Leituras do teste isolado de M1 (cm)}\label{tab:m1-leituras}',
       r'\small\begin{tabular}{ccrrrrrr}\toprule',
       r'Comando & Ciclo & $X_i$ & $Y_i$ & $X_f$ & $Y_f$ & $X_r$ & $Y_r$\\\midrule']
for key,sign in [('positivo',65),('negativo',-65)]:
    a=d[key]
    starts=[a['inicio']]+a['retornos'][:-1]
    shifts=[]
    norms=[]
    return_norms=[]
    for i,(start,final,ret) in enumerate(zip(starts,a['finais'],a['retornos']),1):
        delta=[v-u for u,v in zip(start,final)]
        shifts.append(delta)
        norms.append(math.dist(start,final))
        return_norms.append(math.dist(start,ret))
        lines.append(f'{sign:+d} & {i} & '+' & '.join(f(v) for xy in [start,final,ret] for v in xy)+r'\\')
    stats[key]=dict(delta_x_medio=st.mean(v[0] for v in shifts),delta_y_medio=st.mean(v[1] for v in shifts),distancia_media=st.mean(norms),desvio_final_serie=math.dist(a['inicio'],a['retornos'][-1]),deslocamentos=shifts,distancias=norms,retorno_por_ciclo=return_norms)
lines += [r'\bottomrule\end{tabular}\par\smallskip',r'{\footnotesize Fonte: Registros do autor. $i$: início da ida; $f$: final; $r$: retorno. Nos ciclos 2 e 3, o início corresponde ao retorno anterior.}\end{table}']
lines += [r'\begin{table}[H]\centering',r'\caption{Deslocamento da ponta por ida no teste isolado de M1 (cm)}\label{tab:m1-deslocamento}',r'\small\begin{tabular}{crrr}\toprule Comando & Média $\Delta X$ & Média $\Delta Y$ & Média $\|\Delta\boldsymbol p\|$\\\midrule']
for key,sign in [('positivo',65),('negativo',-65)]:
    s=stats[key]
    lines.append(f'{sign:+d} & '+' & '.join(f(s[k]) for k in ['delta_x_medio','delta_y_medio','distancia_media'])+r'\\')
lines += [r'\bottomrule\end{tabular}\par\smallskip',r'{\footnotesize Fonte: Elaborado pelo autor. A distância é a norma entre início e fim de cada ida, não o comprimento da trajetória.}\end{table}']
(out/'resultados.tex').write_text('\n'.join(lines)+'\n',encoding='utf8')
(out/'estatisticas.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
assert sum(d['blocos_pulsos'])==65
for key in ['positivo','negativo']:
    assert len(d[key]['finais']) == len(d[key]['retornos']) == 3
    assert len(d[key]['inicio']) == 2
    assert all(math.isfinite(v) for xy in d[key]['finais']+d[key]['retornos'] for v in xy)
    assert all(v >= 0 for v in stats[key]['distancias']+stats[key]['retorno_por_ciclo'])
print(json.dumps(stats,ensure_ascii=False,indent=2))
