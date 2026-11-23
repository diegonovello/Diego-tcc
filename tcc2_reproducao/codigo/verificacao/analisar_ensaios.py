from pathlib import Path
import json,math,statistics as st,csv
r=Path(__file__).resolve().parents[2]
d=json.loads((r/'dados/ensaios_posicionamento_cm.json').read_text(encoding='utf8'))
f=lambda x,n=2: f'{x:.{n}f}'.replace('.',',')
out=[];stats={}
for key in ['sem_ajuste','com_ajuste']:
 a=d[key];rows=[];allerr=[]
 for p in range(2,8):
  pts=a[2*p-3];t=d['teorico'][p-1];err=[math.dist(v,t) for v in pts];allerr+=err
  mean=[st.mean(v[j] for v in pts) for j in range(2)]
  rows.append(dict(posicao=p,erro_medio=st.mean(err),erro_dp=st.stdev(err),erro_max=max(err),x_medio=mean[0],y_medio=mean[1],sx=st.stdev(v[0] for v in pts),sy=st.stdev(v[1] for v in pts),raio_max_centroide=max(math.dist(v,mean) for v in pts)))
 ret=[math.dist(a[i][k],a[0][k]) for i in range(2,13,2) for k in range(5)]
 axis_errors=[(v[0]-d['teorico'][p-1][0],v[1]-d['teorico'][p-1][1]) for p in range(2,8) for v in a[2*p-3]]
 stats[key]={'posicoes':rows,'erro_medio_global':st.mean(allerr),
  'rmse_planar':math.sqrt(st.mean(e*e for e in allerr)),
  'vies_x_global':st.mean(e[0] for e in axis_errors),
  'vies_y_global':st.mean(e[1] for e in axis_errors),
  'retorno_medio':st.mean(ret),'retorno_max':max(ret)}
assert sum(len(d[k])*5 for k in ['sem_ajuste','com_ajuste'])==130
(r/'dados/estatisticas_ensaios.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
with (r/'dados/ensaios_posicionamento_cm.csv').open('w',newline='',encoding='utf-8-sig') as fi:
 w=csv.writer(fi,delimiter=';');w.writerow(['condicao','bateria','ordem','posicao','x_cm','y_cm'])
 for k in stats:
  for i,row in enumerate(d[k]):
   for j,(x,y) in enumerate(row):w.writerow([k,j+1,i+1,d['sequencia'][i],f(x),f(y)])
out.append(r'\subsection{Comparação do erro de posicionamento}')
out.append('Os alvos teóricos foram expressos em centímetros e usados com a mesma precisão numérica nas duas condições. A Tabela~\\ref{tab:erros-medidos} apresenta a média dos cinco erros individuais da Eq.~\\eqref{eq:erro-posicionamento-experimental} e seu desvio-padrão amostral (DP). O DP descreve a dispersão dos erros entre as cinco baterias. Na coluna de variação, valores positivos indicam redução do erro com offsets e valores negativos indicam aumento.')
out.append(r'\begin{table}[H]\centering\caption{Erro planar por posição, em cm (cinco leituras por condição)}\label{tab:erros-medidos}\small\begin{tabular}{crrr}\toprule Posição & Sem ajuste: média (DP) & Com ajuste: média (DP) & Variação (\%)\\\midrule')
for a,b in zip(stats['sem_ajuste']['posicoes'],stats['com_ajuste']['posicoes']):
 out.append(f"{a['posicao']} & {f(a['erro_medio'])} ({f(a['erro_dp'])}) & {f(b['erro_medio'])} ({f(b['erro_dp'])}) & {f(100*(1-b['erro_medio']/a['erro_medio']),1)}"+r'\\')
out.append(r'\bottomrule\end{tabular}\par\smallskip{\footnotesize Fonte: Elaborado pelo autor a partir dos registros dos ensaios.}\end{table}')
a,b=stats['sem_ajuste'],stats['com_ajuste']
change=100*abs(1-b['erro_medio_global']/a['erro_medio_global'])
direction='redução' if b['erro_medio_global'] < a['erro_medio_global'] else 'aumento'
out.append(f"Considerando as posições 2 a 7, são 30 leituras por condição. O erro médio foi de {f(a['erro_medio_global'])} cm sem ajuste e {f(b['erro_medio_global'])} cm com ajuste, {direction} descritiva de {f(change,1)}\\%. Essa comparação não isola a influência do reposicionamento inicial, do alinhamento, do tensionamento e da leitura. Os offsets foram selecionados em cinco tentativas qualitativas na posição 6 e cinco na posição 7, sem critério numérico documentado. Essas posições também entram na média de avaliação; portanto, a campanha não constitui uma validação independente em novas configurações.")
out.append(f"Sobre as mesmas 30 leituras, o RMSE planar foi de {f(a['rmse_planar'])} cm sem offsets e {f(b['rmse_planar'])} cm com offsets. Os vieses globais $(\\overline e_X;\\overline e_Y)$ foram $({f(a['vies_x_global'])};{f(a['vies_y_global'])})$ cm e $({f(b['vies_x_global'])};{f(b['vies_y_global'])})$ cm, respectivamente. Esses valores agregados complementam, mas não substituem, a análise por posição.")
out.append('Os ensaios independentes nas configurações $(15^\\circ,15^\\circ,15^\\circ)$ e $(30^\\circ,10^\\circ,-10^\\circ)$ não foram realizados. Essas configurações são propostas para uma campanha futura; não há erros experimentais a relatar para elas.')
out.append(r'\subsection{Exatidão de posicionamento e repetibilidade}')
out.append(r'\input{indicadores_ap_rp}')
out.append('Como informação complementar, a Tabela~\\ref{tab:dispersao-medida} apresenta os desvios-padrão por eixo. Eles não equivalem ao indicador RP, que utiliza as distâncias individuais ao baricentro.')
out.append(r'\begin{table}[H]\centering\caption{Dispersão amostral das coordenadas entre baterias, em cm}\label{tab:dispersao-medida}\small\begin{tabular}{crrrr}\toprule & \multicolumn{2}{c}{Sem ajuste} & \multicolumn{2}{c}{Com ajuste}\\ Posição & $s_X$ & $s_Y$ & $s_X$ & $s_Y$\\\midrule')
for a,b in zip(stats['sem_ajuste']['posicoes'],stats['com_ajuste']['posicoes']):out.append(f"{a['posicao']} & {f(a['sx'])} & {f(a['sy'])} & {f(b['sx'])} & {f(b['sy'])}"+r'\\')
out.append(r'\bottomrule\end{tabular}\par\smallskip{\footnotesize Fonte: Elaborado pelo autor a partir dos registros dos ensaios.}\end{table}')
out.append('A dispersão entre baterias inclui o reposicionamento manual, a variação dos movimentos e a leitura. Ela caracteriza a consistência do procedimento completo, sem constituir uma medida isolada da repetibilidade mecânica.')
a,b=stats['sem_ajuste'],stats['com_ajuste']
out.append(f"Nos 30 retornos de cada condição, a distância ao centro inicial da própria bateria apresentou média de {f(a['retorno_medio'])} cm e máximo de {f(a['retorno_max'])} cm sem ajuste; com ajuste, média de {f(b['retorno_medio'])} cm e máximo de {f(b['retorno_max'])} cm. Houve variações tanto em X quanto em Y. Esses desvios devem ser distinguidos do afastamento do centro inicial em relação ao alvo (0;44,5) cm.")
appendix_start = len(out)
for key,title in [('sem_ajuste','sem ajuste'),('com_ajuste','com ajuste')]:
 out.append(r'\clearpage\subsection{Coordenadas medidas '+title+'}')
 out.append(r'Na Tabela~\ref{tab:leituras-'+key+r'}, as referências e as leituras de X e Y estão em centímetros. O centro inicial foi medido após o reposicionamento manual; os retornos à posição 1 foram medidos sem novo ajuste manual durante a bateria.')
 out.append(r'\begin{table}[H]\centering\caption{Referências e coordenadas medidas '+title+r' (cm)}\label{tab:leituras-'+key+r'}\begingroup\footnotesize\renewcommand{\arraystretch}{1.16}\setlength{\tabcolsep}{6pt}')
 for group in [[0,1,2],[3,4]]:
  cols=2+len(group)*2
  out.append(r'\begin{tabular}{@{}l'+('r'*cols)+r'@{}}\toprule')
  out.append(r' & \multicolumn{2}{c}{Referência} & '+' & '.join(r'\multicolumn{2}{c}{Bateria '+str(k+1)+'}' for k in group)+r'\\')
  out.append(''.join(r'\cmidrule(lr){'+str(2+2*j)+'-'+str(3+2*j)+'}' for j in range(len(group)+1)))
  out.append('Etapa & '+' & '.join(['X','Y']*(len(group)+1))+r'\\\midrule')
  for i,row in enumerate(d[key]):
   pos=d['sequencia'][i]
   label='Centro inicial' if i==0 else r'\textbf{Posição '+str(pos)+'}' if i%2 else 'Retorno de '+str(d['sequencia'][i-1])
   ref=d['teorico'][pos-1]
   out.append(label+' & '+' & '.join([f(v,3) for v in ref]+[f(v) for k in group for v in row[k]])+r'\\')
   if i%2==0 and i<12:out.append(r'\addlinespace[2pt]')
  out.append(r'\bottomrule\end{tabular}')
  if len(group)==3:out.append(r'\par\vspace{12pt}')
 out.append(r'\endgroup\par\smallskip{\footnotesize Fonte: registros do autor. Todos os retornos têm como destino a posição 1.}\end{table}')
(r/'dados/resultados_medidos.tex').write_text('\n\n'.join(out[:appendix_start])+'\n',encoding='utf8')
(r/'dados/leituras_apendice.tex').write_text('\n\n'.join(out[appendix_start:]).replace(r'\clearpage\subsection',r'\clearpage\section').replace(r'\clearpage', '', 1)+'\n',encoding='utf8')
