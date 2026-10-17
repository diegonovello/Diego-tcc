# Registro de verificação computacional — 17/10/2026

Versão sequencial: M1 (base/A) → M2 (B) → M3 (distal/C), um motor por vez, inclusive no retorno. Substitui a versão inicial coordenada.

Não houve gravação no Arduino, ligação de drivers ou ensaio físico.

## Compilação Arduino Uno

- Configuração distribuída, quatro confirmações falsas: 14.018 bytes de programa e 462 bytes de variáveis globais.
- Cópia temporária de teste, quatro confirmações verdadeiras somente no emulador: 15.316 bytes de programa e 468 bytes de variáveis globais.
- A cópia temporária não é distribuída nem deve ser gravada sem a calibração da montagem.
- Esses números não medem o uso máximo de pilha nem garantem tempo real.

## Execução dos HEXs em AVR8js 0.21.1

O teste executou o firmware compilado, com temporizador, UART e GPIO simulados de um ATmega328P a 16 MHz:

- A configuração distribuída bloqueou movimento mesmo após confirmação manual da referência e tentativa de armar.
- Ausência de referência, intertrava aberta, alvo fora do alcance, números inválidos e linha longa não produziram pulsos.
- Caso 3: contagem acumulada de GPIO `0;0;84`.
- Caso 4, a partir do anterior: destino acumulado `42;127;190`.
- Caso 6: destino acumulado `127;84;169`.
- Caso 1, após o caso 6: retorno dos comandos acumulados a `0;0;0`.
- Caso 5, a partir do reto, incluindo reversão: destino acumulado `-42;-127;-190`.
- Em todos esses trajetos, o teste confirmou ordem M1 → M2 → M3 (pulando deltas nulos) e ausência de sobreposição dos sinais STEP ativos.
- A transição direta caso 4 → caso 5 foi bloqueada antes de qualquer pulso, pois uma etapa ultrapassaria a flexão intermediária máxima do modelo.
- Nos trajetos completos observados, menor largura ativa de 66,19 µs e menor período de 16.684,44 µs.
- O comando `!` interrompeu o caso 2, encerrou os pulsos, desarmou e invalidou a referência; não houve novos pulsos após a parada.
- A abertura de D8 interrompeu o caso 6 e impediu rearmar com a entrada aberta.

Esses testes não são uma análise exaustiva do firmware. Não simulam a fonte, a corrente de retenção, os drivers, o motor, os cabos, ruído elétrico, atrito, gravidade, perda de passos ou os recursos de segurança física. Também não demonstram que a ponta atinja a posição calculada. A confirmação adicional `FONTE_CONFIRMADA` permanece falsa na distribuição; movimentação sequencial não comprova suficiência da fonte com os demais drivers energizados.

## Referência numérica

`validar_modelo.py` verifica Jacobiano em 30 configurações, seis alvos da cinemática direta e a conversão cumulativa dos cabos. A referência desktop não substitui os testes dos GPIO nem a calibração física.
