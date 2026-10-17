# Uso de inteligência artificial — implementação preliminar do TCC II

Os dois programas para Arduino Uno, o script de conferência numérica e o script que gera as seis configurações planares foram elaborados com auxílio de inteligência artificial, por meio do Codex (OpenAI), a partir das informações e decisões de projeto fornecidas pelo autor. A ferramenta auxiliou na escrita e nos comentários do código, na adaptação do modelo para três segmentos, nos testes numéricos, na geração dos desenhos e na redação explicativa correspondente.

Esta declaração não atribui a IA às publicações científicas citadas nem afirma que todos os arquivos antigos do repositório tiveram a mesma origem. Seu escopo são os arquivos acrescentados em `arduino/` e `src/tcc2/` e as figuras em `figuras/tcc2/`.

## Verificações realizadas

- Compilação dos sketches para Arduino Uno.
- Conferência independente do Jacobiano por diferenças finitas e dos seis alvos no script de referência Python.
- Verificação dos comprimentos dos elos e das coordenadas da ponta no desenho.
- As verificações computacionais não constituem ensaio físico nem execução do binário AVR no robô.

## Limites e responsabilidade

O programa cartesiano não gera pulsos de acionamento. A distribuição uniforme de flexão, o afastamento do cabo de 18,98 mm, a redução preliminar de 3:1, o raio efetivo do carretel, os sentidos e o retorno dos segmentos ainda exigem conferência ou calibração física. A cinemática não inclui os efeitos da gravidade.

O uso de IA não substitui as fontes técnicas nem a revisão crítica. A conferência final, a operação segura e a interpretação dos resultados permanecem sob responsabilidade do autor. Não se declara que a validação experimental já foi realizada.
