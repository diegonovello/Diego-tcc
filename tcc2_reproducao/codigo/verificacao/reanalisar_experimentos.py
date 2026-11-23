"""Reanálise da v2: Python 3.10+, numpy e matplotlib.

Executar de qualquer diretório. Lê os 130 pares originais sem alterá-los.
Bootstrap independente entre condições, em blocos de bateria, semente 20261117.
Os ajustes de rotação e ganho são descritivos, avaliados na própria amostra.
"""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dados/reanalise'
FIG = ROOT / 'imagens/reanalise'
SOURCE = ROOT / 'dados/ensaios_posicionamento_cm.json'
KEYS = ['sem_ajuste', 'com_ajuste']
NAMES = ['Sem ajuste', 'Com ajuste']
SEED, NBOOT = 20261117, 10000


def fk(beta_deg):
    phi = np.cumsum(np.repeat(np.deg2rad(beta_deg) / 3, 3, axis=-1), axis=-1)
    lengths = np.array([5.] * 8 + [3.])
    return np.stack((np.sin(phi) @ lengths, 1.5 + np.cos(phi) @ lengths), axis=-1)


def rotation(p, q):
    u, _, vt = np.linalg.svd(p.reshape(-1, 2).T @ np.broadcast_to(q, p.shape).reshape(-1, 2))
    return u @ np.diag([1., np.linalg.det(u @ vt)]) @ vt


def csv_write(name, header, rows):
    with (OUT / (name + '.csv')).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow(header)
        writer.writerows(rows)


def fmt(x, places=2):
    return f'{x:.{places}f}'.replace('.', ',')


def table(name, caption, header, rows, spec):
    text = '\\begin{table}[H]\\centering\n\\caption{' + caption + '}\\label{tab:reanalise-' + name + '}\n'
    text += '\\small\\begin{tabular}{' + spec + '}\\toprule\n' + ' & '.join(header) + r'\\\midrule' + '\n'
    text += '\n'.join(' & '.join(row) + r'\\' for row in rows)
    text += '\n\\bottomrule\\end{tabular}\\par\\smallskip\n{\\footnotesize Fonte: Elaborado pelo autor a partir dos registros dos ensaios.}\\end{table}\n'
    (OUT / (name + '.tex')).write_text(text, encoding='utf-8')


def golden_min(fn, lo, hi):
    for _ in range(90):
        a = hi - (hi - lo) / ((1 + np.sqrt(5)) / 2)
        b = lo + (hi - lo) / ((1 + np.sqrt(5)) / 2)
        if fn(a) < fn(b):
            hi = b
        else:
            lo = a
    return (lo + hi) / 2


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    original = SOURCE.read_bytes()
    d = json.loads(original)
    target = np.asarray(d['teorico'])
    beta = np.array([[0., 0., 0.], [20., 20., 20.], [-20., -20., -20.],
                     [10., 20., 15.], [-10., -20., -15.], [45., 45., 45.],
                     [-45., -45., -45.]])
    assert np.allclose(fk(beta), target, atol=1e-12), \
        'As referências teóricas não coincidem com a cinemática do marcador.'
    q = target[1:] - target[0]
    results, point_rows, pose_rows, iso_rows = {}, [], [], []
    rels, absolutes, positions = [], [], []
    for key, label in zip(KEYS, NAMES):
        a = np.asarray(d[key], dtype=float)
        assert a.shape == (13, 5, 2)
        m = a[1::2].transpose(1, 0, 2)
        p = m - a[0, :, None, :]
        rot = rotation(p, q)
        assert np.allclose(rot.T @ rot, np.eye(2)) and np.isclose(np.linalg.det(rot), 1.)
        errors = [m - target[1:], p - q, p @ rot - q]
        assert np.sum(errors[2] ** 2) <= np.sum(errors[1] ** 2) + 1e-10
        distances = [np.linalg.norm(e, axis=-1) for e in errors]
        # Row-vector convention: atan2(R[0,1], R[0,0]) is applied CCW angle.
        angle = float(np.rad2deg(np.arctan2(rot[0, 1], rot[0, 0])))
        means = [float(e.mean()) for e in distances]
        results[key] = dict(rotation_deg=angle, rotation_matrix=rot.tolist(), global_means_cm=means)
        rels.append(p)
        positions.append(m)
        absolutes.append(distances[0])
        for b in range(5):
            for j in range(6):
                point_rows.append([key, b+1, j+2, *m[b,j], *(p[b,j] @ rot + target[0]), *[v[b,j] for v in distances]])
        for j in range(6):
            row = [key, j+2]
            for err, dist in zip(errors, distances):
                row += [float(dist[:, j].mean()), float(dist[:, j].std(ddof=1)), *err[:,j].mean(axis=0)]
            pose_rows.append(row)
            center = m[:,j].mean(axis=0)
            ll = np.linalg.norm(m[:,j] - center, axis=-1)
            iso_rows.append([key, j+2, float(np.linalg.norm(center-target[j+1])), float(ll.mean()+3*ll.std(ddof=1))])
    csv_write('leituras_corrigidas', ['condicao','bateria','posicao','x_cm','y_cm','x_corrigido_cm','y_corrigido_cm','erro_absoluto_cm','erro_relativo_cm','erro_rigido_cm'], point_rows)
    csv_write('indicadores_posicao', ['condicao','posicao'] + [f'{v}_{mode}' for mode in ['absoluto','relativo','rigido'] for v in ['media_cm','dp_cm','vies_x_cm','vies_y_cm']], pose_rows)
    csv_write('indicadores_exploratorios', ['condicao','posicao','AP_cm','RP_cm'], iso_rows)
    rng = np.random.default_rng(SEED)
    boot = np.empty((NBOOT, 3))
    for i in range(NBOOT):
        sample_means = []
        for k in range(2):
            ix = rng.integers(0, 5, 5)
            p = rels[k][ix]
            rot = rotation(p, q)
            sample_means.append([absolutes[k][ix].mean(), np.linalg.norm(p-q, axis=-1).mean(), np.linalg.norm(p@rot-q, axis=-1).mean()])
        boot[i] = np.subtract(*sample_means)
    csv_write('bootstrap', ['replica','reducao_absoluta_cm','reducao_relativa_cm','reducao_rigida_cm'], [[i+1,*row] for i,row in enumerate(boot)])
    observed = np.array(results[KEYS[0]]['global_means_cm']) - results[KEYS[1]]['global_means_cm']
    ci = np.quantile(boot, [.025,.975], axis=0).T
    results['bootstrap'] = dict(seed=SEED, replicas=NBOOT, method='percentil; baterias inteiras; condições independentes; rotação reestimada', reduction_observed_cm=observed.tolist(), ci95_cm=ci.tolist(), nonpositive_count=(boot<=0).sum(axis=0).tolist())
    kconv, dd = 400*(4/3)/(2*np.pi*15), 21.5
    offset_rows = []
    for j in range(6):
        motor = np.array([65,5,5]) if j%2==0 else -np.array([5,5,5])
        cords = motor[[1,2,0]] / kconv
        dbeta = np.rad2deg(np.diff(np.r_[0.,cords]) / dd)
        pred = fk(beta[j+1]+dbeta)-target[j+1]
        measured = positions[1][:,j].mean(axis=0)-positions[0][:,j].mean(axis=0)
        offset_rows.append([j+2,*dbeta,*pred,*measured, bool(np.any(np.abs(beta[j+1]+dbeta)>45))])
    csv_write('offsets', ['posicao','delta_beta_base_deg','delta_beta_meio_deg','delta_beta_ponta_deg','delta_x_previsto_cm','delta_y_previsto_cm','delta_x_medido_cm','delta_y_medido_cm','extrapola_limite_segmento'], offset_rows)
    gain_rows = []
    for cond, p in zip(KEYS, rels):
        for side, ix in [('Direita', [0,2,4]), ('Esquerda', [1,3,5])]:
            b = beta[1:][ix]
            def objective(g):
                e = p[:,ix] - (fk(g*b)-target[0])
                return float(np.sum(e**2))
            grid = np.linspace(.5,1.5,2001)
            best = int(np.argmin([objective(g) for g in grid]))
            assert 0 < best < len(grid)-1
            gain = golden_min(objective, grid[best-1], grid[best+1])
            gain_rows.append([cond,side,gain,np.sqrt(objective(gain)/15)])
    csv_write('ganhos', ['condicao','sentido','ganho','rmse_planar_cm'], gain_rows)
    results['gains'] = gain_rows
    results['K_pulses_per_mm'] = kconv
    results['Kd_pulses_per_rad'] = kconv*dd
    results['source_sha256'] = hashlib.sha256(original).hexdigest()
    (OUT/'resumo.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    table('global', 'Erros médios e diferença por indicador (cm)', ['Indicador','Sem ajuste','Com ajuste','Diferença (\\%)'], [[name,*[fmt(results[k]['global_means_cm'][i]) for k in KEYS],fmt(100*observed[i]/results[KEYS[0]]['global_means_cm'][i],1)] for i,name in enumerate(['Absoluto','Relativo','Após rotação'])], 'lrrr')
    table('rotacao', 'Erro após rotação: média, DP amostral e viés por posição (cm)', ['Condição','Posição','Média','DP','Viés X','Viés Y'], [[NAMES[KEYS.index(row[0])],str(row[1]),*[fmt(v) for v in row[10:14]]] for row in pose_rows], 'lrrrrr')
    table('vies-relativo', 'Viés relativo por eixo antes da rotação (cm)', ['Condição','Posição','Viés X','Viés Y'], [[NAMES[KEYS.index(row[0])],str(row[1]),*[fmt(v) for v in row[8:10]]] for row in pose_rows], 'lrrr')
    table('ap-rp', 'Indicadores exploratórios AP e RP nas coordenadas absolutas (cm)', ['Posição','AP sem','AP com','RP sem','RP com'], [[str(j+2),fmt(iso_rows[j][2]),fmt(iso_rows[j+6][2]),fmt(iso_rows[j][3]),fmt(iso_rows[j+6][3])] for j in range(6)], 'crrrr')
    table('bootstrap', 'Diferença do erro médio e intervalo percentil do bootstrap (cm)', ['Indicador','Diferença sem - com','IC de 95\\%'], [[name,fmt(observed[i]),'['+fmt(ci[i,0])+'; '+fmt(ci[i,1])+']'] for i,name in enumerate(['Absoluto','Relativo','Após rotação'])], 'lrr')
    table('offsets', 'Deslocamento previsto pelos offsets e diferença dos baricentros (cm)', ['Posição',r'$\Delta X_{prev}$',r'$\Delta Y_{prev}$',r'$\Delta X_{med}$',r'$\Delta Y_{med}$'], [[str(row[0]),*[fmt(v) for v in row[4:8]]] for row in offset_rows], 'crrrr')
    table('ganhos', 'Ganho global descritivo por sentido e condição', ['Condição','Sentido',r'$g$','RMSE planar (cm)'], [[NAMES[KEYS.index(row[0])],row[1],fmt(row[2],4),fmt(row[3],3)] for row in gain_rows], 'llrr')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors = ['#176b91','#c76a20']
    fig, axes = plt.subplots(3,1,figsize=(7,8),sharex=True,layout='constrained')
    for i, ax in enumerate(axes):
        for k, name in enumerate(NAMES):
            rows=pose_rows[k*6:(k+1)*6]
            ax.errorbar(np.arange(2,8)+(k-.5)*.12,[r[2+4*i] for r in rows],yerr=[r[3+4*i] for r in rows],fmt='o-',capsize=3,color=colors[k],label=name)
        ax.set(ylabel='Erro (cm)',title=['Absoluto','Relativo ao centro inicial','Após rotação ajustada'][i])
        ax.grid(alpha=.2)
    axes[0].legend(ncol=2)
    axes[-1].set(xlabel='Posição',xticks=np.arange(2,8))
    fig.savefig(FIG/'erros.png',dpi=180)
    plt.close(fig)
    fig, axes=plt.subplots(1,2,figsize=(9,6),sharey=True,layout='constrained')
    for k,ax in enumerate(axes):
        corrected=rels[k] @ np.array(results[KEYS[k]]['rotation_matrix'])+target[0]
        ax.scatter(*positions[k].reshape(-1,2).T,s=16,alpha=.6,label='Medido',color=colors[k])
        ax.scatter(*corrected.reshape(-1,2).T,s=17,marker='+',label='Corrigido',color='#474747')
        ax.scatter(*target.T,s=40,marker='x',color='black',label='Alvo')
        for j,t in enumerate(target): ax.annotate(str(j+1),t,xytext=(5,5),textcoords='offset points')
        ax.set(title=NAMES[k],xlabel='X (cm)',aspect='equal',ylim=(3,54))
        ax.grid(alpha=.2)
        ax.legend(fontsize=8,loc='upper center')
    axes[0].set_ylabel('Y (cm)')
    fig.savefig(FIG/'coordenadas.png',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(7,7),layout='constrained')
    for i,ax in enumerate(axes):
        ax.hist(boot[:,i],bins=40,color=colors[0],alpha=.8)
        for bound in ci[i]: ax.axvline(bound,color=colors[1],linestyle='--')
        ax.set(title=['Absoluto','Relativo','Após rotação'][i],ylabel='Frequência')
    axes[-1].set_xlabel('Diferença do erro médio: sem - com (cm)')
    fig.savefig(FIG/'bootstrap.png',dpi=180)
    plt.close(fig)
    assert SOURCE.read_bytes() == original
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
