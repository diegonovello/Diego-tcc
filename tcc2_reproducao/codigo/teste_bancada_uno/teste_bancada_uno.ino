#include <Arduino.h>

// OBJETIVO DO TESTE
// Conferir USB/Serial -> Uno -> DM556T -> motor, com o eixo livre.
// Este programa gera pulsos; nao mede posicao, nao detecta perda de passos,
// nao executa controle PI e nao possui rampa de aceleracao.
// Comecar com apenas o conjunto A conectado e com os comandos t e T.
//
// Arduino UNO R3 (ATmega328P, logica 5 V).
// DM556T em anodo comum: PUL+/DIR+ em 5 V, negativos nos pinos abaixo.
// Primeiro teste com eixos livres. Apenas um motor move por vez.
// Confirmar a revisao do driver e a selecao de sinais de 5 V antes de ligar.
// ENA nao e controlado pelo programa; seguir o manual da revisao utilizada.
//
// MAPA DOS PINOS
// Indice do vetor:          0 = motor A | 1 = motor B | 2 = motor C
// PUL- (passos):                 D2           D3           D4
// DIR- (sentido):                D5           D6           D7
// Pinos 0 e 1 ficam livres para a comunicacao serial USB do Uno.
const uint8_t STEP_PINS[] = {2, 3, 4};
const uint8_t DIR_PINS[] = {5, 6, 7};

// Cada pulso completo possui duas metades: 5000 us ativo + 5000 us inativo.
// Frequencia nominal = 1000000 / (2 * HALF_PERIOD_US) = 100 pulsos/s.
// Aumentar HALF_PERIOD_US deixa o motor mais lento. O tempo real inclui
// eventuais atrasos do loop; este gerador e suficiente para o teste lento.
const unsigned long HALF_PERIOD_US = 5000UL; // aproximadamente 100 pulsos/s

// Espera entre a mudanca de DIR e a possibilidade do primeiro pulso.
// Nao e uma rampa: serve apenas para estabilizar o sinal de direcao.
const unsigned int DIR_SETTLE_US = 100;

// ESTADO DO MOVIMENTO
// Estes valores descrevem o comando em andamento, sem realimentacao do motor.
// selectedMotor: indice 0/1/2; moving: permite ou nao gerar novos pulsos.
// pulseActive: true durante a metade ativa do pulso (GPIO em LOW).
// remaining: quantidade de pulsos completos ainda a finalizar.
// lastChangeUs: instante da ultima troca de nivel do sinal PUL.
uint8_t selectedMotor = 0;
bool moving = false;
bool pulseActive = false;
uint16_t remaining = 0;
unsigned long lastChangeUs = 0;

void printHelp() {
  // Se a mensagem sair ilegivel, conferir 115200 baud no monitor serial.
  // F("texto") guarda os textos fixos na memoria de programa e economiza
  // a RAM limitada do Uno. Nao imprimir mensagens a cada pulso: isso pode
  // atrasar a geracao dos sinais e mudar o comportamento que se quer medir.
  Serial.println(F("UNO pronto. Teste com eixo livre, um motor por vez."));
  Serial.println(F("a/b/c: selecionar motor A/B/C (inicial: A)"));
  Serial.println(F("t/T: 10 pulsos, sentido 1/2"));
  Serial.println(F("f/r: 100 pulsos, sentido 1/2"));
  Serial.println(F("x: parar pulsos | ?: ajuda"));
  Serial.println(F("x NAO desenergiza o driver nem e parada de emergencia."));
}

void selectMotor(uint8_t motor) {
  // A selecao so muda em repouso, evitando trocar o destino dos pulsos
  // durante um movimento. As chamadas abaixo fornecem apenas indices 0 a 2.
  if (moving) {
    Serial.println(F("Aguarde o movimento terminar ou envie x."));
    return;
  }
  selectedMotor = motor;
  // Converte 0, 1 e 2 nas letras A, B e C para facilitar a conferencia.
  Serial.print(F("Motor selecionado: "));
  Serial.println(char('A' + selectedMotor));
}

void stopMotion() {
  // Cancela o comando e retorna todos os PUL ao nivel de repouso.
  // Em anodo comum, HIGH no GPIO deixa quase zero volts sobre a entrada
  // optica; LOW drena corrente e ativa essa entrada.
  // Pode encerrar um pulso em andamento: o comando x nao preserva uma
  // contagem confiavel de posicao nem garante uma parada mecanica imediata.
  moving = false;
  remaining = 0;
  pulseActive = false;
  for (uint8_t i = 0; i < 3; ++i) digitalWrite(STEP_PINS[i], HIGH);
  Serial.println(F("Pulsos parados. Driver pode continuar energizado."));
}

void startMotion(bool reverse, uint16_t pulses) {
  // reverse seleciona o nivel de DIR; o sentido mecanico real depende
  // das bobinas e da transmissao. pulses e numero de pulsos, nao de graus.
  // O angulo depende do passo do motor, microstepping e reducao mecanica.
  if (moving) {
    // Nao ha fila de movimentos: um comando recebido enquanto ocupado
    // e rejeitado. Aguardar "Movimento concluido" antes de enviar outro.
    Serial.println(F("Ocupado. Aguarde ou envie x."));
    return;
  }
  digitalWrite(STEP_PINS[selectedMotor], HIGH); // entrada optica inativa
  digitalWrite(DIR_PINS[selectedMotor], reverse ? LOW : HIGH);
  delayMicroseconds(DIR_SETTLE_US);
  // Prepara o contador e o estado inicial; o loop alternara o sinal PUL.
  remaining = pulses;
  pulseActive = false;
  lastChangeUs = micros();
  // Mensagem de inicio: permite identificar motor, quantidade e direcao
  // antes de investigar a fiacao. Ela confirma o comando, nao o giro real.
  Serial.print(F("Motor "));
  Serial.print(char('A' + selectedMotor));
  Serial.print(F(" | pulsos: "));
  Serial.print(pulses);
  Serial.print(F(" | sentido: "));
  Serial.println(reverse ? 2 : 1);
  moving = true;
}

void setup() {
  // Executado uma vez a cada energizacao ou reset. Abrir o monitor serial
  // pode reiniciar o Uno, conforme a placa. Nao existe movimento automatico.
  for (uint8_t i = 0; i < 3; ++i) {
    // Habilita pull-up antes de mudar o pino para saida.
    // Isso prepara a saida em HIGH, em vez de iniciar com um LOW ativo.
    // O software nao controla os pinos durante o bootloader/reset; preparar
    // e gravar a placa com a potencia dos drivers desligada no teste inicial.
    digitalWrite(STEP_PINS[i], HIGH);
    digitalWrite(DIR_PINS[i], HIGH);
    pinMode(STEP_PINS[i], OUTPUT);
    pinMode(DIR_PINS[i], OUTPUT);
  }
  Serial.begin(115200);
  printHelp();
}

void loop() {
  // ETAPA 1: recebe comandos sem esperar uma linha completa.
  // t e T sao diferentes. Os terminadores do monitor serial sao ignorados.
  // Enviar um comando por vez: varios comandos na mesma mensagem podem
  // ser processados antes de o primeiro pulso ser gerado.
  while (Serial.available() > 0) {
    const char command = char(Serial.read());
    switch (command) {
      case 'a': selectMotor(0); break; // conjunto A: PUL D2 / DIR D5
      case 'b': selectMotor(1); break;
      case 'c': selectMotor(2); break;
      case 't': startMotion(false, 10); break;
      case 'T': startMotion(true, 10); break;
      case 'f': startMotion(false, 100); break;
      case 'r': startMotion(true, 100); break;
      case 'x': stopMotion(); break;  // parada dos pulsos, sem cortar potencia
      case '?': printHelp(); break;
      case '\r': case '\n': case ' ': break; // ignora CR, LF e espacos
      default: Serial.println(F("Comando desconhecido. Envie ?.")); break;
    }
  }

  // ETAPA 2: gera as transicoes do pulso apenas quando existe um comando.
  // return encerra esta passagem do loop; o Arduino volta a chama-lo,
  // permitindo receber x enquanto o motor esta sendo comandado.
  if (!moving) return;
  const unsigned long now = micros();
  // A subtracao com unsigned long continua valida na virada de micros()
  // para estes intervalos curtos. Evita comparar com um prazo absoluto.
  if (now - lastChangeUs < HALF_PERIOD_US) return;
  lastChangeUs = now;
  // Alterna ativo/inativo a cada meia-periodo, em anodo comum:
  // pulseActive=true -> GPIO LOW  -> corrente na entrada PUL.
  // pulseActive=false -> GPIO HIGH -> entrada PUL em repouso.
  pulseActive = !pulseActive;
  digitalWrite(STEP_PINS[selectedMotor], pulseActive ? LOW : HIGH);
  // Conta somente ao terminar cada pulso, nao a cada troca de nivel.
  // O operador && impede decrementar remaining durante a metade ativa.
  // --remaining decrementa primeiro e depois compara o resultado com zero.
  if (!pulseActive && --remaining == 0) {
    moving = false;
    Serial.println(F("Movimento concluido."));
  }
}

// ROTEIRO RAPIDO DE DEBUG
// 1. Sem resposta ao ?: conferir cabo USB, placa/porta e 115200 baud.
// 2. Mostra "Inicio" mas nao gira: conferir alimentacao e falha do driver,
//    selecao 5 V, ligacao PUL/DIR, habilitacao e pares de bobinas.
// 3. Motor apenas vibra: conferir bobinas e corrente; nao alterar fios ligado.
// 4. Nao inverte: conferir o DIR do motor selecionado e testar t versus T.
// 5. Move menos que o esperado: conferir microstepping e reducao; comandos
//    especificam pulsos, nao voltas. Conferir tambem perdas de passos.
// 6. "Movimento concluido" confirma apenas o fim dos pulsos comandados.
//    O programa nao recebe confirmacao de movimento ou falha do DM556T.
