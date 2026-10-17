# Uso de inteligência artificial — implementação preliminar do TCC II

Os programas para Arduino Uno, o script de conferência numérica e o script que gera as seis configurações planares foram elaborados com auxílio de inteligência artificial, por meio do Codex (OpenAI), a partir das informações e decisões de projeto fornecidas pelo autor. A ferramenta auxiliou na escrita e nos comentários do código, na adaptação do modelo para três segmentos, nos testes numéricos, na geração dos desenhos e na redação explicativa correspondente. A versão experimental adicional `arduino/cinematica_xy_movimento/` e seu teste de emulação também foram preparados com essa assistência.

Esta declaração não atribui a IA às publicações científicas citadas nem afirma que todos os arquivos antigos do repositório tiveram a mesma origem. Seu escopo são os arquivos acrescentados em `arduino/` e `src/tcc2/` e os desenhos produzidos localmente pelo gerador. As imagens prontas não são distribuídas no repositório.

## Verificações realizadas

- Compilação dos sketches para Arduino Uno.
- Conferência independente do Jacobiano por diferenças finitas e dos seis alvos no script de referência Python.
- Verificação dos comprimentos dos elos e das coordenadas da ponta no desenho.
- As verificações computacionais não constituem ensaio físico nem execução do binário AVR no robô.

## Limites e responsabilidade

A simulação `arduino/cinematica_xy/` não gera pulsos. A nova versão `arduino/cinematica_xy_movimento/` pode gerar pulsos reais, exclusivamente em sequência M1 (base) → M2 → M3 (distal), mas é distribuída bloqueada até confirmação da calibração, referência manual e armação; seus testes de emulação são registrados separadamente. A distribuição uniforme de flexão, o afastamento do cabo de 18,98 mm, a redução preliminar de 3:1, o raio efetivo do carretel, os sentidos e o retorno dos segmentos ainda exigem conferência ou calibração física. A cinemática não inclui os efeitos da gravidade. A fonte deve suportar um motor em movimento mais os drivers em retenção; a sequência não elimina esse consumo. As flexões intermediárias também dependem do acoplamento dos cabos.

O uso de IA não substitui as fontes técnicas nem a revisão crítica. A conferência final, a operação segura e a interpretação dos resultados permanecem sob responsabilidade do autor. Não se declara que a validação experimental já foi realizada.
# Atualização do controle por tecla mantida

O painel `painel_espaco.py`, o protocolo de permissão renovável no firmware e os
testes `validar_painel.py` foram elaborados com auxílio de IA (Codex/OpenAI).
O objetivo é permitir movimento lento apenas com ESPAÇO mantido, preservando
a sequência M1 → M2 → M3. Testes computacionais não validam a mecânica,
a segurança funcional ou o comportamento real da comunicação e do teclado.

