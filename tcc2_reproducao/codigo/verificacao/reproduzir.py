"""Reprodução numérica da monografia. Unidades: mm e radianos.

Gera dados e figuras teóricas; não lê instrumentos nem envia comandos a motores.
Python 3.10+, NumPy e Matplotlib. Executar na pasta da monografia.
"""
from pathlib import Path
import json,math,csv,sys,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
PROFILE='original' if '--original' in sys.argv else 'fisico'
OUT=ROOT/('imagens/verificacao' if PROFILE=='original' else 'imagens/verificacao_dimensoes_fisicas')
DATA=ROOT/'codigo/verificacao'/('' if PROFILE=='original' else 'dimensoes_fisicas')
DATA.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True,exist_ok=True)
L=np.full(9,15.17) if PROFILE=="original" else np.full(9,50.)
D=18.98 if PROFILE=="original" else 21.5
R=15.;RATIO=4/3;NP=400
BASE=0. if PROFILE=="original" else 15.
TIP=0. if PROFILE=="original" else -20.
TOTAL=BASE+float(L.sum())+TIP
EFFECTIVE=L.copy();EFFECTIVE[-1]+=TIP
COLORS=['#007eaa','#d47700','#c62828']
TARGET=np.array([-62.39,115.51]) if PROFILE=="original" else np.array([158.56985171011988, 401.402292406276])
K=NP*RATIO/(2*np.pi*R)

def points(q):
 a=np.cumsum(q)
 return np.vstack(([0.,0.],np.cumsum(L[:,None]*np.column_stack((np.sin(a),np.cos(a))),axis=0)))+np.array([0.,BASE])
def fk(q):return points(q)[-1]+TIP*np.array([np.sin(np.sum(q)),np.cos(np.sum(q))])
def jac(q):
 a=np.cumsum(q)
 return np.array([[(EFFECTIVE[j:]*np.cos(a[j:])).sum() for j in range(9)],[-(EFFECTIVE[j:]*np.sin(a[j:])).sum() for j in range(9)]])
def solve(target,q0,group=False,tol=.01,maxiter=500):
 q=np.array(q0,dtype=float);limit=np.deg2rad(45 if group else 15);hist=[]
 for it in range(maxiter):
  joints=np.repeat(q/3,3) if group else q
  err=target-fk(joints);norm=float(np.linalg.norm(err));hist.append(norm)
  if norm<tol:return q,hist,it
  j=jac(joints)
  if group:j=j.reshape(2,3,3).sum(axis=2)/3
  dq=j.T@np.linalg.solve(j@j.T+.5**2*np.eye(2),err)
  scale=min(1.,np.deg2rad(5)/max(np.max(np.abs(dq)),1e-12))
  for _ in range(12):
   cand=np.clip(q+scale*dq,-limit,limit)
   trial=np.repeat(cand/3,3) if group else cand
   if np.linalg.norm(target-fk(trial))<norm:q=cand;break
   scale/=2
  else:raise RuntimeError('Sem redução do erro')
 raise RuntimeError('Limite de iterações atingido')

def baseplot():
 fig,ax=plt.subplots(figsize=(6.3,6.2),layout='constrained');ax.set(xlim=(-TOTAL,TOTAL),ylim=(-.04*TOTAL,1.08*TOTAL),xlabel='X (mm)',ylabel='Y (mm)');ax.set_aspect('equal');ax.grid(alpha=.22);ax.axvline(0,color='#888',lw=.6);ax.axhline(0,color='#888',lw=.6);return fig,ax
def chain(ax,q,label=True):
 ps=points(q)
 for g,col in enumerate(COLORS):ax.plot(ps[g*3:g*3+4,0],ps[g*3:g*3+4,1],'-o',color=col,lw=2.3,ms=4,label=f'Segmento {g+1}' if label else None)
 ax.plot([0,0],[0,BASE],color='#444444',lw=3)
 tip=fk(q);ax.plot([ps[-1,0],tip[0]],[ps[-1,1],tip[1]],color='#444444',lw=3)
 ax.plot(0,0,'^',color='black',ms=7);return ps
def save(fig,name):fig.savefig(OUT/(name+'.png'),dpi=200);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)

def main():
 q9,h9,it9=solve(TARGET,np.zeros(9))
 b7=solve(TARGET,np.deg2rad([-24,4,-42]),True,tol=1e-8,maxiter=300)[0] if PROFILE=='original' else np.zeros(3)
 assert max(abs(np.rad2deg(q9)))<=15
 assert max(abs(np.rad2deg(b7)))<=45
 # Derivadas independentes de funções e consistência de escala.
 rng=np.random.default_rng(42);diff=0
 for _ in range(30):
  q=rng.uniform(-np.pi/12,np.pi/12,9);eps=1e-6
  fd=np.column_stack([(fk(q+np.eye(9)[j]*eps)-fk(q-np.eye(9)[j]*eps))/(2*eps) for j in range(9)])
  diff=max(diff,float(np.max(np.abs(fd-jac(q)))))
  transform=np.eye(4);transform[1,3]=BASE
  for angle,length in zip(q,L):
   sn,cs=np.sin(angle),np.cos(angle)
   h=np.array([[cs,sn,0,length*sn],[-sn,cs,0,length*cs],[0,0,1,0],[0,0,0,1]])
   transform=transform@h
  terminal=np.eye(4);terminal[1,3]=TIP
  transform=transform@terminal
  assert np.allclose(transform[:2,3],fk(q),atol=1e-10)
 assert diff<1e-5
 cases=([np.array(a,float) for a in [(0,0,0),(20,20,20),(0,0,20),(10,20,15),(-10,-20,-15),(30,-10,20)]]+[np.rad2deg(b7)]) if PROFILE=='original' else [np.array(a,float) for a in [(0,0,0),(20,20,20),(-20,-20,-20),(10,20,15),(-10,-20,-15),(45,45,45),(-45,-45,-45)]]
 # Esquema dimensional reprodutivel, sem escala de fabricacao.
 fig,ax=plt.subplots(figsize=(9,2.5),layout='constrained')
 cumulative=BASE+np.r_[0,np.cumsum(L)]
 for g,col in enumerate(COLORS):
  x=cumulative[g*3:g*3+4]
  ax.plot(x,np.zeros(4),'-o',color=col,lw=4,ms=6)
  mid=(x[0]+x[-1])/2
  ax.text(mid,20,f'Segmento {g+1}: {x[-1]-x[0]:.0f} mm',ha='center',fontsize=11,color=col)
  ax.text(mid,-23,' + '.join(f'{v:.0f}' for v in L[g*3:g*3+3])+' mm',ha='center',fontsize=10)
 ax.plot([0,BASE],[0,0],color='#444444',lw=4)
 ax.plot([cumulative[-1],TOTAL],[0,0],color='#444444',lw=4)
 ax.text(0,33,f'Fixo: {BASE:.0f} mm',ha='left',fontsize=9)
 ax.text(TOTAL,33,f'Recuo do marcador: {-TIP:.0f} mm',ha='right',fontsize=9)
 for x in cumulative[[0,3,6,9]]:
  ax.text(x,-48,f'{x:.0f} mm',ha='center',fontsize=11)
 ax.text(0,45,'Saída dos cabos / origem',fontsize=10,ha='left')
 ax.text(TOTAL,45,f'Ponta física: {BASE+L.sum():.0f} mm; marcador: {TOTAL:.0f} mm',fontsize=10,ha='right')
 ax.set(xlim=(-15,BASE+L.sum()+15),ylim=(-65,60));ax.axis('off')
 save(fig,'dimensoes_equivalentes')
 records=[]
 for number,beta in enumerate(cases,1):
  q=np.repeat(np.deg2rad(beta)/3,3);target=fk(q);c=D*np.cumsum(np.deg2rad(beta));raw=K*c
  n=np.sign(raw)*np.floor(np.abs(raw)+.5);n=n.astype(int)
  rounded=n.copy()
  if PROFILE!='original':
   previous=0;limit=math.floor(K*D*np.pi/4)
   for motor in range(3):
    n[motor]=np.clip(n[motor],previous-limit,previous+limit);previous=int(n[motor])
  quant_beta=np.diff(np.r_[0,n/K])/D
  quant_error=float(np.linalg.norm(fk(np.repeat(quant_beta/3,3))-target))
  ik_attempts=[]
  for seed in [[0,0,0],[10,10,10],[-10,-10,-10],[30,30,30],[-30,-30,-30]]:
   try:
    sol,h,it=solve(target,np.deg2rad(seed),True,tol=.1,maxiter=300)
    ik_attempts.append(dict(semente=seed,convergiu=True));break
   except RuntimeError as exc:
    ik_attempts.append(dict(semente=seed,convergiu=False,motivo=str(exc)))
  else:raise RuntimeError(f'Caso {number}: nenhuma semente convergiu')
  records.append(dict(caso=number,beta=beta.tolist(),xy=target.tolist(),cabos=c.tolist(),pulsos=n.tolist(),pulsos_arredondados=rounded.tolist(),pulsos_m1_m2_m3=n[[2,0,1]].tolist(),erro_ik=h[-1],erro_quantizacao=quant_error,iteracoes=it,tentativas_ik=ik_attempts,solucao_ik_graus=np.rad2deg(sol).tolist()))
  fig,ax=baseplot();chain(ax,q);ax.plot(*target,'kx',ms=9);ax.set_title(f'Caso {number}: '+ '; '.join(f'{a:.3f}°' for a in beta)+'\n'+f'X={target[0]:.3f} mm; Y={target[1]:.3f} mm');ax.legend(loc='upper left',fontsize=8);save(fig,f'caso_{number:02d}')
 for name,q,title in [('modelo_nove_elos',q9,'Modelo de nove elos equivalentes'),('direta_verificada',q9,'Verificação direta da solução de nove juntas'),('inversa_inicial',np.zeros(9),'Configuração inicial: nove ângulos nulos'),('inversa_final',q9,'Solução inversa com limites de ±15° por junta')]:
  fig,ax=baseplot();chain(ax,q);ax.plot(*TARGET,'kx',ms=9,label='Referência geométrica');ax.set_title(title);ax.legend(fontsize=8);save(fig,name)
 fig,ax=plt.subplots(figsize=(6.5,3.3),layout='constrained');ax.semilogy(range(len(h9)),h9,'o-',color=COLORS[0]);ax.set(xlabel='Atualização do vetor de juntas',ylabel='Erro cartesiano (mm)',title='Convergência da solução de nove juntas');ax.grid(alpha=.25);save(fig,'convergencia_nove')
 # Espaço amostrado do modelo agrupado: não é uma identificação física.
 betas=np.stack(np.meshgrid(*([np.linspace(-45,45,25)]*3),indexing='ij'),axis=-1).reshape(-1,3)
 qs=np.repeat(np.deg2rad(betas)/3,3,axis=1);phi=np.cumsum(qs,axis=1);cloud=np.column_stack((np.sin(phi)@EFFECTIVE,BASE+np.cos(phi)@EFFECTIVE))
 fig,ax=plt.subplots(figsize=(6.5,4.8),layout='constrained');ax.scatter(cloud[:,0],cloud[:,1],s=.45,alpha=.10,color=COLORS[0],rasterized=True);ax.plot(*TARGET,'rx',ms=8,label=f'Referência ({TARGET[0]:.2f}; {TARGET[1]:.2f}) mm');ax.plot(0,TOTAL,'ko',ms=4,label='Configuração reta');ax.set(xlabel='X (mm)',ylabel='Y (mm)',title='Espaço de trabalho geométrico amostrado');ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=8);ax.text(.02,.98,f'X: {cloud[:,0].min():.2f} a {cloud[:,0].max():.2f} mm\nY: {cloud[:,1].min():.2f} a {cloud[:,1].max():.2f} mm'.replace('.',','),transform=ax.transAxes,va='top',fontsize=8,bbox=dict(facecolor='white',alpha=.85,edgecolor='none'));save(fig,'espaco_trabalho')
 # Exportar a nuvem, sem preencher buracos com um casco convexo.
 np.savetxt(DATA/'espaco_trabalho.csv',np.column_stack((betas,cloud)),delimiter=',',header='beta1_deg,beta2_deg,beta3_deg,X_mm,Y_mm',comments='')
 minimum=float(np.linalg.norm(fk(np.full(9,-np.pi/12))))
 workspace=dict(configuracoes=len(cloud),limite_junta_graus=15,limite_segmento_graus=45,
   suporte_fixo_mm=BASE,extensao_ponta_mm=TIP,segmentos_mm=L.reshape(3,3).sum(axis=1).tolist(),juntas_equivalentes_mm=L.tolist(),
   x_amostrado_mm=[float(cloud[:,0].min()),float(cloud[:,0].max())],
   y_amostrado_mm=[float(cloud[:,1].min()),float(cloud[:,1].max())],
   distancia_radial_minima_mm=minimum,extremo_negativo_mm=fk(np.full(9,-np.pi/12)).tolist(),
   alvo_solicitado_mm=[-212.4906613931,100.],
   alvo_solicitado_fora_limite_radial=bool(np.hypot(-212.4906613931,100)<minimum),
   hipoteses=['Tres juntas uniformes por segmento','Origem equivalente na saida dos cabos','Marcador recuado 20 mm da ponta fisica; suporte fixo de 15 mm','Sem colisoes, gravidade ou tensao dos cabos'])
 (DATA/'espaco_trabalho.json').write_text(json.dumps(workspace,indent=2),encoding='utf-8')
 fig,ax=plt.subplots(figsize=(7,5),layout='constrained')
 ax.scatter(cloud[:,0],cloud[:,1],s=1,alpha=.16,rasterized=True,label='15.625 configuracoes admissiveis')
 for sign in [-1,1]:
  q=np.full(9,sign*np.pi/12);ps=points(q);ax.plot(ps[:,0],ps[:,1],'-o',ms=3,label=f'Todas as juntas: {sign*15} graus')
 ax.plot(-212.4906613931,100,'rx',ms=9,label='Alvo solicitado (-212,49; 100)')
 ax.plot(0,TOTAL,'ko',label='Robo reto')
 ax.set(xlabel='X (mm)',ylabel='Y (mm)',title='Espaco de trabalho: dimensoes atualizadas' if PROFILE=='fisico' else 'Espaco de trabalho original')
 ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=8);save(fig,'espaco_trabalho_alvo')
 fig,ax=plt.subplots(figsize=(8,2.3));ax.axis('off')
 for x,text in [(.04,'Ângulo relativo θᵢ\npositivo para +X'),(.37,'Rz(−θᵢ) · Ty(Lᵢ)\ntransformação Hᵢ'),(.72,'Ty(b) · H₁…H₉ · Ty(−a)\nposição da ponta em mm')]:ax.text(x,.5,text,ha='left',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#eff6fa',ec=COLORS[0]),transform=ax.transAxes)
 for x in [.30,.65]:ax.annotate('',xy=(x+.055,.5),xytext=(x,.5),arrowprops=dict(arrowstyle='->'),xycoords='axes fraction')
 save(fig,'fluxo_homogeneas')
 result=dict(suporte_fixo_mm=BASE,extensao_ponta_mm=TIP,alvo_auxiliar_mm=TARGET.tolist(),perfil=PROFILE,L=L.tolist(),comprimento_total_mm=TOTAL,d=D,r=R,i=RATIO,Np=NP,pulsos_por_mm=K,mm_por_pulso=1/K,graus_por_pulso=180/np.pi/(D*K),q9=np.rad2deg(q9).tolist(),p9=fk(q9).tolist(),erro9=h9[-1],iteracoes9=it9,jacobiano_diferenca=diff,casos=records)
 (DATA/'resultados_numericos.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 with (DATA/'casos_teoricos.csv').open('w',newline='',encoding='utf-8') as stream:
  writer=csv.writer(stream);writer.writerow(['caso','beta1_deg','beta2_deg','beta3_deg','X_mm','Y_mm','c1_mm','c2_mm','c3_mm','A_pulsos','B_pulsos','C_pulsos','erro_ik_mm','erro_quantizacao_mm'])
  for r in records:writer.writerow([r['caso'],*r['beta'],*r['xy'],*r['cabos'],*r['pulsos'],r['erro_ik'],r['erro_quantizacao']])
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
