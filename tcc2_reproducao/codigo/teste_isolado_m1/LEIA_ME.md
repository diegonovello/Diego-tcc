# Teste isolado de M1 — 18/11/2026

Sketch separado para Arduino Uno / DM556. Não altera os códigos anteriores. Compilado, mas não enviado à placa nem ensaiado fisicamente.

## Ligações mantidas

- M1: STEP/PUL no pino 2 e DIR no pino 5.
- M2: STEP 6 / DIR 7; M3: STEP 8 / DIR 9. Sem pulsos durante o teste; não desligar automaticamente os drivers que sustentam os outros cordões.
- Mantém a interface existente: STEP ativo em LOW, largura 2 ms, período 20 ms (50 pulsos/s). DIR HIGH = comando positivo. Confirmar o sentido físico do cordão na bancada.
- Sem offsets, encoder, homing ou leitura de posição. O contador registra pulsos comandados completos, não passos mecânicos confirmados.

## Como usar

1. Abrir `teste_isolado_m1.ino`, selecionar Arduino Uno e a porta correta, compilar e carregar manualmente.
2. Abrir Monitor Serial em **115200 baud** com final de linha **Nova linha** (ou Ambos NL e CR).
3. Colocar fisicamente o robô reto e conferir os cordões. Enviar `ok` e registrar X0/Y0 e a posição da marca do cordão.
4. Enviar `+65`. Serão executados **somente os primeiros 10 pulsos**, seguindo-se uma pausa para inspeção.
5. Enviar `av` após cada conferência, aguardando o fim do bloco. São **seis comandos av** após o comando inicial: cinco blocos adicionais de 10 e o último de 5. Saldos: +10, +20, +30, +40, +50, +60, +65.
6. Quando aparecer `IDA COMPLETA`, medir o recolhimento do cordão e Xf/Yf. Enviar `1` para retornar pelo saldo emitido, sem offsets. O retorno é contínuo, a 50 pulsos/s. Medir Xr/Yr antes de reposicionar.
7. Repetir três vezes, medindo o início de cada repetição. Para o outro sentido, usar `-65` e os mesmos seis `av`; o saldo final será −65.

Não colar vários comandos de uma vez. Comandos recebidos durante o movimento são descartados, exceto `x`. O sketch não executa automaticamente as três repetições: você precisa medir entre elas.

## Comandos

| Comando | Efeito |
|---|---|
| `ok` | Confirma referência física inicial; aceito quando a referência está pendente. |
| `+65` / `-65` | Inicia uma ida em blocos de até 10 pulsos; exige saldo zero. |
| `av` | Executa o próximo bloco da ida, sem acrescentar uma nova meta de 65. |
| `1` | Cancela blocos pendentes e retorna pelo saldo efetivo, inclusive após uma ida parcial. |
| `x` | Interrompe; completa apenas o pulso já iniciado (até 2 ms) e contabiliza-o. Não corta potência. |
| `zero` | Solicita nova confirmação física; só funciona parado, sem ida pendente e com saldo zero. |
| `?` | Mostra ajuda e saldo. |

O comando `1` deve ser enviado parado, em uma pausa ou depois de `x`. Não reiniciar/desligar a placa para interromper uma medição: o contador é volátil. Se ocorrer reinício ou perda de alimentação, registrar a interrupção e estabelecer novamente a referência física; o programa não pode reconstruir o saldo anterior.

## O que medir e esperar

Somente M1 se move. No modelo nominal, 65 pulsos equivalem a 11,486 mm de cordão e 30,610° de flexão distal, com sinais opostos nos dois sentidos. Essa previsão é distinta dos 28,256° do perfil conjunto +65/+5/+5. Observar fisicamente qual lado é recolhido.

Registrar início, fim, retorno, deslocamento longitudinal do cordão, segmentos que se movem e qualquer interrupção. Não confundir saldo zero com retorno físico exato. Interromper diante de travamento, fim de curso, perda de tensão ou tensionamento excessivo; não forçar o movimento para atingir 65.

## Verificação

Compilação para `arduino:avr:uno` concluída: 4.840 bytes de programa e 260 bytes de variáveis globais. Inspeção do fluxo: somente M1 recebe pulsos; ida limitada a ±65; nenhum offset; retorno desfaz saldo incluindo blocos parciais; troca de referência não apaga saldo pendente. Não houve teste no hardware ou simulação temporal.

```text
arduino-cli compile --fqbn arduino:avr:uno teste_isolado_m1
```
