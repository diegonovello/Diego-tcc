from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,FancyBboxPatch
r=Path(__file__).resolve().parents[2];o=r/'imagens/verificacao_dimensoes_fisicas'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
fig,(a,b)=plt.subplots(1,2,figsize=(10,4),gridspec_kw={'width_ratios':[1.7,1]})
ink='#243343';blue='#23659a';orange='#dc8214';gray='#e5e8eb'
a.add_patch(FancyBboxPatch((0,-20),60,40,boxstyle='round,pad=0,rounding_size=6',facecolor=gray,edgecolor=ink,lw=1.3))
for y in [-21.5,21.5]:
 a.add_patch(Rectangle((-2,y-1.5),64,3,facecolor=orange,edgecolor=orange))
 a.plot([-3,75],[y,y],color=orange,lw=.9,ls='--')
a.plot([-4,76],[0,0],color=blue,lw=1,ls='--');a.add_patch(Circle((15,0),2.1,facecolor='white',edgecolor=blue,lw=1.5));a.plot(15,0,'.',color=blue)
a.annotate('Eixo da junta',xy=(15,0),xytext=(8,-11),arrowprops={'arrowstyle':'-','color':blue},color=blue,fontsize=10)
def dim(ax,x,y1,y2,label,color=ink):
 ax.annotate('',xy=(x,y1),xytext=(x,y2),arrowprops={'arrowstyle':'<->','color':color,'lw':1.2,'shrinkA':0,'shrinkB':0})
 ax.text(x+2,(y1+y2)/2,label,va='center',color=color,fontsize=10)
for y in [-20,20]:a.plot([-13,0],[y,y],color=ink,lw=.7)
a.annotate('',xy=(-10,-20),xytext=(-10,20),arrowprops={'arrowstyle':'<->','color':ink,'shrinkA':0,'shrinkB':0});a.text(-14,0,'h = 40 mm',rotation=90,ha='center',va='center',color=ink)
dim(a,70,0,21.5,'d = 21,5 mm',blue);dim(a,70,-21.5,0,'d = 21,5 mm',blue)
a.text(27,28,'Centro do cabo superior',color=orange,ha='center');a.text(27,-29,'Centro do cabo inferior',color=orange,ha='center')
a.set(xlim=(-20,100),ylim=(-34,38));a.set_aspect('equal');a.axis('off');a.set_title('a) Plano da dobra — esquema do elo',loc='left',fontsize=12,fontweight='bold',color=ink,pad=12)
b.add_patch(Rectangle((-6,-4),12,4,facecolor=gray,edgecolor='none'));b.plot([-6,6],[0,0],color=ink,lw=1.3)
b.add_patch(Circle((0,1.5),1.5,facecolor=orange,edgecolor=ink,lw=1.3));b.plot(0,1.5,'o',color=ink,ms=4)
b.plot([0,4.3],[1.5,1.5],ls='--',color=ink,lw=.7);b.plot([0,4.3],[0,0],ls='--',color=ink,lw=.7)
dim(b,3.7,0,1.5,'1,5 mm')
b.text(0,3.6,'Cabo: diâmetro 3 mm',ha='center',color=ink)
b.text(0,-1.3,'Face externa do elo',ha='center',color=ink)
b.text(0,-3.4,'Contato tangente, sem afastador',ha='center',fontsize=9,color=ink)
b.set(xlim=(-6.5,8),ylim=(-4.5,6));b.set_aspect('equal');b.axis('off');b.set_title('b) Detalhe em seção',loc='left',fontsize=12,fontweight='bold',color=ink,pad=12)
fig.subplots_adjust(left=.02,right=.98,top=.84,bottom=.12,wspace=.13)
fig.savefig(o/'afastamento_cabo_esquema.pdf',bbox_inches='tight',pad_inches=.12)
fig.savefig(o/'afastamento_cabo_esquema.png',dpi=220,bbox_inches='tight',pad_inches=.12)
