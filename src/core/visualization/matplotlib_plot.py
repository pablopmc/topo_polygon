from __future__ import annotations

from typing import Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon


Point2D = Tuple[float, float]


def _format_distancia(distancia: float) -> str:
    return f"{distancia:.2f}"


def _calcular_area(pontos: Sequence[Point2D]) -> float:
    area = 0.0
    for indice in range(len(pontos)):
        x1, y1 = pontos[indice]
        x2, y2 = pontos[(indice + 1) % len(pontos)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _calcular_perimetro(pontos: Sequence[Point2D]) -> float:
    perimetro = 0.0
    for indice in range(len(pontos)):
        x1, y1 = pontos[indice]
        x2, y2 = pontos[(indice + 1) % len(pontos)]
        dx = x2 - x1
        dy = y2 - y1
        perimetro += (dx**2 + dy**2) ** 0.5
    return perimetro


def _draw_north_arrow(ax, location: tuple[float, float] = (0.95, 0.1)) -> None:
    x, y = location
    arrow = FancyArrowPatch(
        posA=(x, y),
        posB=(x, y + 0.08),
        transform=ax.transAxes,
        arrowstyle="simple",
        mutation_scale=20,
        color="black",
    )
    ax.add_artist(arrow)
    ax.text(
        x,
        y + 0.09,
        "N",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )


def _build_scale_bar(ax, scale_length: float = 10.0, location: tuple[float, float] = (0.05, 0.05)) -> None:
    x0, y0 = location
    ax.annotate(
        "",
        xy=(x0 + scale_length, y0),
        xytext=(x0, y0),
        xycoords="axes fraction",
        textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-", lw=2, color="black"),
    )
    ax.text(
        x0 + scale_length / 2,
        y0 - 0.03,
        f"{scale_length:.0f} m",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
    )


def plot_poligono(
    pontos: Sequence[Point2D],
    distancias: Sequence[float] | None = None,
    titulo: str | None = None,
    mostrar_area: bool = True,
    mostrar_perimetro: bool = True,
    escala: float = 10.0,
    azimute_inicial: float | None = None,
) -> plt.Figure:
    """Gera um gráfico simples do polígono topográfico."""
    if len(pontos) < 2:
        raise ValueError("É necessário pelo menos dois pontos para desenhar o polígono.")

    pontos_plot = list(pontos)
    if pontos_plot[0] != pontos_plot[-1]:
        pontos_plot.append(pontos_plot[0])

    xs = [x for x, _ in pontos_plot]
    ys = [y for _, y in pontos_plot]

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect("equal", adjustable="box")

    polygon = Polygon(pontos_plot, closed=True, edgecolor="blue", facecolor="lightcyan", alpha=0.4, linewidth=1.8)
    ax.add_patch(polygon)
    ax.plot(xs, ys, marker="o", color="darkblue", linestyle="-", linewidth=1.5)

    for indice, (x, y) in enumerate(pontos_plot[:-1], start=1):
        ax.text(
            x,
            y,
            str(indice),
            fontsize=9,
            fontweight="bold",
            color="black",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1.5),
        )

    if distancias:
        for indice, distancia in enumerate(distancias):
            x1, y1 = pontos_plot[indice]
            x2, y2 = pontos_plot[indice + 1]
            xm = (x1 + x2) / 2.0
            ym = (y1 + y2) / 2.0
            ax.text(
                xm,
                ym,
                _format_distancia(distancia),
                fontsize=8,
                color="darkred",
                ha="center",
                va="center",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1.0),
            )

    if mostrar_area:
        ax.text(
            0.02,
            0.98,
            f"Área: {_calcular_area(pontos_plot[:-1]):.3f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8),
        )

    if mostrar_perimetro:
        ax.text(
            0.02,
            0.92,
            f"Perímetro: {_calcular_perimetro(pontos_plot[:-1]):.3f}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8),
        )

    if azimute_inicial is not None:
        from core.calculations.engine import _formatar_dms
        az_formatado = _formatar_dms(azimute_inicial)
        ax.text(
            0.02,
            0.86,
            f"Azimute Inicial: {az_formatado}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8),
        )

    if titulo:
        ax.set_title(titulo, fontsize=12, pad=14)

    _draw_north_arrow(ax)
    _build_scale_bar(ax, scale_length=escala)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_xlim(min(xs) - escala, max(xs) + escala)
    ax.set_ylim(min(ys) - escala, max(ys) + escala)

    return fig
