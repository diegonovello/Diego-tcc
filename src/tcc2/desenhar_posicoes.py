"""Gera seis figuras individuais, em PNG/PDF, das configurações da Tabela 10.

Código elaborado com auxílio de IA (Codex, OpenAI), a partir dos dados do
projeto. Referência geométrica ideal, não validação experimental.
Requer NumPy e Pillow; funciona na monografia e no repositório.
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

def generate_case(k, beta):
    im = Image.new('RGB',(1200,1100),'white')
    draw = ImageDraw.Draw(im)
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
        draw.text((x,y),s,font=font,fill='#253e51',anchor=anchor)

    q = np.deg2rad(beta)
    phi = np.cumsum(np.repeat(q/3,3))
    pts = np.vstack(([0.,0.], np.cumsum(10*ref.L*np.column_stack((np.sin(phi),np.cos(phi))),axis=0)))
    target = pts[-1]
    assert np.allclose(target,10*ref.fk(q),atol=1e-9)
    assert np.allclose(np.linalg.norm(np.diff(pts,axis=0),axis=1),15.17)
    txt(600,25,f'Caso {k} | β1 = {beta[0]}°; β2 = {beta[1]}°; β3 = {beta[2]}°',37,'ma',True)
    txt(600,85,f'Ponta: X = {target[0]:.3f} mm; Y = {target[1]:.3f} mm'.replace('.',','),30,'ma')
    for s,color in enumerate(colors):
        x = 190+s*300
        draw.line((x,160,x+50,160),fill=color,width=10)
        txt(x+65,143,f'Segmento {s+1}',25)
    # Mesma escala isotrópica e mesmos limites em todas as figuras.
    x0,y0,scale = 600,850,4.2
    def p(point):
        return (x0+scale*point[0],y0-scale*point[1])
    draw.rectangle((*p((-85,150)),*p((85,-10))),fill='#fbfcfe',outline='#c2cdd7',width=2)
    for x in range(-75,76,25):
        a,b = p((x,-10)),p((x,150))
        draw.line((*a,*b),fill='#dae3ec',width=1)
        txt(a[0],a[1]+12,str(x),25,'ma')
    for y in range(0,151,25):
        a,b = p((-85,y)),p((85,y))
        draw.line((*a,*b),fill='#dae3ec',width=1)
        txt(a[0]-15,a[1]-15,str(y),25,'ra')
    draw.line((*p((-85,0)),*p((85,0))),fill='#9badbc',width=2)
    draw.line((*p((0,-10)),*p((0,150))),fill='#9badbc',width=2)
    for a,b in [(p((target[0],0)),p(target)),(p((0,target[1])),p(target))]:
        a,b = np.array(a),np.array(b)
        length = np.linalg.norm(b-a)
        if length>0:
            u = (b-a)/length
            for t in np.arange(0,length,16):
                draw.line((*tuple(a+t*u),*tuple(a+min(t+6,length)*u)),fill='#52606d',width=2)
    for j in range(9):
        draw.line((*p(pts[j]),*p(pts[j+1])),fill=colors[j//3],width=12)
    for point in pts[1:-1]:
        x,y = p(point)
        draw.ellipse((x-8,y-8,x+8,y+8),fill='white',outline='#354958',width=2)
    draw.polygon([(x0,y0-13),(x0-13,y0+12),(x0+13,y0+12)],fill='#172d40')
    x,y = p(target)
    draw.line((x-12,y-12,x+12,y+12),fill='#253e51',width=4)
    draw.line((x-12,y+12,x+12,y-12),fill='#253e51',width=4)
    txt(600,950,'X (mm)',30,'ma')
    txt(185,180,'Y (mm)',30,'ma')
    txt(600,1008,'Círculos: juntas  |  ▲: base fixa  |  ×: ponta teórica',25,'ma')
    txt(600,1050,'Modelo geométrico ideal; configuração reta em +Y.',25,'ma')
    output = out_dir/f'posicao_caso_{k:02d}'
    im.save(output.with_suffix('.png'),dpi=(180,180))
    im.save(output.with_suffix('.pdf'),resolution=180)
    print(f'Caso {k}: beta={beta}; X={target[0]:.6f} mm; Y={target[1]:.6f} mm')

for k,beta in enumerate(cases,start=1):
    generate_case(k,beta)
