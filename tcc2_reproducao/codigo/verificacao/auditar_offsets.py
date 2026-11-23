"""Confere previsões, leituras e constantes do firmware sem alterar os dados."""
from pathlib import Path
import csv
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
K = 400 * (4 / 3) / (2 * math.pi * 15)
D = 21.5
POSES = [(20,20,20),(-20,-20,-20),(10,20,15),(-10,-20,-15),(45,45,45),(-45,-45,-45)]

def fk(beta):
    x, y, angle = 0., 1.5, 0.
    for joint in range(9):
        angle += math.radians(beta[joint // 3]) / 3
        length = 3 if joint == 8 else 5
        x += length * math.sin(angle)
        y += length * math.cos(angle)
    return x, y

def main():
    data = json.loads((ROOT/'dados/ensaios_posicionamento_cm.json').read_text(encoding='utf-8'))
    with (ROOT/'dados/reanalise/offsets.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f, delimiter=';'))
    code = (ROOT/'codigo/sete_posicoes_revisado/sete_posicoes_revisado.ino').read_text(encoding='utf-8')
    constants = {name: int(value) for name, value in re.findall(r'const int16_t (pulso_folga_motor_\w+)\s*=\s*(-?\d+)', code)}
    historical_code = (ROOT/'codigo/historico/sete_posicoes_m1_25_5.ino').read_text(encoding='utf-8')
    historical = {name: int(value) for name, value in re.findall(r'const int16_t (pulso_folga_motor_\w+)\s*=\s*(-?\d+)', historical_code)}
    assert constants['pulso_folga_motor_esq1'] == 5
    assert constants['pulso_folga_motor_direita1'] == 65
    assert historical['pulso_folga_motor_esq1'] == 25
    assert historical['pulso_folga_motor_direita1'] == 5
    for side in ['esq', 'direita']:
        for motor in [2, 3]:
            assert constants[f'pulso_folga_motor_{side}{motor}'] == 5
    checks = []
    for i, beta in enumerate(POSES):
        motor = (65,5,5) if i % 2 == 0 else (-5,-5,-5)
        c = [motor[j] / K for j in (1,2,0)]
        db = [math.degrees(v / D) for v in (c[0], c[1]-c[0], c[2]-c[1])]
        a, b = fk(beta), fk([v+w for v,w in zip(beta,db)])
        predicted = [w-v for v,w in zip(a,b)]
        measured = [sum(p[axis] for p in data['com_ajuste'][2*i+1])/5 - sum(p[axis] for p in data['sem_ajuste'][2*i+1])/5 for axis in (0,1)]
        for values, suffix in ((predicted,'previsto'),(measured,'medido')):
            for value, axis in zip(values, ('x','y')):
                assert abs(value-float(rows[i][f'delta_{axis}_{suffix}_cm'])) < 1e-10
        checks.append(dict(posicao=i+2, previsto_cm=predicted, medido_cm=measured))
    result = dict(tabela_reproduzida=True, constantes_entrega=constants, constantes_historico=historical,
        parametros_relato_m1=dict(esquerda=5,direita=65),
        parametros_coleta_confirmados_pelo_autor=True,
        binario_da_coleta_disponivel=False, verificacoes=checks)
    (ROOT/'dados/reanalise/auditoria_offsets.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Seis posições conferidas; firmware de entrega 5/65 verificado e histórico 25/5 preservado.')

if __name__ == '__main__':
    main()
