import re,json,math,csv
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.spatial.transform import Rotation
src=Path(__file__).resolve().parent
dest=src/'dados'/'reanalise_atualizada'
dest.mkdir(parents=True,exist_ok=True)
text=(src/'dados'/'dados_ensaios_sem_offset_e_com_offset_atualizados.txt').read_text(encoding='utf-8')
refs={1:(0,44.5),2:(21.894683863749513,36.42270486767261),3:(-21.894683863749513,36.42270486767261),4:(15.856985171011985,40.14022924062759),5:(-15.856985171011985,40.14022924062759),6:(32.77046177574005,12.073969712740638),7:(-32.77046177574005,12.073969712740638)}
betas={1:(0,0,0),2:(20,20,20),3:(-20,-20,-20),4:(10,20,15),5:(-10,-20,-15),6:(45,45,45),7:(-45,-45,-45)}
def fwd(pos,g=1):
    a=0;x=0;y=1.5
    for b in betas[pos]:
      for _ in range(3):
        a+=math.radians(g*b/3);x+=5*math.sin(a);y+=5*math.cos(a)
    return np.array([x-2*math.sin(a),y-2*math.cos(a)])
assert max(np.linalg.norm(fwd(p)-refs[p]) for p in refs)<.001
raw={}
for condition in ('SEM OFFSETS','COM OFFSETS'):
    sec=text.split(condition+' — 5 BATERIAS',1)[1].split('==================================================================================================================',2)[1] # maybe
    if condition=='SEM OFFSETS':sec=sec.split('COM OFFSETS — 5 BATERIAS',1)[0]
    batches={i:{} for i in range(1,6)}
    for line in sec.splitlines():
       m=re.match(r'^(Centro inicial|Posição [2-7]|Retorno de [2-7])\s+(.*)$',line.strip())
       if not m:continue
       key,remaining=m.groups(); nums=[float(s.replace(',','.')) for s in re.findall(r'(?<!\w)-?\d+[,.]\d+',remaining)]
       # 2 reference coordinates + 6 measurements or 4; determine table block by header position
       if len(nums) not in (6,8):continue
       offset=1 if len(nums)==8 else 4
       for j in range((len(nums)-2)//2):batches[offset+j][key]=np.array(nums[2+2*j:4+2*j],dtype=float)
    for i in range(1,6):
       if len(batches[i])!=13: raise ValueError((condition,i,len(batches[i]),batches[i]))
    raw['sem' if condition=='SEM OFFSETS' else 'com']=batches
print('Parsed',[(k,[len(b) for b in v.values()]) for k,v in raw.items()])
poses=list(range(2,8)); tgt=np.array([fwd(p)-fwd(1) for p in poses]); targetAbs=np.array([fwd(p) for p in poses])
def arrays(cond,chosen=None):
 b=raw[cond];chosen=chosen or list(range(1,6)); M=np.array([[b[i][f'Posição {p}'] for p in poses] for i in chosen]);init=np.array([b[i]['Centro inicial'] for i in chosen]);P=M-init[:,None,:];return P,M,init

def applyrot(P,theta):
 c,s=np.cos(theta),np.sin(theta);R=np.array([[c,-s],[s,c]])
 return P@R

def fitrot(P,Q,keep=None):
 if keep is not None:P=P[:,keep];Q=Q[keep]
 out=minimize_scalar(lambda t:np.sum((applyrot(P,t)-Q)**2),bounds=(-.2,.2),method='bounded',options={'xatol':1e-12})
 return float(out.x)

def fitjoint(P,keep=None):
 if keep is None:keep=np.arange(6)
 def obj(v):
  t,g=v;Q=np.array([fwd(poses[i],g)-fwd(1,g) for i in keep]);return float(np.sum((applyrot(P[:,keep],t)-Q)**2))
 best=None
 for guess in [(0,1),(0,.6),(0,1.4),(-.15,1.2),(.15,.8)]:
  a=minimize(obj,guess,method='L-BFGS-B',bounds=[(-.2,.2),(.5,1.5)],options={'ftol':1e-13,'maxiter':500})
  if best is None or a.fun<best.fun:best=a
 return float(best.x[0]),float(best.x[1])

def score(P,Q):return float(np.linalg.norm(P-Q,axis=-1).mean())
results={};errors={}
for condition in ['sem','com']:
 P,M,init=arrays(condition);theta=fitrot(P,tgt); t2,g=fitjoint(P)
 rot=applyrot(P,theta);jointTarget=np.array([fwd(p,g)-fwd(1,g) for p in poses]);jointResidual=applyrot(P,t2)-jointTarget
 looR=np.zeros((5,6));looG=np.zeros((5,6));lootheta=[];loog=[]
 for withheld in range(6):
  keep=[i for i in range(6) if i!=withheld];th=fitrot(P,tgt,keep);thg,gg=fitjoint(P,keep)
  looR[:,withheld]=np.linalg.norm(applyrot(P[:,withheld:withheld+1],th)-tgt[withheld],axis=-1).ravel()
  looG[:,withheld]=np.linalg.norm(applyrot(P[:,withheld:withheld+1],thg)-(fwd(poses[withheld],gg)-fwd(1,gg)),axis=-1).ravel()
  lootTheta=math.degrees(th);lootheta.append(lootTheta);loog.append(gg)
 absErr=np.linalg.norm(M-targetAbs,axis=-1);relative=np.linalg.norm(P-tgt,axis=-1)
 results[condition]={'angle_rotation_deg':math.degrees(theta),'angle_joint_deg':math.degrees(t2),'joint_gain_g':g,'relative_nominal':float(relative.mean()),'relative_rot_fit':score(rot,tgt),'relative_joint_fit':float(np.linalg.norm(jointResidual,axis=-1).mean()),'LOO_rotation':float(looR.mean()),'LOO_rotation_gain':float(looG.mean()),'absolute_mean':float(absErr.mean()),'rmse_absolute':float(np.sqrt(np.square(absErr).mean())),'per_pose_nominal':relative.mean(axis=0).tolist(),'per_pose_rotation':np.linalg.norm(rot-tgt,axis=-1).mean(axis=0).tolist(),'per_pose_loog':looG.mean(axis=0).tolist(),'loo_gain_folds':loog,'loo_rotation_folds_deg':lootheta}
 errors[condition]={'absolute':absErr,'relative':relative,'rotation':np.linalg.norm(rot-tgt,axis=-1),'joint':np.linalg.norm(jointResidual,axis=-1),'loo_rotation':looR,'loo_joint':looG}
 print(condition,results[condition])
# Bootstrap 10000 battery resamples PER condition; reestimate rotation for each replicate, and empirical relative/abs error
rng=np.random.default_rng(20261122);B=10000
boot={c:{'absolute':np.empty(B),'relative':np.empty(B),'rotation':np.empty(B)} for c in ('sem','com')}
for c in boot:
 P,M,_=arrays(c)
 for r in range(B):
  ix=rng.integers(0,5,5);sP=P[ix];sM=M[ix];boot[c]['absolute'][r]=np.linalg.norm(sM-targetAbs,axis=-1).mean();boot[c]['relative'][r]=np.linalg.norm(sP-tgt,axis=-1).mean();theta=fitrot(sP,tgt);boot[c]['rotation'][r]=np.linalg.norm(applyrot(sP,theta)-tgt,axis=-1).mean()
bootSummary={}
for metric in ['absolute','relative','rotation']:
 vals=boot['sem'][metric]-boot['com'][metric];b0=boot['sem'][metric];b1=boot['com'][metric];red=100*vals/b0
 bootSummary[metric]={'sem_mean':float(b0.mean()),'com_mean':float(b1.mean()),'diff_observed':results['sem']['relative_rot_fit' if metric=='rotation' else ('relative_nominal' if metric=='relative' else 'absolute_mean')]-results['com']['relative_rot_fit' if metric=='rotation' else ('relative_nominal' if metric=='relative' else 'absolute_mean')],'CI95_difference':np.quantile(vals,[.025,.975]).tolist(),'CI95_reduction_pct':np.quantile(red,[.025,.975]).tolist(),'fraction_non_positive':float(np.mean(vals<=0))}
print('BOOT',bootSummary)
# csv per pose, each condition
with open(dest/'erros_por_leitura.csv','w',newline='') as fh:
 w=csv.writer(fh);w.writerow(['condicao','bateria','posicao','X_medido','Y_medido','X_ref','Y_ref','erro_absoluto','erro_relativo','erro_apos_rotacao','erro_LOO_rotacao','erro_LOO_rotacao_g'])
 for c in ['sem','com']:
  _,M,_=arrays(c)
  for bi in range(5):
   for pi,p in enumerate(poses):w.writerow([c,bi+1,p,*M[bi,pi],*targetAbs[pi],*[errors[c][k][bi,pi] for k in ['absolute','relative','rotation','loo_rotation','loo_joint']]])
with open(dest/'resultados_reanalise.json','w') as fh:json.dump({'method':'P measured minus battery initial, target target(p)-target(1); row vector rotation R=[[cos,-sin],[sin,cos]], P@R; gain scales 3 segment flexions before forward kinematics; leave one position all 5 battery rows withheld; bootstrap 10000 independently by complete battery','geometry':'b15mm, 9x50mm, marker minus20mm from physical tip; straight 445mm','results':results,'bootstrap':bootSummary},fh,indent=2,ensure_ascii=False)
# calc tex
fmt=lambda a:f'{a:.2f}'.replace('.',',')
lines=[r'\clearpage\refstepcounter{chapter}',r'\chapter*{Apêndice \thechapter{} - Resultados detalhados da reanálise}',r'\addcontentsline{toc}{chapter}{Apêndice \thechapter{} - Resultados detalhados da reanálise}',r'\label{ap:detalhes_reanalise}',r'\section{Definição do ajuste e do conjunto de avaliação}',
'As análises utilizam os 30 pontos das posições 2 a 7 por condição (cinco baterias de seis posições), tomando como origem relativa o centro inicial da própria bateria. Os retornos foram reservados à análise de retorno. As posições de calibração dos offsets coincidem parcialmente com as de avaliação. As referências geométricas seguem o marcador a 445~mm, sem alteração das coordenadas experimentais definitivas.',
r'Os vetores são $\mathbf P_{bp}=\mathbf p_{m,bp}-\mathbf p_{m,b1}$ e $\mathbf Q_p=\mathbf p_{t,p}-\mathbf p_{t,1}$. A rotação única por condição minimiza $\sum_{b,p}\|\mathbf P_{bp}R(\theta)-\mathbf Q_p\|^2$, impondo uma rotação própria no plano, com $-0{,}2\leq\theta\leq0{,}2$ rad. O ganho escalar $g$ atua nas três flexões por $\boldsymbol\beta_{\mathrm{ef}}=g\boldsymbol\beta$, antes da cinemática direta, com $0{,}5\leq g\leq 1{,}5$. A otimização conjunta minimiza a mesma soma de quadrados, com alvos $\mathbf Q_p(g)$.',
r'\section{Resultados do ajuste e da validação cruzada}',r'\begin{table}[H]\centering',r'\caption{Erros planares médios de ajuste e validação cruzada por condição (cm)}\label{tab:reanalise-definitiva}',r'\small\begin{tabular}{lrr}\toprule',r'Indicador & Sem offsets & Com offsets\\\midrule']
for name,key in [('Nominal relativo ao centro','relative_nominal'),('Após rotação, nos dados ajustados','relative_rot_fit'),('Rotação, validação leave-one-out','LOO_rotation'),('Rotação e ganho, nos dados ajustados','relative_joint_fit'),('Rotação e ganho, leave-one-out','LOO_rotation_gain')]:lines.append(f'{name} & {fmt(results["sem"][key])} & {fmt(results["com"][key])}'+r'\\')
lines +=[r'\bottomrule\end{tabular}',r'\par\smallskip{\footnotesize Fonte: recálculo a partir das cinco baterias definitivas por condição; cada posição retida na validação foi excluída do ajuste nas cinco baterias.}',r'\end{table}']
for c,label in [('sem','sem offsets'),('com','com offsets')]:
 d=results[c];lines.append('Na condição '+label+', a rotação estimada nos próprios dados foi de '+fmt(d['angle_rotation_deg'])+'$^\\circ$. O ajuste conjunto de rotação e ganho produziu rotação de '+fmt(d['angle_joint_deg'])+'$^\\circ$ e $g='+fmt(d['joint_gain_g'])+'$.')
lines +=[r'A validação \textit{leave-one-out} foi feita por posição: em cada uma das seis rodadas excluíram-se as cinco leituras da posição retida, estimaram-se os parâmetros nas outras cinco posições e avaliou-se exclusivamente a posição excluída. O ponto inicial foi usado somente para definir os deslocamentos relativos. O procedimento avalia transferência entre as posições já estudadas, não generalização a configurações novas nem a validade independente dos offsets.',r'\section{Bootstrap por bateria}',r'Foram produzidas 10.000 réplicas com semente 20261122, amostrando cinco baterias completas com reposição, independentemente em cada condição. Na comparação após rotação, a rotação foi reestimada a cada réplica. Os intervalos percentis de 95\% são descritivos e não capturam erros sistemáticos na origem, alinhamento ou seleção prévia dos offsets.',r'\begin{table}[H]\centering',r'\caption{Redução do erro sem menos com offsets, por indicador, com bootstrap por bateria}\label{tab:bootstrap-definitivo}',r'\small\begin{tabular}{lrrr}\toprule',r'Indicador & Redução observada (cm) & IC 95\% (cm) & IC 95\% (\%)\\\midrule']
for label,key in [('Absoluto calculado','absolute'),('Relativo ao centro','relative'),('Relativo após rotação ajustada','rotation')]:
 d=bootSummary[key];ci=d['CI95_difference'];pr=d['CI95_reduction_pct'];lines.append(f'{label} & {fmt(d["diff_observed"])} & [{fmt(ci[0])}; {fmt(ci[1])}] & [{fmt(pr[0])}; {fmt(pr[1])}]'+r'\\')
lines +=[r'\bottomrule\end{tabular}\end{table}',r'O erro absoluto depende da correspondência entre as origens experimental e teórica, que foi declarada pelo autor como mantida. O ganho ajustado com offsets incorpora seu efeito e não representa identificação independente de parâmetros da transmissão. A reamostragem não corrige a reutilização das posições de calibração na avaliação.',r'\section{Reprodutibilidade}',r'O arquivo \texttt{dados/reanalise\_atualizada/resultados\_reanalise.json} contém os parâmetros e indicadores não arredondados; \texttt{erros\_por\_leitura.csv} permite auditar as 60 observações. O script \texttt{reanalisar\_definitivos.py} executa toda a reanálise.']
(src/'apendice_detalhes_reanalise.tex').write_text('\n'.join(lines)+'\n')
# report
with open(dest/'RELATORIO.md','w') as fh:
 fh.write('# Reanálise estatística final\n\nDados definitivos confirmados pelo autor; mesma origem física de referência declarada. Análise direta sobre 30 leituras por condição, marcador em 445 mm.\n\n')
 for c in ('sem','com'):
  fh.write('## '+c+' offsets\n')
  for k,v in results[c].items():
   if not isinstance(v,list):fh.write(f'- {k}: {v:.6f}\n')
 fh.write('\n## Bootstrap\n')
 for k,v in bootSummary.items():fh.write(f'- {k}: {v}\n')
 fh.write('\n## Limitações\nOffsets selecionados em posições também avaliadas; leave-one-out retém os offsets, e assim valida somente rotação/g, não offsets. Amostra de 5 baterias por condição; bootstrap independente de condições, e diferenças sistemáticas não representadas.\n')
