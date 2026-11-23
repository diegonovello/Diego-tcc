from pathlib import Path
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
r=Path(__file__).resolve().parents[2];o=r/'imagens/verificacao_dimensoes_fisicas';plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
colors=['#2876a3','#d18b22','#b34949'];poses=[[0,0,0],[20,20,20],[-20,-20,-20],[10,20,15],[-10,-20,-15],[45]*3,[-45]*3]
from matplotlib.lines import Line2D
fig=plt.figure(figsize=(8.6,10.6))
gs=fig.add_gridspec(4,4,left=.10,right=.96,bottom=.10,top=.97,hspace=.48,wspace=.65)
axs=[fig.add_subplot(gs[0,1:3])]
for row in range(1,4):
 axs.extend([fig.add_subplot(gs[row,0:2]),fig.add_subplot(gs[row,2:4])])
for k,(ax,beta) in enumerate(zip(axs,poses)):
 pts=[[0,15]];phi=0
 for j in range(9):
  phi+=np.deg2rad(beta[j//3]/3);L=50;pts.append(np.array(pts[-1])+[L*np.sin(phi),L*np.cos(phi)])
 pts=np.array(pts)
 for j in range(3):ax.plot(pts[3*j:3*j+4,0],pts[3*j:3*j+4,1],'-o',color=colors[j],ms=2.5,lw=2)
 tip=pts[-1]-20*np.array([np.sin(phi),np.cos(phi)])
 ax.plot([0,0],[0,15],color='#444444',lw=2)
 ax.plot([pts[-1,0],tip[0]],[pts[-1,1],tip[1]],color='#444444',lw=2)
 ax.plot(0,0,'ks',ms=4);ax.set_title(f'({chr(97+k)}) Posição {k+1}',fontsize=11)
 ax.set(xlim=(-400,400),ylim=(-20,500),xticks=[-350,0,350],yticks=[0,250,445]);ax.grid(alpha=.2);ax.set_aspect('equal');ax.tick_params(labelsize=8)
fig.supxlabel('X (mm)',y=.068,fontsize=10);fig.supylabel('Y (mm)',x=.018,fontsize=10)
fig.legend([Line2D([0],[0],color=c,lw=2) for c in colors],['Segmento da base','Segmento do meio','Segmento da ponta'],loc='lower center',bbox_to_anchor=(.5,.012),ncol=3,frameon=False,fontsize=9)
fig.savefig(o/'sete_posicoes_paineis.pdf',bbox_inches='tight');plt.close(fig)

def canvas(w,h):
 f,a=plt.subplots(figsize=(w,h));a.set(xlim=(0,10),ylim=(0,10));a.axis('off');return f,a
def box(a,x,y,w,h,t,fc='#eaf1f6',fs=10):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.09',facecolor=fc,edgecolor='#456077',lw=1));a.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs)
def arrow(a,p,q,t=None):
 a.annotate('',xy=q,xytext=p,arrowprops={'arrowstyle':'->','color':'#456077','lw':1.3})
 if t:a.text((p[0]+q[0])/2,(p[1]+q[1])/2+.15,t,fontsize=8,ha='center')
f,a=canvas(10,4)
box(a,.1,3,2,4,'Arduino Uno\nUSB / serial\n115.200 baud')
for y,m,pins,seg in [(8,'M1','D2 / D5','Ponta'),(5,'M2','D6 / D7','Base'),(2,'M3','D8 / D9','Meio')]:
 box(a,3,y-1,2,1.7,'DM556\nPUL / DIR');box(a,6,y-1,3.6,1.7,f'{m} → par cônico → carretel\nPar de cordões: {seg}',fs=9);arrow(a,(2.2,5),(2.8,y-.15),pins);arrow(a,(5.1,y-.15),(5.9,y-.15))
a.text(4.5,.1,'Fonte DC → alimentação de potência dos três drivers',ha='center',fontsize=10);f.savefig(o/'arquitetura_tres_canais.pdf',bbox_inches='tight');plt.close(f)
f,a=canvas(8,4.8)
box(a,2.5,8.4,5,1,'Início: robô reto e cordões tensionados\nConfirmar ok → zerar contadores')
box(a,3,6.9,4,.8,'Aguardar comando');arrow(a,(5,8.3),(5,7.8))
box(a,.2,4.3,4.3,1.5,'Comando 2–7: sair do centro\nMovimento nominal completo\n+ correção uma única vez',fs=9)
box(a,5.5,4.3,4.3,1.5,'Comando 1: retorno completo\nInverter todo o saldo emitido\nSem nova correção',fs=9)
arrow(a,(4,6.8),(2.4,5.9));arrow(a,(6,6.8),(7.6,5.9))
box(a,.2,1.6,4.3,1.2,'Posição concluída\nSolicitar retorno com 1')
box(a,5.5,1.6,4.3,1.2,'Saldo zero\nPróximo ensaio')
arrow(a,(2.4,4.2),(2.4,2.9));arrow(a,(7.6,4.2),(7.6,2.9))
a.text(5,.4,'Em movimento: atualizar saldo a cada pulso; x interrompe e conserva a contagem.',ha='center',fontsize=8)
f.savefig(o/'fluxo_comandos.pdf',bbox_inches='tight');plt.close(f)
f,a=canvas(10,3.8)
for j in range(3):
 box(a,1+2.7*j,3.4,2.7,4,'',fc='#f2f4f6');a.text(2.35+2.7*j,8,f'Segmento {j+1}',ha='center');a.text(1+2.7*(j+1),2.6,['165 mm','315 mm','465 mm'][j],ha='center',fontsize=9)
for j,end in enumerate([3.7,6.4,9.1]):
 y=6.7-j*1.15
 for dy in [-.14,.14]:a.plot([.3,end],[y+dy,y+dy],color=colors[j],lw=2)
 a.plot([end,end],[y-.14,y+.14],color=colors[j],lw=5);a.text(.25,y+.4,['M2: base','M3: meio','M1: ponta'][j],fontsize=9,color=colors[j]);
a.text(1,2.6,'0',ha='center');a.text(5,1.3,'Cada cor representa um par antagonista; traço final = ancoragem.',ha='center',fontsize=10);a.text(5,.45,'Esquema funcional: as linhas foram afastadas para leitura.',ha='center',fontsize=9)
f.savefig(o/'ancoragens_cabos.pdf',bbox_inches='tight');plt.close(f)
print('4 figuras vetoriais geradas')
