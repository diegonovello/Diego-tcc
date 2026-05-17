from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import sympy as sp


@dataclass(frozen=True)
class DHRow:
    """One Denavit-Hartenberg row: theta, d, a, alpha."""

    theta: object
    d: object
    a: object
    alpha: object


def dh_transform(theta, d, a, alpha) -> sp.Matrix:
    """Symbolic homogeneous transform using standard DH convention."""
    return sp.Matrix(
        [
            [sp.cos(theta), -sp.sin(theta) * sp.cos(alpha), sp.sin(theta) * sp.sin(alpha), a * sp.cos(theta)],
            [sp.sin(theta), sp.cos(theta) * sp.cos(alpha), -sp.cos(theta) * sp.sin(alpha), a * sp.sin(theta)],
            [0, sp.sin(alpha), sp.cos(alpha), d],
            [0, 0, 0, 1],
        ]
    )


def dh_transform_numeric(theta: float, d: float, a: float, alpha: float) -> np.ndarray:
    """Numeric homogeneous transform using standard DH convention."""
    cth, sth = cos(theta), sin(theta)
    ca, sa = cos(alpha), sin(alpha)
    return np.array(
        [
            [cth, -sth * ca, sth * sa, a * cth],
            [sth, cth * ca, -cth * sa, a * sth],
            [0.0, sa, ca, d],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def planar_snake_dh(n_joints: int, link_length: float, joint_symbols: Sequence[object] | None = None) -> list[DHRow]:
    """Build a planar snake model with all revolute joints around z."""
    if joint_symbols is None:
        joint_symbols = sp.symbols(f"theta1:{n_joints + 1}")
    if len(joint_symbols) != n_joints:
        raise ValueError("joint_symbols must have exactly n_joints items")
    return [DHRow(theta=joint_symbols[i], d=0, a=link_length, alpha=0) for i in range(n_joints)]


def modular_planar_snake_dh(
    module_count: int,
    joints_per_module: int,
    link_lengths: float | Sequence[float],
    joint_symbols: Sequence[object] | None = None,
) -> list[DHRow]:
    """Build a planar snake model grouped by modules."""
    n_joints = module_count * joints_per_module
    if joint_symbols is None:
        joint_symbols = sp.symbols(f"theta1:{n_joints + 1}")
    if len(joint_symbols) != n_joints:
        raise ValueError("joint_symbols must have module_count * joints_per_module items")

    if isinstance(link_lengths, (int, float)):
        lengths = [float(link_lengths)] * n_joints
    else:
        lengths = [float(length) for length in link_lengths]
        if len(lengths) != n_joints:
            raise ValueError("link_lengths must be a scalar or have one value per joint")

    return [DHRow(theta=joint_symbols[i], d=0, a=lengths[i], alpha=0) for i in range(n_joints)]


def chain_transform(rows: Iterable[DHRow]) -> sp.Matrix:
    """Symbolic transform from base to end-effector."""
    transform = sp.eye(4)
    for row in rows:
        transform = transform * dh_transform(row.theta, row.d, row.a, row.alpha)
    return sp.simplify(transform)


def chain_transform_numeric(rows: Sequence[DHRow], q_values: Sequence[float]) -> np.ndarray:
    """Numeric transform from base to end-effector."""
    if len(rows) != len(q_values):
        raise ValueError("rows and q_values must have the same length")

    transform = np.eye(4)
    for row, q in zip(rows, q_values):
        theta = float(q)
        d = float(row.d)
        a = float(row.a)
        alpha = float(row.alpha)
        transform = transform @ dh_transform_numeric(theta, d, a, alpha)
    return transform


def joint_positions(rows: Sequence[DHRow], q_values: Sequence[float]) -> np.ndarray:
    """Return base, joint and tip positions as an array with shape (n+1, 3)."""
    if len(rows) != len(q_values):
        raise ValueError("rows and q_values must have the same length")

    transform = np.eye(4)
    positions = [transform[:3, 3].copy()]
    for row, q in zip(rows, q_values):
        transform = transform @ dh_transform_numeric(float(q), float(row.d), float(row.a), float(row.alpha))
        positions.append(transform[:3, 3].copy())
    return np.array(positions)


def serpenoid_angles(
    n_joints: int,
    amplitude: float,
    phase_step: float,
    time_phase: float = 0.0,
    offset: float = 0.0,
) -> np.ndarray:
    """Generate a simple serpenoid angle pattern for a snake robot."""
    i = np.arange(n_joints)
    return offset + amplitude * np.sin(time_phase + i * phase_step)


def end_effector_position(rows: Sequence[DHRow], q_values: Sequence[float]) -> np.ndarray:
    """Return the xyz position of the robot tip."""
    return chain_transform_numeric(rows, q_values)[:3, 3]


def numeric_position_jacobian(rows: Sequence[DHRow], q_values: Sequence[float], eps: float = 1e-6) -> np.ndarray:
    """Finite-difference Jacobian for the tip position."""
    q = np.asarray(q_values, dtype=float)
    base = end_effector_position(rows, q)
    jac = np.zeros((3, len(q)))

    for idx in range(len(q)):
        q_step = q.copy()
        q_step[idx] += eps
        jac[:, idx] = (end_effector_position(rows, q_step) - base) / eps

    return jac


def inverse_kinematics_position(
    rows: Sequence[DHRow],
    target_xyz: Sequence[float],
    q_initial: Sequence[float] | None = None,
    max_iter: int = 500,
    tolerance: float = 1e-5,
    damping: float = 1e-3,
    step_limit: float = 0.2,
) -> tuple[np.ndarray, list[float]]:
    """Solve tip-position IK with damped least squares."""
    target = np.asarray(target_xyz, dtype=float)
    q = np.zeros(len(rows), dtype=float) if q_initial is None else np.asarray(q_initial, dtype=float)
    errors: list[float] = []

    for _ in range(max_iter):
        current = end_effector_position(rows, q)
        error = target - current
        error_norm = float(np.linalg.norm(error))
        errors.append(error_norm)
        if error_norm < tolerance:
            break

        jac = numeric_position_jacobian(rows, q)
        lhs = jac @ jac.T + (damping**2) * np.eye(3)
        delta = jac.T @ np.linalg.solve(lhs, error)
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm > step_limit:
            delta = delta * (step_limit / delta_norm)
        q = q + delta

    return q, errors


def plot_snake_2d(positions: np.ndarray, ax=None, title: str = "Snake robot - plano XY"):
    """Plot a 2D top view of the snake robot."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    ax.plot(positions[:, 0], positions[:, 1], "-o", linewidth=2)
    ax.scatter([positions[0, 0]], [positions[0, 1]], s=80, label="base")
    ax.scatter([positions[-1, 0]], [positions[-1, 1]], s=80, label="ponta")
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax


def plot_snake_modules_2d(
    positions: np.ndarray,
    joints_per_module: int,
    ax=None,
    title: str = "Snake robot modular - plano XY",
):
    """Plot a 2D top view with one color per module."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))

    colors = ["#0b36b8", "#111111", "#3267d6", "#555555"]
    n_segments = len(positions) - 1
    module_count = int(np.ceil(n_segments / joints_per_module))

    for module_idx in range(module_count):
        start = module_idx * joints_per_module
        end = min(start + joints_per_module, n_segments)
        module_positions = positions[start : end + 1]
        ax.plot(
            module_positions[:, 0],
            module_positions[:, 1],
            "-o",
            linewidth=2.5,
            color=colors[module_idx % len(colors)],
            label=f"modulo {module_idx + 1}",
        )

    ax.scatter([positions[0, 0]], [positions[0, 1]], s=90, color="#33a852", label="base")
    ax.scatter([positions[-1, 0]], [positions[-1, 1]], s=90, color="#d93025", label="ponta")
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend()
    return ax


def plot_snake_3d(positions: np.ndarray, ax=None, title: str = "Snake robot - 3D"):
    """Plot a 3D view of the snake robot."""
    if ax is None:
        fig = plt.figure(figsize=(7, 5))
        ax = fig.add_subplot(111, projection="3d")

    ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], "-o", linewidth=2)
    ax.scatter([positions[0, 0]], [positions[0, 1]], [positions[0, 2]], s=80, label="base")
    ax.scatter([positions[-1, 0]], [positions[-1, 1]], [positions[-1, 2]], s=80, label="ponta")
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    return ax
