# Reanálise atualizada em 22/11/2026

Referência reta: 44,5 cm; último elo efetivo: 3 cm. Para reproduzir, siga `../../LEIA_ME.md`. Os valores atuais estão em `resumo.json` e `validacao_loo.json`. Os intervalos de bootstrap das diferenças ficam acima de zero; os ganhos são superiores a 1 e extrapolam os limites articulares nas posições extremas.

## Histórico anterior (não usar seus números como resultados atuais)

# Reanálise experimental da v2 — 17/11/2026

Os 130 pares de coordenadas são lidos diretamente de `dados/ensaios_posicionamento_cm.json`. Nenhuma medição foi alterada. São 5 baterias por condição, 6 posições de teste e 7 leituras do centro por bateria. Os 60 pontos de teste alimentam os indicadores; os centros iniciais referenciam os deslocamentos, e os retornos permanecem na análise original.

## Reprodução

Requisitos: Python 3.10 ou superior, NumPy e Matplotlib.

```sh
python -m pip install numpy matplotlib
python codigo/verificacao/reanalisar_experimentos.py
```

O script gera seis CSV, resumo JSON, seis tabelas LaTeX e três gráficos PNG. Verifica a geometria contra os sete alvos originais, a ortogonalidade e o determinante da rotação, o objetivo quadrático do ajuste e a preservação do arquivo de entrada. O SHA256 da entrada consta do resumo JSON.

- `leituras_corrigidas.csv`: coordenadas absolutas e corrigidas; três erros por leitura.
- `indicadores_posicao.csv`: média, DP amostral e vieses X/Y dos três indicadores.
- `indicadores_exploratorios.csv`: AP e RP nas coordenadas absolutas.
- `bootstrap.csv`: 10.000 reduções reamostradas, semente 20261117.
- `offsets.csv`: equivalência angular, deslocamento previsto/medido e extrapolação angular.
- `ganhos.csv`: ajuste escalar por sentido e condição, com RMSE planar.

## Convenções e limites

Rotação Procrustes em vetores-linha: P @ R; ângulo aplicado positivo anti-horário, calculado por atan2(R[0,1], R[0,0]). Ajuste único por condição, após subtrair o centro inicial de cada bateria. Sem escala, reflexão ou translação livre adicional. Ajuste e avaliação na mesma amostra.

Bootstrap em blocos completos de bateria, com sorteios independentes entre condições (pareamento não documentado). Rotação reestimada a cada réplica; intervalos percentis, sem correção de viés. A contagem nula de reduções não positivas não demonstra probabilidade populacional menor que 0,01%.

Ganhos ajustados nos deslocamentos relativos, sem rotação e sem acrescentar novamente os offsets. Busca em [0,5; 1,5], grade de 2.001 valores e refinamento por seção áurea; mínimos interiores. RMSE usa 15 distâncias quadráticas, não 30 componentes escalares.

Offsets: ordem dos cordões c1/c2/c3 = M2/M3/M1. A previsão é sem saturação. Posições 2, 6 e 7 ultrapassam 45 graus por segmento ao somar os incrementos: são extrapolações matemáticas, não posições admissíveis validadas.

Os cenários de leitura de 1 mm são hipóteses de sensibilidade, não especificações instrumentais verificadas. AP/RP são exploratórios e não estabelecem conformidade ISO 9283. O bootstrap não inclui todos os erros sistemáticos.

## Conferência com a análise fornecida

Reproduzidos erros globais, rotações, AP/RP, offsets e ganhos. O IC relativo desta execução é [1,48; 1,89] cm, frente a aproximadamente [1,49; 1,90] cm no texto recebido. O texto não forneceu o script completo nem a semente; a v2 documenta seu próprio sorteio. O IC após rotação é [1,51; 1,86] cm.

K é calculado sem arredondamento: 5,658842421... pulsos/mm. Kd = 121,665112052... pulsos/rad; usar K arredondado para 5,65884 produz 121,66506. Essa diferença não altera a interpretação.

Alguns valores da tabela após rotação diferem em 0,01 cm do texto fornecido: médias com ajuste nas posições 5 e 7 são 0,79 e 1,50 cm nesta reprodução; viés Y sem ajuste na posição 6 é 1,95 cm. A v2 usa os resultados recalculados a partir dos dados originais, sem ajustar números para coincidir com o texto recebido.
