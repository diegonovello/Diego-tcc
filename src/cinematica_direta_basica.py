from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


N_MODULES = 3
JOINTS_PER_MODULE = 3
N_JOINTS = N_MODULES * JOINTS_PER_MODULE

MODULE_HEIGHT_MM = 29.17
MODULE_WIDTH_MM = 18.56
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


def desenhar_robo(positions: np.ndarray) -> None:
    """Desenha o robo no plano XY, separando os tres modulos."""
    colors = ["#0b36b8", "#111111", "#3267d6"]

    fig, ax = plt.subplots(figsize=(7, 5))
    for module_idx in range(N_MODULES):
        start = module_idx * JOINTS_PER_MODULE
        end = start + JOINTS_PER_MODULE
        module_positions = positions[start : end + 1]
        ax.plot(
            module_positions[:, 0] * 1000,
            module_positions[:, 1] * 1000,
            "-o",
            linewidth=2.5,
            color=colors[module_idx],
            label=f"Modulo {module_idx + 1}",
        )

    ax.scatter([positions[0, 0] * 1000], [positions[0, 1] * 1000], s=90, color="#ff7f0e", label="Base / origem")
    ax.scatter([positions[-1, 0] * 1000], [positions[-1, 1] * 1000], s=90, color="#1f77b4", label="Ponta / fim")
    ax.set_title("Cinematica direta - robo snake")
    ax.set_xlabel("X [mm]")
    ax.set_ylabel("Y [mm]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.show()


if __name__ == "__main__":
    q_exemplo = np.array([94.61, 17.87, 19.10, 10.48, -3.75, -15.83, -17.68, -5.46, 20.42])
    posicoes = cinematica_direta(q_exemplo)

    print("Comprimento entre juntas:", JOINT_CENTER_DISTANCE_MM, "mm")
    print("Angulos usados [graus]:", q_exemplo)
    print("Posicao da ponta [mm]:", np.round(posicoes[-1] * 1000, 2))

    desenhar_robo(posicoes)
