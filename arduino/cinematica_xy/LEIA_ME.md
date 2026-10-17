# Comandos cartesianos no Arduino Uno — etapa de calculo

Entrada: **X;Y em centimetros**, pelo Monitor Serial a 115200 baud, com New Line. Por exemplo, `20;20` significa X=20 cm e Y=20 cm. Para decimais, usar ponto.

## Modelo implementado

Cada motor controla um segmento de tres juntas, conforme informado pelo autor. O solver possui **tres variaveis**, as flexoes totais dos segmentos, e reconstroi a cadeia de nove elos do TCC.

Hipotese adicional e provisoria: as tres juntas de cada segmento dobram igualmente. Assim, angulo da junta = flexao total do segmento / 3. Os limites de +/-15 graus por junta tornam-se +/-45 graus por segmento. Essa distribuicao deve ser verificada na montagem; o acionamento comum nao garante, sozinho, curvaturas iguais sob atrito e carga.

A cinematica direta soma os nove elos com as rotacoes acumuladas, como no TCC. O Jacobiano dos segmentos e obtido pela regra da cadeia: soma das tres colunas correspondentes do Jacobiano articular, dividida por 3. A inversa utiliza minimos quadrados amortecidos, uma inversao 2x2, busca de passo, limites e cinco sementes. A busca local pode falhar mesmo para alguns alvos atingiveis; o programa informa ausencia de convergencia sem declarar impossibilidade.

Comprimento por elo: 1,517 cm. Comprimento total: 13,653 cm. Origem na base, cadeia reta em +Y (vertical) e X lateral. As coordenadas anteriores foram trocadas: X_novo = Y_anterior e Y_novo = X_anterior; flexao positiva aponta para +X. A orientacao da gravidade nao e modelada pela cinematica.

**O programa calcula no Uno e exibe a configuracao virtual, recolhimentos e passos ideais, mas nao gera pulsos.** As flexoes dos segmentos nao sao os angulos dos motores. A conversao foi adicionada como aproximacao de arco paralelo, ainda sujeita a conferencia da geometria, dos sentidos e da calibracao fisica.

## Testar agora, sem motor ou driver

1. Abrir `cinematica_xy.ino` na pasta que tambem contem `ModeloPlanar.h` e `Transmissao.h`.
2. Selecionar Arduino Uno e a porta USB, verificar e gravar.
3. Manter a potencia dos drivers desligada. Abrir o Monitor Serial em 115200 baud, com New Line.
4. Enviar `estado`: inicialmente a ponta virtual esta em (0; 13,653) cm.
5. Enviar `0;13.653`: deve convergir com os tres segmentos retos.
6. Enviar `7.16835;10.89895`: alvo de teste obtido da direta com flexao total de 20 graus em cada segmento. A inversa pode encontrar outra configuracao com a mesma ponta, pois ha tres variaveis para duas coordenadas.
7. Enviar `20;20`: deve rejeitar a distancia de aproximadamente 28,284 cm, superior ao comprimento de 13,653 cm.
8. Enviar `abc;2`, `1;2;3` e `nan;0`: devem ser rejeitados.

Comandos:
- `?`: ajuda.
- `estado`: ponta e angulos virtuais.
- `config`: diametro do carretel e conversao preliminar de cabo para pulsos.
- `zero`: zera a configuracao matematica; nao faz homing fisico.
- `x` + Enter: cancela a busca e preserva a ultima configuracao virtual aceita.

Falhas de entrada, alcance ou convergencia nao mudam a configuracao virtual aceita. A tolerancia numerica e 0,01 cm (0,1 mm), e o amortecimento e 0,05 cm. Isso nao comprova precisao mecanica. O limite radial e apenas uma verificacao inicial; os limites articulares excluem outros pontos dentro do circulo.

## Dados encontrados no main.pdf e pendencias reais

Fonte: `00_texto_latex/v3/main.pdf`, secoes 3.3, 6.2, 6.4 e 6.6 e Planejamento do TCC II.

| Dado | Situacao |
|---|---|
| Tres segmentos, nove juntas | Definido no texto |
| Elo de 15,17 mm | Definido no texto |
| Limite inicial de +/-15 graus por junta | Definido no texto |
| Um motor por segmento de tres juntas | Confirmado na conversa |
| Mesma flexao nas tres juntas do segmento | Hipotese desta adaptacao; conferir fisicamente |
| Velocidade de saida de 1/3 da entrada | Considerada na secao 3.3; referencia preliminar de reducao 3:1 |
| Diametro do carretel | Autor informou 30 mm; raio geometrico de 15 mm registrado em Transmissao.h |
| Distancia lateral do cabo | 18,98 mm: interpretacao de dZ na imagem enviada, supondo cabo paralelo a X e eixo articular em Y; confirmar fisicamente |
| Ancoragem | Autor confirmou fixacao somente no fim de cada segmento; guias intermediarios permitem deslizamento |
| Trajeto | Autor confirmou que cabos 2 e 3 atravessam os segmentos anteriores pela parede |
| Relacao cabo-curvatura e calibracao | Prevista como continuidade no Planejamento do TCC II |

A relacao de torque Fc = Tm * i * eficiencia / rc apresentada na secao 3.3 nao fornece, sozinha, a conversao de curvatura em deslocamento de cabo.

Com diametro de 30 mm, reducao preliminar 3:1 e 400 pulsos por volta do motor, a conversao nominal e aproximadamente **12,7324 pulsos por mm de cabo** (127,324 por cm). Um pulso corresponde a aproximadamente 0,07854 mm de cabo. Isso nao e o deslocamento da ponta do robo. A funcao em Transmissao.h preserva o sinal do deslocamento e nao aciona saidas.

O diametro deve representar a regiao onde o cabo se enrola. Para calculo mais preciso, usar o raio no centro do cabo, considerando sua espessura e eventuais camadas, e calibrar o recolhimento real.

Para raio constante, depois de obter o deslocamento de cabo pela geometria:
`passos = deslocamento_cm * pulsos_por_volta_motor * reducao / (2*pi*raio_carretel_cm)`.
Definir sinais e offsets, descontar o deslocamento da referencia e arredondar para passos absolutos, evitando acumular erro de arredondamento. A reducao e o numero de voltas do motor por volta da saida. A eficiencia entra no calculo de esforco, nao como multiplicador cinematico arbitrario.

## Compensacao dos cabos que atravessam os segmentos anteriores

Com beta1, beta2 e beta3 como flexoes totais em radianos e d=1,898 cm, usa-se nesta previa a aproximacao de arco paralelo:

- Recolhimento do cabo 1 = d * beta1.
- Recolhimento do cabo 2 = d * (beta1 + beta2).
- Recolhimento do cabo 3 = d * (beta1 + beta2 + beta3).

Por exemplo, curvar somente o primeiro segmento exige compensar os tres cabos nesse modelo. Curvar somente o terceiro exige alterar apenas o terceiro cabo. Portanto, um motor associado a cada segmento nao implica acionamentos desacoplados.

A aproximacao assume afastamento lateral constante, mesmo lado ao longo do trajeto e linha neutra de comprimento constante. Pontos de guia discretos, folgas, atrito e comprimentos de entrada/saida podem exigir um modelo geometrico mais detalhado. O valor 18,98 mm foi interpretado das vistas, nao medido diretamente nesta sessao. O plano fisico XZ foi representado pelos nomes XY do programa.

O programa mostra passos ideais absolutos relativos ao corpo reto e, em cada solucao, o delta relativo ao estado virtual anterior. Positivo significa recolher cabo; negativo significa liberar. A rotacao eletrica correspondente depende da montagem. Liberar cabo sozinho nao empurra o segmento: conferir mecanismo de retorno, antagonismo e manutencao da tensao antes de acionar fisicamente.

Exemplo de verificacao da transmissao (nao e comando de angulos): beta1=beta2=beta3=20 graus produz aproximadamente 84, 169 e 253 passos ideais para os dados atuais. A entrada continua sendo X;Y da ponta em centimetros.

## Proxima etapa de implementacao fisica

1. Confirmar dimensoes reais e origem fisica.
2. Conferir o raio efetivo de recolhimento a partir dos 30 mm, a interpretacao do afastamento de 18,98 mm e a reducao real.
3. Validar e calibrar a aproximacao cumulativa flexao -> cabo -> passos, inclusive os sinais e o retorno dos segmentos ao liberar cabo.
4. Implementar referencia inicial, trajetorias coordenadas, rampas e limites.
5. Testar primeiro com amplitudes pequenas. Uma trajetoria de motores nao garante uma reta cartesiana ou ausencia de colisao.
6. Sem sensor, a posicao comandada continua sendo estimada; PI de posicao exige realimentacao.

O sketch inicial de motor permanece separado em `../teste_bancada_uno/`.

## Verificacao realizada

- Compilacao para `arduino:avr:uno` conferida com Arduino CLI; nao foi gravado automaticamente na placa. A versao anterior ao comando config utilizava 10.140 bytes de programa e 324 bytes de variaveis globais; o tamanho atualizado e informado pela compilacao.
- `validar_modelo.py`: referencia numerica independente em Python/NumPy, com Jacobiano comparado por diferencas finitas em 30 configuracoes e seis alvos conhecidos resolvidos dentro da tolerancia. Tambem confere o alcance radial de 20;20 e casos de acoplamento, sinal e retorno na transmissao cumulativa.
- Esses testes desktop verificam as equacoes e o algoritmo de referencia, nao executam o binario AVR nem validam mecanica. O teste numerico na placa continua necessario.
