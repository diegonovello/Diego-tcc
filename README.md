# Cinematica do Robo Snake

Este repositorio contem os codigos usados para a modelagem cinematica direta e inversa de um robo do tipo snake composto por tres modulos, com tres juntas equivalentes por modulo.

## Estrutura

- `src/`: scripts Python da modelagem cinematica.
- `notebooks/`: notebooks Jupyter usados no desenvolvimento e validacao.
- As figuras de referência podem ser geradas localmente pelos scripts; os arquivos PNG e PDF do TCC II não são distribuídos no repositório.
- `docs/`: relatorio em PDF da cinematica direta e inversa.

## Parametros principais

- Numero de modulos: 3
- Juntas por modulo: 3
- Numero total de juntas equivalentes: 9
- Distancia centro-centro entre juntas: 15,17 mm
- Ponto de referencia da ponta: (-62,39; 115,51) mm

## Como executar

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Execute os scripts principais:

```bash
python src/cinematica_direta_basica.py
python src/cinematica_inversa_basica.py
```

Ou abra os notebooks da pasta `notebooks/` no Jupyter, VS Code ou ambiente equivalente.

## Observacao

Os materiais de aula do professor foram usados como referencia metodologica para a formulacao com matrizes homogeneas, mas nao foram incluidos neste repositorio.

## Implementação preliminar do TCC II

Os materiais anteriores de nove juntas independentes foram preservados. A implementação a seguir agrupa as juntas em três segmentos e utiliza a convenção de ensaio vertical: base na origem, X lateral e Y para cima. A configuração reta tem ponta em `(0; 136,53)` mm. O programa Arduino recebe **X;Y em centímetros**, não em milímetros.

| Arquivo/pasta | Finalidade |
| --- | --- |
| `arduino/teste_bancada_uno/teste_bancada_uno.ino` | Teste lento com Uno e DM556T: seleciona um motor e gera 10 ou 100 pulsos, sem cinemática ou PI. |
| `arduino/cinematica_xy/cinematica_xy.ino` | Entrada cartesiana e cálculo da cinemática inversa, cabos e passos ideais; **não gera pulsos**. |
| `arduino/cinematica_xy_movimento/` | Nova versão experimental com prévia, confirmação `mover`, pulsos sequenciais M1 → M2 → M3 e rampa; bloqueada por padrão até conferir a calibração e a intertrava. |
| `arduino/cinematica_xy/ModeloPlanar.h` | Cinemática direta, Jacobiano 2x3 e solução amortecida para três segmentos de três juntas. |
| `arduino/cinematica_xy/Transmissao.h` | Aproximação cumulativa do recolhimento dos cabos e conversão em destinos nominais de passos. |
| `arduino/cinematica_xy/validar_modelo.py` | Referência numérica desktop para conferir Jacobiano, inversa e transmissão; não executa o binário AVR. |
| `src/tcc2/desenhar_posicoes.py` | Gera seis figuras individuais dos casos planares usados no TCC, cada uma em PNG e PDF. |
| `figuras/tcc2/` (saída local) | Pasta criada ao executar o gerador; as imagens não são versionadas. |

### Reproduzir a conferência numérica e os desenhos

Na raiz do repositório, com Python 3.10 ou superior:

```bash
python -m pip install -r src/tcc2/requirements.txt
python arduino/cinematica_xy/validar_modelo.py
python src/tcc2/desenhar_posicoes.py
```

O último comando cria localmente seis figuras separadas, de `figuras/tcc2/posicao_caso_01.png` até `posicao_caso_06.png`, e os seis PDFs correspondentes. Não é gerada uma montagem única com os seis casos. Somente o código gerador é disponibilizado no repositório, sem as imagens prontas. Não precisa de Arduino ou motor. Os casos são `(0;0;0)`, `(20;20;20)`, `(0;0;20)`, `(10;20;15)`, `(-10;-20;-15)` e `(30;-10;20)` em graus de flexão total dos segmentos. Esses valores não são coordenadas X/Y nem ângulos dos motores.

### Abrir e conferir os sketches

Na Arduino IDE, abrir cada `.ino` na sua própria pasta e selecionar **Arduino Uno**. Manter `ModeloPlanar.h` e `Transmissao.h` junto de `cinematica_xy.ino`. Com Arduino CLI e o núcleo AVR instalados, a compilação pode ser reproduzida por:

```bash
arduino-cli compile --fqbn arduino:avr:uno arduino/teste_bancada_uno
arduino-cli compile --fqbn arduino:avr:uno arduino/cinematica_xy
arduino-cli compile --fqbn arduino:avr:uno arduino/cinematica_xy_movimento
```

Os programas cartesianos usam 115200 baud e final de linha. Exemplos: `0;13.653` para a ponta reta e `1.04480;13.51037` para o alvo do caso 3. A inversa pode encontrar outros ângulos para a mesma ponta. As instruções da simulação estão em [LEIA_ME.md](arduino/cinematica_xy/LEIA_ME.md).

### Nova versão com movimento real

O sketch [cinematica_xy_movimento](arduino/cinematica_xy_movimento/) preserva os dois programas anteriores. Ele calcula a prévia e executa os pulsos somente após `mover`, com referência manual, armação explícita, limites, sequência exclusiva M1 (base/A) → M2 (intermediário/B) → M3 (distal/C) e rampa por motor. Não existe opção de pulsos simultâneos; as flexões intermediárias também são conferidas. Também aceita `caso 1` até `caso 6` para preparar as flexões exatas dos desenhos.

**Antes de usar:** ler o [guia completo](arduino/cinematica_xy_movimento/LEIA_ME.md). As quatro confirmações em `ConfiguracaoMovimento.h` são distribuídas como `false`; só devem ser alteradas depois de verificar fisicamente geometria, sentidos, retorno/tensão e capacidade da fonte. Os drivers parados ainda podem consumir corrente; seu torque não é cortado automaticamente. Há uma intertrava lógica por contato NC entre D8 e GND; ela não substitui o corte físico independente da potência.

O arquivo [VERIFICACAO.md](arduino/cinematica_xy_movimento/VERIFICACAO.md) registra a compilação e os testes dos HEXs em AVR8js. A emulação conferiu contagens de GPIO e bloqueios, mas não valida driver, motores ou posicionamento físico. O código não executa PI, não lê encoder e não realiza homing automático. Nenhum firmware foi gravado automaticamente no Arduino.

### Uso de IA e limites

**Os programas e scripts acrescentados para o TCC II foram elaborados com auxílio de inteligência artificial — Codex (OpenAI)**, a partir dos dados fornecidos pelo autor. A mesma assistência foi utilizada na geração dos desenhos e na redação explicativa correspondente. O escopo e as limitações estão em [Uso de IA no TCC II](docs/USO_DE_IA_TCC2.md).

Os resultados são teóricos. Os testes numéricos e a compilação não demonstram precisão física. Redução, raio efetivo, afastamento, retorno e tensão dos cabos ainda exigem calibração. A gravidade não é modelada. O teste de bancada gera movimento real; o comando de parada não desenergiza o driver e não é parada de emergência. Conferir a revisão do DM556T, a ligação dos oito fios e os limites elétricos antes de energizar.
