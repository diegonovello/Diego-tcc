"""Reprodução numérica da monografia. Unidades: mm e radianos.

Gera dados e figuras teóricas; não lê instrumentos nem envia comandos a motores.
Python 3.10+, NumPy e Matplotlib. Executar na pasta da monografia.
"""
from pathlib import Path
import json,math,csv,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'imagens/verificacao'
OUT.mkdir(parents=True,exist_ok=True)
L=15.17;D=18.98;R=15.;RATIO=4/3;NP=400
COLORS=['#007eaa','#d47700','#c62828']
TARGET=np.array([-62.39,115.51])
K=NP*RATIO/(2*np.pi*R)

def points(q):
 a=np.cumsum(q)
 return np.vstack(([0.,0.],np.cumsum(L*np.column_stack((np.sin(a),np.cos(a))),axis=0)))
def fk(q):return points(q)[-1]
def jac(q):
 a=np.cumsum(q)
 return np.array([[L*np.cos(a[j:]).sum() for j in range(9)],[-L*np.sin(a[j:]).sum() for j in range(9)]])
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
 fig,ax=plt.subplots(figsize=(6.3,6.2),layout='constrained');ax.set(xlim=(-95,95),ylim=(-5,145),xlabel='X (mm)',ylabel='Y (mm)');ax.set_aspect('equal');ax.grid(alpha=.22);ax.axvline(0,color='#888',lw=.6);ax.axhline(0,color='#888',lw=.6);return fig,ax
def chain(ax,q,label=True):
 ps=points(q)
 for g,col in enumerate(COLORS):ax.plot(ps[g*3:g*3+4,0],ps[g*3:g*3+4,1],'-o',color=col,lw=2.3,ms=4,label=f'Segmento {g+1}' if label else None)
 ax.plot(0,0,'^',color='black',ms=7);return ps
def save(fig,name):fig.savefig(OUT/(name+'.png'),dpi=200);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)

def main():
 q9,h9,it9=solve(TARGET,np.zeros(9));b7,h7,it7=solve(TARGET,np.deg2rad([-24,4,-42]),True,tol=1e-8,maxiter=300)
 assert max(abs(np.rad2deg(q9)))<=15
 assert max(abs(np.rad2deg(b7)))<=45
 # Derivadas independentes de funções e consistência de escala.
 rng=np.random.default_rng(42);diff=0
 for _ in range(30):
  q=rng.uniform(-np.pi/12,np.pi/12,9);eps=1e-6
  fd=np.column_stack([(fk(q+np.eye(9)[j]*eps)-fk(q-np.eye(9)[j]*eps))/(2*eps) for j in range(9)])
  diff=max(diff,float(np.max(np.abs(fd-jac(q)))))
  transform=np.eye(4)
  for angle in q:
   sn,cs=np.sin(angle),np.cos(angle)
   h=np.array([[cs,sn,0,L*sn],[-sn,cs,0,L*cs],[0,0,1,0],[0,0,0,1]])
   transform=transform@h
  assert np.allclose(transform[:2,3],fk(q),atol=1e-10)
 assert diff<1e-5
 cases=[np.array(a,float) for a in [(0,0,0),(20,20,20),(0,0,20),(10,20,15),(-10,-20,-15),(30,-10,20)]]+[np.rad2deg(b7)]
 records=[]
 for number,beta in enumerate(cases,1):
  q=np.repeat(np.deg2rad(beta)/3,3);target=fk(q);c=D*np.cumsum(np.deg2rad(beta));raw=K*c
  n=np.sign(raw)*np.floor(np.abs(raw)+.5);n=n.astype(int)
  quant_beta=np.diff(np.r_[0,n/K])/D
  quant_error=float(np.linalg.norm(fk(np.repeat(quant_beta/3,3))-target))
  sol,h,it=solve(target,np.zeros(3),True,tol=.1,maxiter=300)
  records.append(dict(caso=number,beta=beta.tolist(),xy=target.tolist(),cabos=c.tolist(),pulsos=n.tolist(),erro_ik=h[-1],erro_quantizacao=quant_error,iteracoes=it))
  fig,ax=baseplot();chain(ax,q);ax.plot(*target,'kx',ms=9);ax.set_title(f'Caso {number}: '+ '; '.join(f'{a:.3f}°' for a in beta)+'\n'+f'X={target[0]:.3f} mm; Y={target[1]:.3f} mm');ax.legend(loc='upper left',fontsize=8);save(fig,f'caso_{number:02d}')
 for name,q,title in [('modelo_nove_elos',q9,'Modelo de nove elos: convenção vertical'),('direta_verificada',q9,'Verificação direta da solução de nove juntas'),('inversa_inicial',np.zeros(9),'Configuração inicial: nove ângulos nulos'),('inversa_final',q9,'Solução inversa com limites de ±15° por junta')]:
  fig,ax=baseplot();chain(ax,q);ax.plot(*TARGET,'kx',ms=9,label='Referência geométrica');ax.set_title(title);ax.legend(fontsize=8);save(fig,name)
 fig,ax=plt.subplots(figsize=(6.5,3.3),layout='constrained');ax.semilogy(range(len(h9)),h9,'o-',color=COLORS[0]);ax.set(xlabel='Atualização do vetor de juntas',ylabel='Erro cartesiano (mm)',title='Convergência da solução de nove juntas');ax.grid(alpha=.25);save(fig,'convergencia_nove')
 # Espaço amostrado do modelo agrupado: não é uma identificação física.
 betas=np.stack(np.meshgrid(*([np.linspace(-45,45,25)]*3),indexing='ij'),axis=-1).reshape(-1,3)
 qs=np.repeat(np.deg2rad(betas)/3,3,axis=1);phi=np.cumsum(qs,axis=1);cloud=L*np.column_stack((np.sin(phi).sum(axis=1),np.cos(phi).sum(axis=1)))
 fig,ax=plt.subplots(figsize=(6.5,4.8),layout='constrained');ax.scatter(cloud[:,0],cloud[:,1],s=.45,alpha=.10,color=COLORS[0],rasterized=True);ax.plot(*TARGET,'rx',ms=8,label='Referência (-62,39; 115,51) mm');ax.plot(0,136.53,'ko',ms=4,label='Configuração reta');ax.set(xlabel='X (mm)',ylabel='Y (mm)',title='Espaço de trabalho geométrico amostrado');ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=8);save(fig,'espaco_trabalho')
 fig,ax=plt.subplots(figsize=(8,2.3));ax.axis('off')
 for x,text in [(.04,'Ângulo relativo θᵢ\npositivo para +X'),(.37,'Rz(−θᵢ) · Ty(L)\ntransformação Hᵢ'),(.72,'H₁H₂…H₉\nposição em mm')]:ax.text(x,.5,text,ha='left',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#eff6fa',ec=COLORS[0]),transform=ax.transAxes)
 for x in [.30,.65]:ax.annotate('',xy=(x+.055,.5),xytext=(x,.5),arrowprops=dict(arrowstyle='->'),xycoords='axes fraction')
 save(fig,'fluxo_homogeneas')
 result=dict(L=L,d=D,r=R,i=RATIO,Np=NP,pulsos_por_mm=K,mm_por_pulso=1/K,graus_por_pulso=180/np.pi/(D*K),q9=np.rad2deg(q9).tolist(),p9=fk(q9).tolist(),erro9=h9[-1],iteracoes9=it9,jacobiano_diferenca=diff,casos=records)
 (ROOT/'codigo/verificacao/resultados_numericos.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 with (ROOT/'codigo/verificacao/casos_teoricos.csv').open('w',newline='',encoding='utf-8') as stream:
  writer=csv.writer(stream);writer.writerow(['caso','beta1_deg','beta2_deg','beta3_deg','X_mm','Y_mm','c1_mm','c2_mm','c3_mm','A_pulsos','B_pulsos','C_pulsos','erro_ik_mm','erro_quantizacao_mm'])
  for r in records:writer.writerow([r['caso'],*r['beta'],*r['xy'],*r['cabos'],*r['pulsos'],r['erro_ik'],r['erro_quantizacao']])
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
