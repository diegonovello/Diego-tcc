# Material de reprodução do TCC

Este diretório reúne os programas, firmwares, dados e resultados citados no TCC
**“Estudo de aplicação de mecanismo articulado para robô do tipo snake”**.

A geometria adotada é:

- suporte fixo de 15 mm;
- três segmentos articulados de 150 mm;
- nove elos equivalentes de 50 mm;
- ponta física em 465 mm;
- marcador de medição 20 mm antes da ponta, em 445 mm na configuração reta.

As 130 coordenadas experimentais são preservadas em
`dados/ensaios_posicionamento_cm.json`. O arquivo de entrada recebido do autor
está em `dados/dados_ensaios_sem_offset_e_com_offset_atualizados.txt`.
As referências teóricas foram recalculadas separadamente pela cinemática do
marcador.

## Reprodução

Requer Python 3.10 ou superior.

```bash
python -m pip install -r codigo/verificacao/requirements.txt
python codigo/verificacao/importar_dados_definitivos.py
python codigo/verificacao/reproduzir.py
python codigo/verificacao/analisar_ensaios.py
python codigo/verificacao/analisar_vies.py
python codigo/verificacao/analisar_m1_isolado.py
python codigo/verificacao/reanalisar_experimentos.py
python codigo/verificacao/calcular_loo.py
python codigo/verificacao/auditar_offsets.py
python reanalisar_definitivos.py
```

Os ajustes de rotação e ganho são análises retrospectivas. A validação
`leave-one-out` exclui uma posição por rodada, mas permanece condicionada aos
offsets escolhidos anteriormente. Os arquivos não demonstram validação física
independente em novas configurações.

O arquivo `codigo/MANIFESTO_SHA256.txt` contém os hashes dos arquivos de código
incluídos neste pacote.
