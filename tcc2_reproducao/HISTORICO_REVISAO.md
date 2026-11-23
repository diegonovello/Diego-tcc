# TCC2 v4 — referência corrigida em 22/11/2026

Estado atual: suporte fixo de 15 mm, nove elos equivalentes de 50 mm, ponta física em 465 mm e marcador 20 mm antes da ponta (445 mm na posição reta).

As medições da campanha principal foram consolidadas a partir de `dados/dados_ensaios_sem_offset_e_com_offset_atualizados.txt`, sem alteração de seus 130 pares. As referências teóricas foram recalculadas separadamente pela geometria do marcador a 445 mm. As colunas de referência divergentes do arquivo de entrada não foram tratadas como medições.

Resultados atuais: erro absoluto médio 4,36/3,94 cm (sem/com offsets), redução de 9,5%; erro relativo 4,48/4,30 cm; após rotação 4,44/4,28 cm. O erro absoluto melhora nas posições 2, 4, 5 e 7 e piora nas posições 3 e 6. Somente o intervalo de bootstrap da diferença absoluta fica acima de zero. Ganhos acima de 1 extrapolam o limite angular nas posições extremas; são ajustes descritivos.

Reprodução (Python 3.10+):

```sh
python -m pip install -r codigo/verificacao/requirements.txt
python codigo/verificacao/reproduzir.py
python codigo/verificacao/figuras_revisao.py
python codigo/verificacao/analisar_ensaios.py
python codigo/verificacao/analisar_vies.py
python codigo/verificacao/analisar_m1_isolado.py
python codigo/verificacao/reanalisar_experimentos.py
python codigo/verificacao/calcular_loo.py
python codigo/verificacao/auditar_offsets.py
pdflatex -interaction=nonstopmode main.tex
biber main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

`calcular_loo.py` agora lê o mesmo JSON da análise principal, sem duplicar medições no código. O firmware `codigo/sete_posicoes_revisado/` foi preservado: a mudança da posição do marcador não modifica os comandos nominais calculados a partir das flexões. `codigo/cinematica_xy/`, o perfil `--original`, os relatórios anteriores e os pacotes antigos são históricos; não representam a geometria atual. Em 23/11/2026, temporários, artefatos de compilação, pacotes antigos e materiais de revisão foram movidos para `../_arquivo_tcc2_v4_2026-11-23/`. Nenhuma alteração foi enviada ao GitHub ou ao Arduino.

## Histórico anterior — valores superados pela revisão acima

# Revisão final de 19/11/2026

Ver REVISAO_FINAL_V3_2026-11-19.md. Firmware de entrega: M1 5/65; histórico 25/5 em codigo/historico. O binário compilado nesta revisão não é o binário original da coleta.

# TCC2 v3 — corpo limitado a 45 páginas

Versão derivada da v2, preservada na pasta irmã. Ver REVISAO_V3_45_PAGINAS.md. Compilar main.tex com pdflatex; usar biber quando alterar referências. As tabelas e figuras complementares estão nos Apêndices D, E e F; os dados e resultados numéricos foram preservados.

# TCC2 v2 — reanálise de 17/11/2026

## Ensaio complementar de 18/11/2026

Coordenadas de M1 corrigidas e confirmadas: início positivo (+0,3;48,5) cm e negativo (−0,1;48,4) cm, com novas leituras finais/retornos. Ver `dados/m1_isolado/CORRECAO_2026-11-18.md`. Médias das distâncias de ida: 2,32 e 1,79 cm; desvios finais das séries: 1,02 e 0,50 cm.

Incluídos teste isolado de M1, seis ciclos com ±65 pulsos, observação com transferidor e fotografia. Ver `REVISAO_M1_2026-11-18.md`. Dados separados em `dados/m1_isolado`; executar `python codigo/verificacao/analisar_m1_isolado.py`. A flexão observada concentrou-se nas juntas identificadas como 8 e 9; o atrito nas conexões é discutido como hipótese não isolada experimentalmente. As notas de 17/11 sobre ausência desse teste são histórico anterior.

Entrada: `main.tex`. PDF: `main.pdf`. A v2 incorpora a reanálise dos ensaios na discussão e nas conclusões. Medições e firmware preservados. Consulte `REVISAO_V2_2026-11-17.md` e `dados/reanalise/LEIA_ME.md` para resultados, hipóteses e reprodução.

A revisão por blocos e as confirmações do autor estão em `REVISAO_BLOCOS_2026-11-17.md`: dez tentativas qualitativas na seleção dos offsets, sem retensionamento; teste isolado de M1, medições angulares e posições independentes não realizados. Resumo, Abstract, objetivos e dedução dos 95 pulsos atualizados. AP/RP aparecem na apresentação dos indicadores experimentais.

Executar `python codigo/verificacao/reanalisar_experimentos.py` (NumPy e Matplotlib) para gerar os seis CSV, as tabelas LaTeX, o resumo JSON e os três gráficos novos. Compilar com `pdflatex main.tex`, `biber main` e duas novas chamadas de `pdflatex main.tex`.

As notas abaixo são o histórico herdado da v1; afirmações sobre ausência de dados preenchidos ou análises pendentes não descrevem o estado atual.

# Histórico: novos ensaios

A nova campanha recebida em 16/11/2026 foi incorporada e reprocessada para a geometria de 485 mm. As notas abaixo sobre preservação de ensaios anteriores descrevem a etapa prévia e foram superadas. Ver dados/LEIA_ME.md.

## Revisão geométrica de 16/11/2026

Somente a teoria foi recalculada. Dados, figuras, estatísticas e texto dos ensaios permanecem preservados com as referências anteriores; não representam validação da geometria revisada. Firmware preservado.

## Atualização dos ensaios em 14/11/2026

Foram incorporadas cinco baterias por condição e as leituras de retorno. Ver dados/LEIA_ME.md e resultados_experimentais.tex. A configuração confirmada é +5/+5/+5 à esquerda e +65/+5/+5 à direita. Menções abaixo a medições pendentes ou ajustes anteriores descrevem a revisão prévia.

# TCC2 — revisão dimensional e firmware atual

Entrada: main.tex. PDF: main.pdf. Atualização em 14/11/2026.

- Geometria revisada em 16/11/2026: suporte fixo de 15 mm; segmentos móveis 150/150/150 mm; nove elos equivalentes de 50 mm; extensão rígida terminal de 20 mm. Ponta reta em (0;485) mm. Fixações longitudinais informadas em 165/315/465 mm; não são necessariamente eixos articulares.
- Limites ±15 graus por junta e ±45 por segmento. X lateral; Y ao longo do robô reto.
- d=21,5 mm condicionado a altura40 mm, caboØ3 mm, eixo centralizado e cabo por fora. Raio efetivo r=15 mm e 400 pulsos/volta exigem conferência de bancada. K=5,65884 pulsos/mm.
- Sete posições: reta; pares 2/3 (±20 em todos); 4/5 (±10/20/15); 6/7 (±45 em todos).
- Firmware atual congelado em codigo/sete_posicoes_revisado. Correções preliminares M1/M2/M3: esquerda -5/-5/-5; direita65/5/5. Retorno desfaz saldo emitido, em duas etapas. Sem encoder ou medição de X/Y.
- Código cartesiano antigo é histórico. Não confundir sua geometria com a versão atual.
- Resultados de reprodução em codigo/verificacao/dimensoes_fisicas; figuras em imagens/verificacao_dimensoes_fisicas. `python codigo/verificacao/reproduzir.py` gera o perfil atualizado. `--original` é cenário histórico.
- Nas posições6/7 a discretização limitada produz diferença de3,109mm do alvo ideal. Critério de aceitação experimental ainda deve ser definido antes da campanha.
- Fotos de montagem incluídas. Não há resultados_medidos.tex preenchido, nem precisão experimental demonstrada.

Compilar: pdflatex main.tex; biber main; pdflatex main.tex; pdflatex main.tex.
Manifesto SHA256 identifica a cópia local de código. Nenhuma alteração enviada ao GitHub ou Arduino nesta revisão.

## Atualização da auditoria experimental

Ver REVISAO_ORIENTADOR_2026-11-18.md para as posições usadas no ajuste e a divergência de parâmetros no firmware preservado.
