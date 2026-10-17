# Cinemática XY com movimento — protótipo experimental

Esta é uma **nova versão separada**. `cinematica_xy/` continua sendo a simulação sem saídas e `teste_bancada_uno/` continua sendo o teste individual. O novo sketch calcula a cinemática e pode gerar pulsos reais para três DM556T, com DDA coordenado e rampa discreta. Foi elaborado com auxílio de IA (Codex/OpenAI).

**Não é controle PI, não mede posição, não realiza homing automático e não detecta perda de passos. Não foi validado no robô físico.** Uma trajetória interpolada nos motores não garante uma reta cartesiana nem ausência de colisão. Na montagem vertical, sustentar o mecanismo de forma segura; o modelo não inclui gravidade.

## Arquivos

- `cinematica_xy_movimento.ino`: comandos, busca inversa, estados e geração dos sinais.
- `ConfiguracaoMovimento.h`: pinagem, sentidos, confirmações, velocidade e limites.
- `PlanejadorPassos.h`: distribuição DDA dos passos e perfil de velocidade.
- `ModeloPlanar.h` e `Transmissao.h`: geometria vertical e transmissão cumulativa.
- `validar_modelo.py`: referência numérica desktop.
- `validar_firmware.cjs`: testes do HEX no emulador AVR8js; não conecta ao Arduino.

## Bloqueios de partida

O programa inicia desarmado e sem referência. Em `ConfiguracaoMovimento.h`, as três confirmações são `false`:

1. `GEOMETRIA_CONFIRMADA`: conferir redução real, raio efetivo do carretel, afastamento, microstepping e limites. Os valores 3:1 e 18,98 mm ainda são preliminares.
2. `SENTIDOS_CONFIRMADOS`: testar A/B/C individualmente e ajustar `DIR_RECOLHER_LOW[]` para que positivo realmente recolha cada cabo.
3. `RETORNO_E_TENSAO_CONFIRMADOS`: verificar que liberar cabo permite retorno e mantém tensão. Um cabo não empurra o segmento.

**Somente após as verificações físicas correspondentes** modificar essas confirmações e recompilar. Não mudar os flags apenas para contornar o bloqueio. Com os valores distribuídos, os cálculos e as prévias funcionam, mas `armar` e `mover` não liberam pulsos.

## Ligações de sinal

Mesma referência do teste de bancada: Uno R3, lógica 5 V, ânodo comum, PUL+ e DIR+ em 5 V. Conferir no driver a seleção de entradas para 5 V e a revisão do manual.

| Conjunto | PUL− | DIR− |
| --- | --- | --- |
| A | D2 | D5 |
| B | D3 | D6 |
| C | D4 | D7 |

A alimentação dos motores é feita pelos drivers, nunca pelos pinos do Uno. As ligações de potência, a corrente e as emendas do motor devem ser conferidas no guia de bancada e no datasheet do motor.

### Intertrava lógica adicional

Conectar um **contato normalmente fechado (NC) entre D8 e GND do Uno**. O pino usa `INPUT_PULLUP`: contato fechado permite a verificação; abertura, cabo interrompido ou contato ausente bloqueiam/abortam o movimento. Não ligar D8 à fonte de potência do driver.

Essa entrada apenas solicita parada ao software. **Não é parada de emergência certificada e não substitui um circuito físico independente de interrupção da potência.** O programa não controla ENA, e parar pulsos não desenergiza os motores. A ausência de ENA só é admissível quando compatível com a revisão real do driver. Não mexer nos cabos ou conectores energizados.

## Testar sem acionar motores

1. Manter a potência dos drivers desligada. Abrir o `.ino` na pasta que contém todos os `.h`.
2. Selecionar Arduino Uno; verificar/compilar. Gravação não é realizada automaticamente por estes scripts.
3. Monitor Serial em **115200 baud, New Line**.
4. Enviar `config` e `estado`; observar os bloqueios.
5. Enviar `caso 3`: prévia para flexões `(0;0;20)` graus, ponta aproximadamente `(10,448;135,104)` mm e destinos `0;0;84` pulsos.
6. Enviar `1.04480;13.51037`: alvo cartesiano equivalente, em **centímetros**. A inversa pode encontrar outra configuração e, portanto, outros destinos.
7. `mover` deverá ser rejeitado enquanto faltar confirmação, referência ou armação.

`20;20` continua fora do alcance. O robô reto corresponde a `0;13.653`, não a `0;0`. A origem fica na base, X é lateral e Y é vertical.

## Sequência física, somente após calibração

Primeiro conferir as ligações e os sentidos com o teste individual, sem o robô acoplado. Antes dos ensaios com cabos, confirmar a montagem, sustentar o mecanismo e verificar limites e corte de potência independente. Energizar o Uno e aguardar sua inicialização antes de alimentar os drivers, pois os GPIO ficam em alta impedância durante reset/boot. O circuito deve impedir pulsos espúrios nessa condição.

Com a montagem conferida, o corpo **realmente reto**, os cabos tensionados e a intertrava fechada:

```text
referenciar RETO
armar
caso 3
mover
```

- `referenciar RETO` é uma declaração manual do operador. Não procura sensores nem reposiciona o robô; não usar para esconder uma posição desconhecida.
- `caso 3` prepara exatamente as flexões do desenho. `caso 1` a `caso 6` correspondem aos seis casos documentados.
- Alternativamente, enviar `X;Y` em cm e conferir a prévia; `mover` é sempre uma confirmação separada.
- Começar com flexões pequenas e movimentos limitados; não assumir que um desenho teórico é seguro ou executável na montagem real.
- Aguardar a mensagem de conclusão antes de outro comando. Os destinos são absolutos em relação ao reto; o programa calcula a diferença desde os pulsos já comandados.
- Após conclusão, o estado mostra uma **estimativa** reconstruída dos pulsos, incluindo arredondamento. Não é uma posição medida.

## Parada e recuperação

- `!` interrompe sem Enter. Durante um movimento, `x` também interrompe sem Enter. Fora de movimento, `x` com Enter cancela e desarma.
- `desarmar` invalida a referência. Abertura de D8 e tempo máximo excedido também abortam.
- Após qualquer aborto, não há continuação automática: o programa desarma e exige reposicionamento/conferência manual e nova referência.
- Um pulso já iniciado é encerrado respeitando a largura mínima. Não há rampa no aborto; ele pode provocar perda de passos, oscilação ou movimento residual.
- Durante o movimento, as demais entradas são ignoradas e não entram em fila. `estado`, `config` e mensagens longas só são tratados fora do trajeto, para não atrasar a temporização.
- A perda da conexão USB não é monitorada e não garante parada. Usar a intertrava e o corte físico apropriados. Abrir o Monitor Serial pode reiniciar o Uno e perder a referência.

## Parâmetros iniciais de software

- Saídas PUL− ativas em LOW, repouso HIGH; pulso ativo nominal de pelo menos 40 µs, direção estabilizada por 100 µs.
- Rampa discreta simétrica: velocidade inicial de 8 e máxima de 60 ticks dominantes/s; aceleração de 20 ticks/s². Cada motor recebe no máximo um pulso por tick.
- Limite absoluto de ±600 pulsos por motor e deslocamento máximo de 600 pulsos por motor/comando. São limites preliminares de software, não limites mecânicos calibrados.
- Tempo máximo de 120 s por comando. Não há recuperação de atrasos por rajadas de pulsos.

O manual DM556T V4 especifica largura mínima de 2,5 µs e antecedência de DIR de 5 µs. O software adota margens maiores, mas a temporização e os níveis devem ser conferidos no hardware real. Fonte: [manual do fabricante](https://www.omc-stepperonline.com/download/DM556T_V4.0.pdf).

## Verificação computacional

```bash
arduino-cli compile --fqbn arduino:avr:uno cinematica_xy_movimento
python cinematica_xy_movimento/validar_modelo.py
```

O teste `validar_firmware.cjs` usa `avr8js@0.21.1` para executar dois HEXs: o distribuído com confirmações falsas e uma cópia temporária com confirmações verdadeiras apenas no emulador. Ele verifica bloqueios, entradas inválidas, contagem nos GPIO, direções, término dos pulsos e aborto/intertrava. O teste não deve modificar o arquivo de configuração distribuído e não deve gravar a cópia liberada no hardware.

Para reproduzir, instalar as dependências de teste com `npm install --ignore-scripts` nesta pasta e executar `npm run test:firmware -- caminho/do/bloqueado.hex caminho/do/temporario.hex`. Os resultados observados e as limitações estão em `VERIFICACAO.md`.

Compilar e emular não valida corrente, torque, folgas, retorno, tensão, colisão, segurança funcional nem precisão física. Não se deve apresentar esses testes como validação experimental do robô.
