"""Referencia numerica desktop da adaptacao 3 segmentos x 3 juntas.

Confere o Jacobiano por diferencas finitas e o comportamento do algoritmo
em float32. Nao executa o binario AVR e nao valida cabos ou motores.
Executar com Python e numpy. Os comprimentos e limites vem de ModeloPlanar.h.
"""
from pathlib import Path
import math
import re
import numpy as np

header = Path(__file__).with_name("ModeloPlanar.h").read_text(encoding="utf-8")

def parametro(nome):
    return float(re.search(rf"{nome}\s*=\s*([0-9.]+)f", header).group(1))

L = parametro("ELO_CM")
RAD = parametro("RAD")
LIMITE = 45 * RAD
TOL = parametro("TOLERANCIA_CM")
AMORT = parametro("AMORTECIMENTO_CM")

def fk(q):
    # Independente do acumulador reverso utilizado no C++.
    phi = np.cumsum(np.repeat(np.asarray(q) / 3, 3))
    return L * np.array([np.sin(phi).sum(), np.cos(phi).sum()])

def jac(q):
    phi = np.cumsum(np.repeat(np.asarray(q, dtype=np.float32) / 3, 3))
    xs, ys = L * np.cos(phi), -L * np.sin(phi)
    j = np.zeros((2, 3), dtype=np.float32)
    sx = np.float32(0)
    sy = np.float32(0)
    for i in reversed(range(9)):
        sx += xs[i]
        sy += ys[i]
        j[0, i // 3] += sx / 3
        j[1, i // 3] += sy / 3
    return j

def resolver(alvo):
    seeds = [np.zeros(3), np.full(3, 5*RAD), np.full(3, -5*RAD),
             np.array([8, -8, 8])*RAD, np.array([-8, 8, -8])*RAD]
    for seed in seeds:
        q = seed.astype(np.float32)
        for _ in range(300):
            erro = alvo - fk(q)
            norma = np.linalg.norm(erro)
            if norma <= TOL:
                return q, norma
            j = jac(q)
            a = np.float32(AMORT**2) + np.sum(j[0]*j[0])
            b = np.sum(j[0]*j[1])
            d = np.float32(AMORT**2) + np.sum(j[1]*j[1])
            det = a*d-b*b
            if not math.isfinite(det) or det <= 1e-9:
                break
            u = np.array([(d*erro[0]-b*erro[1])/det,
                          (a*erro[1]-b*erro[0])/det], dtype=np.float32)
            dq = j.T @ u
            maximum = np.max(np.abs(dq))
            if not np.all(np.isfinite(dq)) or maximum < 1e-8:
                break
            scale = min(1., 5*RAD/maximum)
            for _ in range(8):
                cand = np.clip(q + scale*dq, -LIMITE, LIMITE).astype(np.float32)
                if np.linalg.norm(alvo-fk(cand)) < norma:
                    q = cand
                    break
                scale *= .5
            else:
                break
    return None, None

def main():
    assert np.allclose(fk(np.zeros(3)), [0, 9*L])
    rng = np.random.default_rng(42)
    max_diff = 0.
    for _ in range(30):
        q = rng.uniform(-LIMITE, LIMITE, 3)
        eps = 1e-5
        finite = np.column_stack([
            (fk(q+np.eye(3)[k]*eps)-fk(q-np.eye(3)[k]*eps))/(2*eps)
            for k in range(3)])
        diff = np.max(np.abs(jac(q)-finite))
        max_diff = max(max_diff, diff)
        assert diff < 1e-4, (q, diff)
    print(f"PASS: Jacobiano 2x3, 30 configuracoes; diferenca maxima {max_diff:.8f} cm/rad")
    for graus in ([0, 0, 0], [20, 20, 20], [0, 0, 20],
                  [10, 20, 15], [-10, -20, -15], [30, -10, 20]):
        alvo = fk(np.deg2rad(graus))
        q, error = resolver(alvo)
        assert q is not None, (graus, alvo)
        assert error <= TOL and np.all(np.abs(q) <= LIMITE+1e-6)
        print(f"PASS: alvo {alvo[0]:.5f};{alvo[1]:.5f} cm | erro {error:.6f} cm")
    assert np.linalg.norm([20,20]) > 9*L
    print(f"PASS: alvo 20;20 fora do alcance radial de {9*L:.3f} cm")
    # Referencia da transmissao cumulativa, independente da inversa.
    transmissao = Path(__file__).with_name('Transmissao.h').read_text(encoding='utf-8')
    def valor(nome):
        return float(re.search(rf'{nome}\s*=\s*([0-9.]+)f', transmissao).group(1))
    d = valor('AFASTAMENTO_CABO_CM')
    raio = valor('DIAMETRO_CARRETEL_CM') / 2
    reducao = valor('REDUCAO_MOTOR_SAIDA')
    pulsos = valor('PULSOS_POR_VOLTA_MOTOR')
    escala = pulsos * reducao / (2*math.pi*raio)
    def cabos(graus):
        return d*np.cumsum(np.deg2rad(graus))
    assert np.allclose(cabos([20,0,0]), [d*math.radians(20)]*3)
    assert np.allclose(cabos([0,0,20])[:2], 0)
    assert np.allclose(cabos([20,-20,0])[1:], 0)
    assert np.allclose(cabos([-20,-20,-20]), -cabos([20,20,20]))
    assert np.allclose(cabos([0,0,0]), 0)
    passos = np.rint(cabos([20,20,20])*escala).astype(int)
    assert np.array_equal(passos, [84,169,253])
    referencias = [np.zeros(3,dtype=int), passos, np.zeros(3,dtype=int)]
    assert np.array_equal(np.diff(referencias,axis=0).sum(axis=0), np.zeros(3))
    print(f'PASS: transmissao cumulativa; 20/20/20 graus -> {passos.tolist()} passos ideais')
    print("Referencia desktop aprovada; nao e validacao fisica ou execucao do binario AVR.")

if __name__ == '__main__':
    main()
