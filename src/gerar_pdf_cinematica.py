from __future__ import annotations

import base64
import html
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
IMG_DIR = ROOT / "imagens"

HTML_OUT = ROOT / "Cinematica_Robo_Snake_Direta_e_Indireta.html"
PDF_OUT = PROJECT_ROOT / "Cinematica_Robo_Snake_Direta_e_Indireta.pdf"

N_MODULES = 3
JOINTS_PER_MODULE = 3
N_JOINTS = N_MODULES * JOINTS_PER_MODULE

L_MM = 15.17
L = L_MM / 1000

TARGET_MM = np.array([-62.39, 115.51])
Q_DIRECT_DEG = np.array([94.61, 17.87, 19.10, 10.48, -3.75, -15.83, -17.68, -5.46, 20.42])
Q_INVERSE_DEG = np.array([93.13, 5.28, 6.74, 7.48, 7.52, 6.90, 5.70, 4.06, 2.11])


def image_to_data_uri(path: Path) -> str:
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def forward_kinematics(q_degrees: np.ndarray) -> np.ndarray:
    q = np.deg2rad(q_degrees)
    phi = np.cumsum(q)
    dx = L * np.cos(phi)
    dy = L * np.sin(phi)
    x = np.concatenate([[0.0], np.cumsum(dx)])
    y = np.concatenate([[0.0], np.cumsum(dy)])
    return np.column_stack([x, y])


def save_direct_validation_image() -> Path:
    positions = forward_kinematics(Q_DIRECT_DEG)
    colors = ["#0b36b8", "#111111", "#3267d6"]
    out = IMG_DIR / "cinematica_direta_validacao.png"

    fig, ax = plt.subplots(figsize=(7, 5), dpi=160)
    for module in range(N_MODULES):
        start = module * JOINTS_PER_MODULE
        end = start + JOINTS_PER_MODULE
        section = positions[start : end + 1] * 1000
        ax.plot(section[:, 0], section[:, 1], "-o", linewidth=2.4, color=colors[module], label=f"Modulo {module + 1}")

    tip_mm = positions[-1] * 1000
    ax.scatter([0], [0], s=90, color="#ff7f0e", label="Base / origem")
    ax.scatter([tip_mm[0]], [tip_mm[1]], s=90, color="#1f77b4", label="Ponta / fim")
    ax.scatter([TARGET_MM[0]], [TARGET_MM[1]], marker="x", s=130, color="red", label="Medida do desenho")
    ax.set_title("Validacao da cinematica direta")
    ax.set_xlabel("X [mm]")
    ax.set_ylabel("Y [mm]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def code_block(text: str) -> str:
    return f"<pre><code>{html.escape(text.strip())}</code></pre>"


def build_html() -> str:
    direct_positions = forward_kinematics(Q_DIRECT_DEG)
    inverse_positions = forward_kinematics(Q_INVERSE_DEG)
    direct_tip_mm = direct_positions[-1] * 1000
    inverse_tip_mm = inverse_positions[-1] * 1000
    direct_error_mm = float(np.linalg.norm(direct_tip_mm - TARGET_MM))
    inverse_error_mm = float(np.linalg.norm(inverse_tip_mm - TARGET_MM))

    direct_image = save_direct_validation_image()

    images = {
        "prancha": image_to_data_uri(IMG_DIR / "prancha_tecnica_referencia.png"),
        "direta": image_to_data_uri(direct_image),
        "inversa_alvo": image_to_data_uri(IMG_DIR / "cinematica_inversa_alvo.png"),
        "inversa_inicial": image_to_data_uri(IMG_DIR / "cinematica_inversa_pose_inicial.png"),
        "inversa_solucao": image_to_data_uri(IMG_DIR / "cinematica_inversa_solucao.png"),
        "inversa_convergencia": image_to_data_uri(IMG_DIR / "cinematica_inversa_convergencia.png"),
    }

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Cinematica Direta e Indireta do Robo Snake</title>
  <style>
    @page {{ size: A4; margin: 14mm; }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: Arial, Helvetica, sans-serif;
      color: #172033;
      line-height: 1.42;
      margin: 0;
      background: white;
      font-size: 12px;
    }}
    h1 {{ color: #0b4ea2; font-size: 26px; margin: 0 0 4px; }}
    h2 {{ color: #0b4ea2; font-size: 18px; margin: 22px 0 8px; border-bottom: 2px solid #0b4ea2; padding-bottom: 4px; }}
    h3 {{ color: #174f96; font-size: 14px; margin: 16px 0 6px; }}
    p {{ margin: 6px 0; }}
    ul {{ margin: 6px 0 6px 20px; padding: 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 11px; }}
    th, td {{ border: 1px solid #b9c6d8; padding: 6px 7px; text-align: left; }}
    th {{ background: #0b4ea2; color: white; }}
    .cover {{
      border: 2px solid #0b4ea2;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
    }}
    .subtitle {{ color: #48617d; font-size: 14px; }}
    .figure {{ margin: 10px 0 16px; page-break-inside: avoid; }}
    .figure img {{ width: 100%; max-height: 650px; object-fit: contain; border: 1px solid #c7d3e5; border-radius: 6px; }}
    .figure.small img {{ max-height: 390px; }}
    .caption {{ font-size: 10.5px; color: #4b5b70; margin-top: 4px; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .note {{ background: #eef5ff; border-left: 4px solid #0b4ea2; padding: 8px 10px; margin: 10px 0; }}
    pre {{ background: #f5f7fb; border: 1px solid #d3ddea; padding: 8px; border-radius: 6px; overflow-wrap: break-word; white-space: pre-wrap; font-size: 10.5px; }}
    .page-break {{ page-break-before: always; }}
  </style>
</head>
<body>
  <section class="cover">
    <h1>Cinematica Direta e Indireta do Robo Snake</h1>
    <div class="subtitle">Documento unico com desenvolvimento baseado no padrao do material do professor</div>
    <p><strong>Robo considerado:</strong> 3 modulos, 3 juntas por modulo, total de 9 juntas rotativas.</p>
    <p><strong>Convencao usada:</strong> origem no ponto inferior da montagem; ponta/fim no ponto superior.</p>
  </section>

  <h2>1. Prancha tecnica de referencia</h2>
  <p>A prancha tecnica reune as vistas e cotas usadas para definir o modelo cinematico.</p>
  <div class="figure">
    <img alt="Prancha tecnica de referencia do robo snake" src="{images['prancha']}">
    <div class="caption">Figura 1 - Prancha tecnica com as dimensoes principais do elo curvo e do suporte de articulacao.</div>
  </div>

  <table>
    <tr><th>Grandeza</th><th>Valor</th><th>Uso no modelo</th></tr>
    <tr><td>Distancia centro-centro entre juntas</td><td>15,17 mm</td><td>Comprimento de cada elo cinematico</td></tr>
    <tr><td>Deslocamento horizontal da pose de referencia</td><td>62,39 mm</td><td>Validacao da posicao final</td></tr>
    <tr><td>Deslocamento vertical centro-centro</td><td>115,51 mm</td><td>Validacao da posicao final</td></tr>
  </table>

  <h2>2. Matriz de Transformacao Homogenea Generica</h2>
  <p>Seguindo a convencao de Denavit-Hartenberg, a matriz homogenea de cada elo pode ser obtida pela multiplicacao dos rotacionais e translacionais:</p>
  {code_block("H = RotZ(theta) * TranslZ(d) * TranslX(a) * RotX(alpha)")}
  <p>As matrizes componentes sao:</p>
  {code_block("""
RotZ(theta) =
[ cos(theta)  -sin(theta)   0   0 ]
[ sin(theta)   cos(theta)   0   0 ]
[ 0            0            1   0 ]
[ 0            0            0   1 ]

TranslZ(d) =
[ 1  0  0  0 ]
[ 0  1  0  0 ]
[ 0  0  1  d ]
[ 0  0  0  1 ]

TranslX(a) =
[ 1  0  0  a ]
[ 0  1  0  0 ]
[ 0  0  1  0 ]
[ 0  0  0  1 ]

RotX(alpha) =
[ 1  0             0            0 ]
[ 0  cos(alpha)   -sin(alpha)  0 ]
[ 0  sin(alpha)    cos(alpha)  0 ]
[ 0  0             0           1 ]
  """)}

  <h2>3. Tabela DH do robo snake</h2>
  <p>O primeiro modelo e planar. Portanto, cada junta gira em torno do eixo z, com d = 0, a = L e alpha = 0.</p>
  <table>
    <tr><th>Elo</th><th>theta</th><th>d (m)</th><th>a (m)</th><th>alpha</th></tr>
    {''.join(f"<tr><td>{i}</td><td>theta{i}</td><td>0</td><td>{L:.5f}</td><td>0</td></tr>" for i in range(1, N_JOINTS + 1))}
  </table>
  <p>Com esses parametros, a matriz de cada elo se reduz a uma rotacao no plano seguida de uma translacao de comprimento L.</p>

  <h2>4. Cinematica direta</h2>
  <p>A cinematica direta calcula a posicao da ponta a partir dos angulos das juntas.</p>
  {code_block("T_total = H1 * H2 * H3 * ... * H9")}
  <p>A posicao final e obtida na ultima coluna da matriz homogenea total.</p>
  <table>
    <tr><th>Item</th><th>Resultado</th></tr>
    <tr><td>Angulos de referencia (graus)</td><td>{np.array2string(Q_DIRECT_DEG, precision=2, separator=', ')}</td></tr>
    <tr><td>Ponta calculada</td><td>{direct_tip_mm[0]:.2f} mm, {direct_tip_mm[1]:.2f} mm</td></tr>
    <tr><td>Alvo do desenho</td><td>{TARGET_MM[0]:.2f} mm, {TARGET_MM[1]:.2f} mm</td></tr>
    <tr><td>Erro total</td><td>{direct_error_mm:.4f} mm</td></tr>
  </table>
  <div class="figure small">
    <img alt="Validacao da cinematica direta" src="{images['direta']}">
    <div class="caption">Figura 2 - Pose obtida pela cinematica direta e comparacao com a medida do desenho.</div>
  </div>

  <h3>Forma planar equivalente</h3>
  <p>Como o robo e planar, tambem e possivel escrever a posicao por soma dos angulos acumulados:</p>
  {code_block("""
phi1 = theta1
phi2 = theta1 + theta2
...
phi9 = theta1 + theta2 + ... + theta9

x = L * [cos(phi1) + cos(phi2) + ... + cos(phi9)]
y = L * [sin(phi1) + sin(phi2) + ... + sin(phi9)]
  """)}

  <div class="page-break"></div>
  <h2>5. Cinematica indireta ou inversa</h2>
  <p>A cinematica indireta, tambem chamada de cinematica inversa, faz o caminho contrario da direta: a partir de uma posicao desejada da ponta, calcula-se um conjunto de angulos para as juntas.</p>
  <div class="note">
    Como o robo possui 9 juntas para posicionar a ponta no plano, existem varias solucoes possiveis. Por isso foi usado um metodo numerico por Jacobiano amortecido.
  </div>

  <h3>5.1 Alvo da ponta</h3>
  <p>Com a origem no ponto inferior da montagem, o alvo usado e:</p>
  {code_block("p_d = [-62,39 mm, 115,51 mm]")}
  <div class="figure small">
    <img alt="Alvo da cinematica inversa" src="{images['inversa_alvo']}">
    <div class="caption">Figura 3 - Alvo desejado para a ponta do robo.</div>
  </div>

  <h3>5.2 Pose inicial</h3>
  <p>O metodo numerico precisa de um chute inicial. Foi usada uma configuracao vertical simples.</p>
  <div class="figure small">
    <img alt="Pose inicial da cinematica inversa" src="{images['inversa_inicial']}">
    <div class="caption">Figura 4 - Pose inicial antes das iteracoes da cinematica inversa.</div>
  </div>

  <h3>5.3 Jacobiano amortecido</h3>
  <p>O Jacobiano relaciona pequenas variacoes dos angulos com pequenas variacoes na posicao da ponta:</p>
  {code_block("delta_p = J * delta_theta")}
  <p>A correcao angular foi calculada por:</p>
  {code_block("delta_theta = J^T * (J * J^T + lambda^2 * I)^-1 * erro")}
  <p>O termo lambda representa o amortecimento usado para melhorar a estabilidade numerica.</p>

  <h3>5.4 Solucao encontrada</h3>
  <table>
    <tr><th>Item</th><th>Resultado</th></tr>
    <tr><td>Angulos encontrados (graus)</td><td>{np.array2string(Q_INVERSE_DEG, precision=2, separator=', ')}</td></tr>
    <tr><td>Ponta calculada</td><td>{inverse_tip_mm[0]:.2f} mm, {inverse_tip_mm[1]:.2f} mm</td></tr>
    <tr><td>Alvo</td><td>{TARGET_MM[0]:.2f} mm, {TARGET_MM[1]:.2f} mm</td></tr>
    <tr><td>Erro total</td><td>{inverse_error_mm:.4f} mm</td></tr>
  </table>
  <div class="figure small">
    <img alt="Solucao encontrada pela cinematica inversa" src="{images['inversa_solucao']}">
    <div class="caption">Figura 5 - Solucao final encontrada pelo metodo numerico.</div>
  </div>

  <h3>5.5 Convergencia do erro</h3>
  <div class="figure small">
    <img alt="Grafico de convergencia do erro" src="{images['inversa_convergencia']}">
    <div class="caption">Figura 6 - Reducao do erro da ponta ao longo das iteracoes.</div>
  </div>

  <h2>6. Conclusao</h2>
  <p>A cinematica direta permitiu calcular a posicao da ponta a partir dos angulos das 9 juntas e validar o resultado com a prancha tecnica.</p>
  <p>A cinematica indireta foi resolvida numericamente pelo metodo do Jacobiano amortecido. O resultado chegou ao alvo com erro abaixo de 0,01 mm, suficiente para validar o desenvolvimento matematico inicial do robo snake.</p>
</body>
</html>
"""


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(build_html(), encoding="utf-8")
    print(HTML_OUT)
    print(PDF_OUT)


if __name__ == "__main__":
    main()
