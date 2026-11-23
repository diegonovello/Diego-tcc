# Reanálise da v2 em 17/11/2026

Os registros originais foram preservados. Resultados adicionais em `reanalise/`, gerados por `codigo/verificacao/reanalisar_experimentos.py`: rotação, AP/RP exploratórios, bootstrap, offsets e ganho global. Os cenários de 1 mm não substituem a caracterização instrumental. Ver `reanalise/LEIA_ME.md`.

# Nova campanha recebida em 16/11/2026

130 pares de coordenadas em cm, transcritos da nova tabela do autor; substituem os registros anteriores na análise atual. Mesma montagem e ajustes de pulsos confirmados pelo autor: M1/M2/M3 esquerda +5/+5/+5, direita +65/+5/+5.

As medidas não foram modificadas. A fonte definitiva desta revisão é `dados_ensaios_sem_offset_e_com_offset_atualizados.txt`. As referências foram derivadas do modelo do marcador a 445 mm, com precisão completa; nas posições 6 e 7, $Y=12,073969712740634$ cm. As colunas de referência do arquivo recebido divergiam da cinemática e foram mantidas apenas como evidência de entrada, não como medições. Data exata da coleta não informada; 16/11 é a data de recebimento.

Reproduzir: executar codigo/verificacao/analisar_ensaios.py e analisar_vies.py. Erro absoluto: distância ao alvo. Erro relativo: desconta o deslocamento do centro inicial de cada bateria. Retornos comparados ao início da própria bateria. Não foi estimada incerteza instrumental. Firmware da coleta sem hash identificado. Backups históricos foram movidos para `../../_arquivo_tcc2_v4_2026-11-23/temporarios/`.

## Remedição das posições 4 e 5 com ajuste

Substituídas dez duplas X/Y conforme a nova tabela do autor. Demais leituras preservadas, inclusive retornos e série sem ajuste. A cópia anterior está no arquivo histórico indicado acima.
