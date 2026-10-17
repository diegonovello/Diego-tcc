"""Desenho científico da Tabela 10. Requer NumPy e Pillow; não altera o TCC.

Código elaborado com auxílio de IA (Codex, OpenAI), a partir dos dados do
projeto. Referência geométrica ideal, não validação experimental.
Aceita --codigo-dir e --saida-dir; funciona na monografia e no repositório.
"""
from pathlib import Path
import argparse
import importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--codigo-dir', type=Path)
parser.add_argument('--saida-dir', type=Path)
args = parser.parse_args()
local = (root/'codigo/cinematica_xy').is_dir()
code_dir = args.codigo_dir or root/('codigo' if local else 'arduino')/'cinematica_xy'
out_dir = args.saida_dir or root/('imagens' if local else 'figuras')/'tcc2'
out_dir.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('ref', code_dir/'validar_modelo.py')
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
cases = [(0,0,0),(20,20,20),(0,0,20),(10,20,15),(-10,-20,-15),(30,-10,20)]
colors = ['#007eaa','#d47700','#c62828']
im = Image.new('RGB',(1800,2500),'white')
d = ImageDraw.Draw(im)
def txt(x,y,s,size=25,anchor='la',bold=False):
    candidates = ['C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),
                  'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf']
    for candidate in candidates:
        try:
            font = ImageFont.truetype(candidate,size)
            break
        except OSError:
            continue
    else:
        font = ImageFont.load_default(size=size)
    d.text((x,y),s,font=font,fill='#253e51',anchor=anchor)
txt(900,55,'Configurações de referência',52,'ma',True)
txt(900,120,'Validação planar • Casos da Tabela 10 • Dimensões em milímetros',29,'ma')
for s,c in enumerate(colors):
    x=310+s*440
    d.line((x,205,x+65,205),fill=c,width=10)
    txt(x+80,188,f'Segmento {s+1}',28)
txt(900,240,'Círculos: juntas     ▲: base fixa     ×: ponta teórica',25,'ma')
for k,beta in enumerate(cases):
    left,top = 95+(k%2)*850,325+(k//2)*650
    txt(left+330,top,f'Caso {k+1} | β1 = {beta[0]}°; β2 = {beta[1]}°; β3 = {beta[2]}°',28,'ma',True)
    q=np.deg2rad(beta)
    phi=np.cumsum(np.repeat(q/3,3))
    pts=np.vstack(([0.,0.],np.cumsum(10*ref.L*np.column_stack((np.sin(phi),np.cos(phi))),axis=0)))
    target=pts[-1]
    assert np.allclose(target,10*ref.fk(q),atol=1e-9)
    assert np.allclose(np.linalg.norm(np.diff(pts,axis=0),axis=1),15.17)
    txt(left+330,top+42,f'Ponta: X = {target[0]:.3f} mm; Y = {target[1]:.3f} mm'.replace('.',','),25,'ma')
    # Escala isotrópica idêntica em todos os painéis: 2,65 pixels/mm.
    x0,y0=left+300,top+500
    def p(point):
        return (x0+2.65*point[0],y0-2.65*point[1])
    d.rectangle((*p((-85,150)),*p((85,-10))),fill='#fbfcfe',outline='#c2cdd7',width=2)
    for x in range(-75,76,25):
        a,b=p((x,-10)),p((x,150))
        d.line((*a,*b),fill='#dae3ec',width=1)
        txt(a[0],a[1]+10,str(x),20,'ma')
    for y in range(0,151,25):
        a,b=p((-85,y)),p((85,y))
        d.line((*a,*b),fill='#dae3ec',width=1)
        txt(a[0]-10,a[1]-12,str(y),20,'ra')
    d.line((*p((-85,0)),*p((85,0))),fill='#9badbc',width=2)
    d.line((*p((0,-10)),*p((0,150))),fill='#9badbc',width=2)
    for a,b in [(p((target[0],0)),p(target)),(p((0,target[1])),p(target))]:
        a,b=np.array(a),np.array(b)
        length=np.linalg.norm(b-a)
        if length>0:
            u=(b-a)/length
            for t in np.arange(0,length,13):
                d.line((*tuple(a+t*u),*tuple(a+min(t+5,length)*u)),fill='#52606d',width=2)
    for j in range(9):
        d.line((*p(pts[j]),*p(pts[j+1])),fill=colors[j//3],width=9)
    for point in pts[1:-1]:
        x,y=p(point)
        d.ellipse((x-6,y-6,x+6,y+6),fill='white',outline='#354958',width=2)
    d.polygon([(x0,y0-11),(x0-11,y0+10),(x0+11,y0+10)],fill='#172d40')
    x,y=p(target)
    d.line((x-9,y-9,x+9,y+9),fill='#253e51',width=4)
    d.line((x-9,y+9,x+9,y-9),fill='#253e51',width=4)
    txt(left+290,top+590,'X (mm)',23,'ma')
    txt(left+15,top+70,'Y (mm)',23)
    print(f'Caso {k+1}: beta={beta}; X={target[0]:.6f} mm; Y={target[1]:.6f} mm')
txt(95,2295,'Modelo: 9 elos de 15,17 mm; 3 juntas por segmento; rotação por junta = β / 3.',26)
txt(95,2340,'β1, β2 e β3 são flexões dos segmentos, não ângulos dos motores nem eixos X, Y e Z.',26)
txt(95,2385,'Referências teóricas: a inversa pode obter outra forma para a mesma posição da ponta.',26)
txt(95,2430,'Na bancada: alinhar a base e os eixos; medir ponta e juntas; conferir tensão, retorno e limites.',24)
output=out_dir/'posicoes_referencia_planar'
im.save(output.with_suffix('.png'),dpi=(150,150))
im.save(output.with_suffix('.pdf'),resolution=150)
