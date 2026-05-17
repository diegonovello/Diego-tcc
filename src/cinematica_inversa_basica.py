from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


N_MODULES = 3
JOINTS_PER_MODULE = 3
N_JOINTS = N_MODULES * JOINTS_PER_MODULE

JOINT_CENTER_DISTANCE_MM = 15.17
LINK_LENGTH_M = JOINT_CENTER_DISTANCE_MM / 1000


def cinematica_direta(q_degrees: np.ndarray, link_length: float = LINK_LENGTH_M) -> np.ndarray:
    """Calcula as posicoes das juntas e da ponta para um robo snake planar."""
    if len(q_degrees) != N_JOINTS:
        raise ValueError(f"Use exatamente {N_JOINTS} angulos.")

    q_radians = np.deg2rad(q_degrees)
    phi = np.cumsum(q_radians)

    x_steps = link_length * np.cos(phi)
    y_steps = link_length * np.sin(phi)

    x = np.concatenate([[0.0], np.cumsum(x_steps)])
    y = np.concatenate([[0.0], np.cumsum(y_steps)])

    return np.column_stack([x, y])


def jacobiano_ponta(q_radians: np.ndarray, link_length: float = LINK_LENGTH_M) -> np.ndarray:
    """Calcula o Jacobiano planar da posicao da ponta em relacao aos angulos."""
    phi = np.cumsum(q_radians)
    jac = np.zeros((2, len(q_radians)))

    for j in range(len(q_radians)):
        jac[0, j] = -link_length * np.sum(np.sin(phi[j:]))
        jac[1, j] = link_length * np.sum(np.cos(phi[j:]))

    return jac


def cinematica_inversa(
    alvo_mm: np.ndarray,
    q_inicial_graus: np.ndarray | None = None,
    max_iter: int = 500,
    tolerancia_mm: float = 0.01,
    amortecimento: float = 0.05,
    passo_maximo_graus: float = 5.0,
) -> tuple[np.ndarray, list[float]]:
    """Resolve a cinematica inversa da ponta usando Jacobiano amortecido."""
    alvo_m = np.asarray(alvo_mm, dtype=float) / 1000
    if q_inicial_graus is None:
        q = np.zeros(N_JOINTS, dtype=float)
    else:
        q = np.deg2rad(np.asarray(q_inicial_graus, dtype=float))

    erros_mm: list[float] = []
    tolerancia_m = tolerancia_mm / 1000
    passo_maximo = np.deg2rad(passo_maximo_graus)

    for _ in range(max_iter):
        posicoes = cinematica_direta(np.rad2deg(q))
        ponta = posicoes[-1]
        erro = alvo_m - ponta
        erro_norma = float(np.linalg.norm(erro))
        erros_mm.append(erro_norma * 1000)

        if erro_norma < tolerancia_m:
            break

        jac = jacobiano_ponta(q)
        lhs = jac @ jac.T + (amortecimento**2) * np.eye(2)
        delta_q = jac.T @ np.linalg.solve(lhs, erro)

        delta_norma = float(np.linalg.norm(delta_q))
        if delta_norma > passo_maximo:
            delta_q = delta_q * (passo_maximo / delta_norma)

        q = q + delta_q

    return np.rad2deg(q), erros_mm


def desenhar_resultado(posicoes: np.ndarray, alvo_mm: np.ndarray) -> None:
    """Desenha o robo e o alvo da cinematica inversa."""
    cores = ["#0b36b8", "#111111", "#3267d6"]

    fig, ax = plt.subplots(figsize=(7, 5))
    for modulo in range(N_MODULES):
        inicio = modulo * JOINTS_PER_MODULE
        fim = inicio + JOINTS_PER_MODULE
        trecho = posicoes[inicio : fim + 1]
        ax.plot(
            trecho[:, 0] * 1000,
            trecho[:, 1] * 1000,
            "-o",
            linewidth=2.5,
            color=cores[modulo],
            label=f"Modulo {modulo + 1}",
        )

    ax.scatter([0], [0], s=90, color="#ff7f0e", label="Base / origem")
    ax.scatter([posicoes[-1, 0] * 1000], [posicoes[-1, 1] * 1000], s=90, color="#1f77b4", label="Ponta / fim")
    ax.scatter([alvo_mm[0]], [alvo_mm[1]], marker="x", s=120, color="red", label="Alvo")
    ax.set_title("Cinematica inversa - robo snake")
    ax.set_xlabel("X [mm]")
    ax.set_ylabel("Y [mm]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.show()


if __name__ == "__main__":
    alvo = np.array([-62.39, 115.51])
    q_inicial = np.zeros(N_JOINTS)

    q_solucao, erros = cinematica_inversa(alvo, q_inicial)
    posicoes_finais = cinematica_direta(q_solucao)

    print("Alvo [mm]:", alvo)
    print("Angulos encontrados [graus]:", np.round(q_solucao, 2))
    print("Ponta calculada [mm]:", np.round(posicoes_finais[-1] * 1000, 2))
    print("Erro final [mm]:", round(erros[-1], 4))

    desenhar_resultado(posicoes_finais, alvo)
