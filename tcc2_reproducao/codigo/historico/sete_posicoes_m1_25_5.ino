#include <Arduino.h>
#include <math.h>

// Sete poses: comandos ABSOLUTOS em relacao ao robo reto, cabos tensionados.
// Modelo equivalente: segmentos 165 / 150 / 150 mm; d = 21,5 mm (eixo centralizado, cabo externo de 3 mm).
// Sem encoder ou homing automatico. Validacao fisica ainda necessaria.
const uint8_t STEP_PINS[3] = {2, 6, 8};
const uint8_t DIR_PINS[3] = {5, 7, 9};
// Indices fisicos: M1=0 (ponta), M2=1 (base), M3=2 (meio).
// A compensacao cumulativa e calculada na ordem base, meio, ponta.
const uint8_t MOTOR_POR_CABO[3] = {1, 2, 0};
// HIGH foi mantido como sentido positivo do original.
// Cada carretel recolhe um cabo e libera o antagonista simultaneamente.
const bool RECOLHER_HIGH[3] = {true, true, true};
// CORRECAO POR MOTOR E SENTIDO: esq/direita seleciona o sentido do movimento.
// Valor positivo acrescenta pulsos; negativo REDUZ a quantidade, sem inverter.
// Reducao limitada ao deslocamento nominal completo.
// Na ida: aplicado uma vez no movimento completo, conforme o sentido do motor.
// Retorno (1): desfaz o saldo REAL de pulsos emitidos, sem folga nova.
// Comandos manuais nao recebem este extra.
// Os parametros abaixo definem o total extra do movimento.
const int16_t pulso_folga_motor_esq1 = 25; // M1 ponta: acrescentar 5 pulsos
const int16_t pulso_folga_motor_esq2 = 5; // M2 base: acrescentar 5 pulsos
const int16_t pulso_folga_motor_esq3 = 5; // M3 meio: acrescentar 5 pulsos
const int16_t pulso_folga_motor_direita1 = 5; // M1 ponta: acrescentar 65 pulsos
const int16_t pulso_folga_motor_direita2 = 5; // M2 base: acrescentar 5 pulsos
const int16_t pulso_folga_motor_direita3 = 5; // M3 meio: acrescentar 5 pulsos
const int16_t PULSOS_FOLGA_ESQ[3] = {
  pulso_folga_motor_esq1, pulso_folga_motor_esq2, pulso_folga_motor_esq3
};
const int16_t PULSOS_FOLGA_DIREITA[3] = {
  pulso_folga_motor_direita1, pulso_folga_motor_direita2, pulso_folga_motor_direita3
};

int16_t folgaParaMovimento(uint8_t motor, long delta) {
  if (delta == 0) return 0;
  return delta < 0 ? PULSOS_FOLGA_ESQ[motor] : PULSOS_FOLGA_DIREITA[motor];
}

const float D_MM = 21.5f;
const float K = 400.0f * (4.0f / 3.0f) / (2.0f * PI * 15.0f);
const uint32_t LARGURA_PULSO_US = 2000;
const uint32_t PERIODO_MIN_US = 4000;
const uint32_t PERIODO_INICIAL_US = 20000;
const float BETA[7][3] = {
  {0, 0, 0}, {20, 20, 20}, {-20, -20, -20}, {10, 20, 15},
  {-10, -20, -15}, {45, 45, 45},
  {-45.0f, -45.0f, -45.0f} // posicao 7 nominal: X=-349,18; Y=104,29 mm
};

long pos[3] = {0, 0, 0};  // estado nominal planejado, exclui correcoes empiricas
long emittedPosition[3] = {0, 0, 0}; // todos os pulsos emitidos, com sinal
uint16_t slackRemaining[3] = {0, 0, 0};
long target[3], steps[3], errorDda[3], total = 0, tick = 0;
int8_t direction[3];
uint8_t pulseMask = 0, selectedMotor = 0;
bool referenced = false, moving = false;
bool receivedO = false;
uint8_t extraCommandState = 0;
uint32_t extraCommandSince = 0;
bool diagnosticExtraMove = false;
bool returningToZero = false;
bool reducedMove[3] = {false, false, false};
long returnNominalSteps[3], returnNominalError[3];
int8_t returnNominalDirection[3];
long diagnosticExtra[3] = {0, 0, 0}; // pulsos completos de +10 desde o ultimo ok
uint32_t pulseSince = 0, lastTick = 0, intervalUs = 0;

void askConfirmation() {
  Serial.println(F("O robo esta RETO e com os cabos tensionados?"));
  Serial.println(F("Confira e digite ok para confirmar. Motores aguardando."));
}

void askPosition() {
  Serial.println(F("Digite a posicao (1 a 7): movimento completo em um comando."));
}

void printEstimatedXY() {
  if (!referenced) {
    Serial.println(F("Posicao estimada indisponivel: confirme o zero com ok."));
    return;
  }
  float x = 0.0f, y = 0.0f, phi = 0.0f;
  long previousCableSteps = 0;
  // Inverter a compensacao cumulativa na ordem base/meio/ponta.
  // Usar pulsos nominais: extras de folga nao representam angulos medidos.
  for (uint8_t segment = 0; segment < 3; ++segment) {
    const long cableSteps = pos[MOTOR_POR_CABO[segment]];
    const float beta = (cableSteps - previousCableSteps) / (K * D_MM);
    previousCableSteps = cableSteps;
    const float theta = beta / 3.0f;
    const float length = segment == 0 ? 55.0f : 50.0f;
    for (uint8_t joint = 0; joint < 3; ++joint) {
      phi += theta;
      x += length * sinf(phi);
      y += length * cosf(phi);
    }
  }
  // Evitar -0.00 na impressao.
  if (fabsf(x) < 0.005f) x = 0.0f;
  if (fabsf(y) < 0.005f) y = 0.0f;
  Serial.print(F("Posicao NOMINAL do modelo (nao medida): X=")); Serial.print(x, 2);
  Serial.print(F(" mm; Y=")); Serial.print(y, 2); Serial.println(F(" mm"));
}

void printPosition() {
  Serial.print(F("Pulsos NOMINAIS M1(ponta), M2(base), M3(meio): "));
  for (uint8_t m = 0; m < 3; ++m) {
    Serial.print(pos[m]); Serial.print(m == 2 ? '\n' : ' ');
  }
  Serial.print(F("Pulsos EMITIDOS com correcao M1/M2/M3: "));
  for (uint8_t m = 0; m < 3; ++m) {
    Serial.print(emittedPosition[m]); Serial.print(m == 2 ? '\n' : ' ');
  }
  printEstimatedXY();
}

void printExtra() {
  Serial.print(F("Extras +10 emitidos desde ok, M1/M2/M3: "));
  for (uint8_t m = 0; m < 3; ++m) {
    Serial.print(diagnosticExtra[m]); Serial.print(m == 2 ? '\n' : ' ');
  }
}

void help() {
  Serial.println(F("SETE POSICOES - 115200 baud"));
  Serial.println(F("+10: mais 10 pulsos em CADA motor, sentido da pose 7; sem extra de folga"));
  Serial.println(F("M1/a=2,5 PONTA | M2/b=6,7 BASE | M3/c=8,9 MEIO"));
  Serial.print(F("Correcao para ESQUERDA M1/M2/M3: "));
  for (uint8_t m = 0; m < 3; ++m) {
    Serial.print(PULSOS_FOLGA_ESQ[m]); Serial.print(m == 2 ? '\n' : ' ');
  }
  Serial.print(F("Correcao para DIREITA M1/M2/M3: "));
  for (uint8_t m = 0; m < 3; ++m) {
    Serial.print(PULSOS_FOLGA_DIREITA[m]); Serial.print(m == 2 ? '\n' : ' ');
  }
  Serial.println(F("Ajuste: positivo soma, negativo reduz; uma unica vez na ida."));
  Serial.println(F("Retorno 1 desfaz os pulsos emitidos, sem correcao nova."));
  Serial.println(F("ok: confirmar robo reto ao iniciar | z: solicitar nova confirmacao"));
  Serial.println(F("1..7: movimento completo em um comando; 1 retorna pelo saldo"));
  Serial.println(F("a/b/c: motor | p: +1 | q: -10 (sentido pose 7) | t/T: +/-10 | f/r: +/-100"));
  Serial.println(F("x: parar pulsos (NAO corta potencia) | ?: ajuda"));
  Serial.println(F("400 pulsos/volta, reducao 4/3, raio 15 mm, d=21,5 mm."));
  Serial.println(F("Sinais de direcao mantidos; cada carretel aciona o par de cabos."));
}

void finishPulse() {
  if (!pulseMask) return;
  for (uint8_t m = 0; m < 3; ++m) {
    if (pulseMask & (1 << m)) {
      digitalWrite(STEP_PINS[m], HIGH);
      emittedPosition[m] += direction[m];
      if (diagnosticExtraMove) ++diagnosticExtra[m];
      if (returningToZero || reducedMove[m]) {
        // Interpolar apenas a estimativa nominal; o retorno usa a contagem
        // efetivamente emitida, incluindo folga, jogs e movimentos interrompidos.
        returnNominalError[m] += returnNominalSteps[m];
        while (returnNominalError[m] >= steps[m]) {
          pos[m] += returnNominalDirection[m];
          returnNominalError[m] -= steps[m];
        }
      } else if (slackRemaining[m]) --slackRemaining[m];
      else pos[m] += direction[m];
    }
  }
  pulseMask = 0;
}

void stopNow() {
  // Completar o pulso em andamento, sem iniciar outro.
  if (pulseMask) {
    while ((uint32_t)(micros() - pulseSince) < LARGURA_PULSO_US) {}
    finishPulse();
  }
  moving = false;
  extraCommandState = 0;

  while (Serial.available()) Serial.read();
  Serial.println(F("Parado. Use 1 para retornar pelo saldo emitido."));
  printPosition();
  printExtra();
}

void startMove(const long requested[3], bool applySlack) {
  diagnosticExtraMove = false;
  returningToZero = false;
  total = tick = 0;
  for (uint8_t m = 0; m < 3; ++m) {
    target[m] = requested[m];
    const long delta = target[m] - pos[m];
    direction[m] = delta >= 0 ? 1 : -1;
    const long nominalSteps = labs(delta);
    long correction = applySlack ? (long)folgaParaMovimento(m, delta) : 0;
    if (correction < -nominalSteps) {
      correction = -nominalSteps;
      Serial.print(F("Reducao limitada ao deslocamento para M")); Serial.println(m + 1);
    }
    reducedMove[m] = correction < 0;
    slackRemaining[m] = correction > 0 ? (uint16_t)correction : 0;
    steps[m] = nominalSteps + correction;
    // Com reducao, avancar o estado nominal proporcionalmente aos pulsos
    // realmente emitidos; o estado nominal continua separado das correcoes.
    returnNominalSteps[m] = nominalSteps;
    returnNominalError[m] = 0;
    returnNominalDirection[m] = direction[m];
    if (!steps[m]) pos[m] = target[m];
    errorDda[m] = 0;
    if (steps[m] > total) total = steps[m];
    const bool high = direction[m] > 0 ? RECOLHER_HIGH[m] : !RECOLHER_HIGH[m];
    digitalWrite(DIR_PINS[m], high ? HIGH : LOW);
  }
  // O primeiro pulso ocorre 20 ms depois: supera os 100 us de setup DIR.
  intervalUs = PERIODO_INICIAL_US;
  lastTick = micros();
  moving = total > 0;
}

void startReturnToZero() {

  diagnosticExtraMove = false;
  returningToZero = true;
  total = tick = 0;
  Serial.println(F("Retorno completo pelo saldo emitido, sem correcao nova."));
  for (uint8_t m = 0; m < 3; ++m) {
    const long emittedDelta = -emittedPosition[m];
    const long nominalDelta = -pos[m];
    target[m] = pos[m] + nominalDelta;
    steps[m] = labs(emittedDelta);
    direction[m] = emittedDelta >= 0 ? 1 : -1;
    slackRemaining[m] = 0;
    errorDda[m] = 0;
    returnNominalSteps[m] = labs(nominalDelta);
    returnNominalDirection[m] = nominalDelta >= 0 ? 1 : -1;
    returnNominalError[m] = 0;
    if (!steps[m]) pos[m] = target[m];
    if (steps[m] > total) total = steps[m];
    const bool high = direction[m] > 0 ? RECOLHER_HIGH[m] : !RECOLHER_HIGH[m];
    digitalWrite(DIR_PINS[m], high ? HIGH : LOW);
  }
  intervalUs = PERIODO_INICIAL_US;
  lastTick = micros();
  moving = total > 0;
  if (!moving) {
    printPosition();
    askPosition();
  }
}

void startPose(uint8_t p) {
  if (p == 0) { startReturnToZero(); return; }
  // Cada teste parte do centro reto. A pose 1 retorna em um comando.
  if ((pos[0] || pos[1] || pos[2] || emittedPosition[0] || emittedPosition[1] || emittedPosition[2])) {
    Serial.println(F("Antes de outro teste, retorne ao centro: 1 e aguarde."));
    Serial.println(F("Depois confira reto; se precisar refazer o zero, use z e ok."));
    return;
  }
  long requested[3];
  float accumulated = 0;
  long previous = 0;
  const long maxSegmentSteps = (long)floorf(K * D_MM * PI / 4.0f);
  for (uint8_t cabo = 0; cabo < 3; ++cabo) {
    accumulated += BETA[p][cabo];
    long cableSteps = lroundf(K * D_MM * accumulated * PI / 180.0f);
    // Limites aplicados entre cabos sucessivos (base, meio, ponta),
    // antes de converter para a ordem fisica dos motores.
    cableSteps = constrain(cableSteps, previous - maxSegmentSteps,
                           previous + maxSegmentSteps);
    previous = cableSteps;
    requested[MOTOR_POR_CABO[cabo]] = cableSteps;
  }
  Serial.print(F("Posicao ")); Serial.println(p + 1);
  if (p == 5) Serial.println(F("Posicao 6: X=+349,18; Y=104,29 mm nominal. Espelho da posicao 7."));
  if (p == 6) Serial.println(F("Posicao 7: X=-349,18; Y=104,29 mm nominal. Tres segmentos a -45 graus."));
  Serial.println(F("Movimento completo com correcao aplicada uma unica vez."));
  startMove(requested, true);
  if (!moving) {
    Serial.println(F("Comando concluido sem deslocamento."));
    askPosition();
  }
}

void updateMotion() {
  if (!moving) return;
  uint32_t now = micros();
  if (pulseMask) {
    if ((uint32_t)(now - pulseSince) < LARGURA_PULSO_US) return;
    finishPulse();
    if (tick == total) {
      moving = false;
      Serial.println(F("Movimento concluido."));
      printPosition();
      printExtra();
      askPosition();
      return;
    }
  }
  if ((uint32_t)(now - lastTick) < intervalUs) return;
  for (uint8_t m = 0; m < 3; ++m) {
    errorDda[m] += steps[m];
    if (errorDda[m] >= total) {
      errorDda[m] -= total;
      pulseMask |= 1 << m;
      digitalWrite(STEP_PINS[m], LOW);
    }
  }
  pulseSince = micros();
  lastTick = pulseSince;
  ++tick;
  // Rampa conservadora de periodo, simetrica; movimentos curtos nao atingem
  // a velocidade maxima. Sem compensacao de atraso por rajadas de pulsos.
  long ramp = tick < total - tick ? tick : total - tick;
  if (ramp > 40) ramp = 40;
  intervalUs = PERIODO_INICIAL_US - (uint32_t)ramp * 400;
  if (intervalUs < PERIODO_MIN_US) intervalUs = PERIODO_MIN_US;
}

void command(char c) {
  if (c == 'x' || c == 'X') { stopNow(); return; }
  if (!referenced) {
    // Aceita ok/OK com ou sem terminador de linha. Nenhum comando de
    // movimento e aceito antes da confirmacao manual.
    if (c == 'o' || c == 'O') { receivedO = true; return; }
    if ((c == 'k' || c == 'K') && receivedO) {
      receivedO = false;
      for (uint8_t m = 0; m < 3; ++m) {
        pos[m] = emittedPosition[m] = diagnosticExtra[m] = 0; slackRemaining[m] = 0;
      }

      extraCommandState = 0;
      referenced = true;
      Serial.println(F("Confirmado! Posicao reta registrada como zero."));
      askPosition();
      return;
    }
    receivedO = false;
    if (c != '\r' && c != '\n' && c != ' ' && c != '\t') askConfirmation();
    return;
  }
  if (moving) { extraCommandState = 0; return; } // somente x durante movimento
  // Ler +10 como comando unico: o digito 1 nunca e tratado como pose.
  if (extraCommandState && (uint32_t)(millis() - extraCommandSince) > 5000) {
    extraCommandState = 0;
    Serial.println(F("+10 incompleto expirou. Reenvie o comando inteiro."));
    return;
  }
  if (extraCommandState) {
    if (extraCommandState == 1 && c == '1') {
      extraCommandState = 2; return;
    }
    if (extraCommandState == 2 && c == '0') {
      extraCommandState = 0;

      long requested[3] = {pos[0] - 10, pos[1] - 10, pos[2] - 10};
      Serial.println(F("Diagnostico: 10 pulsos em cada motor, sentido da posicao 7."));
      startMove(requested, false); // exatamente 10; nao aplica folga automatica
      diagnosticExtraMove = true;
      return;
    }
    extraCommandState = 0;
    Serial.println(F("Comando invalido. Envie +10 inteiro, sem espacos."));
    return;
  }
  if (c == '+') {
    extraCommandState = 1; extraCommandSince = millis(); return;
  }
  if (c == '\r' || c == '\n' || c == ' ' || c == '\t') return;
  if (c == '?') { help(); printPosition(); printExtra(); return; }
  if (c >= 'a' && c <= 'c') {
    selectedMotor = c - 'a';
    Serial.print(F("Motor ")); Serial.println(selectedMotor + 1); return;
  }
  if (c == 'z') {
    referenced = false;
    receivedO = false;

    askConfirmation();
    return;
  }
  if (c >= '1' && c <= '7') {
    startPose(c - '1');
    return;
  }
  long jog = 0;
  switch (c) {
    case 'p': jog = 1; break; case 'q': jog = -10; break;
    case 't': jog = 10; break; case 'T': jog = -10; break;
    case 'f': jog = 100; break; case 'r': jog = -100; break;
    default: Serial.println(F("Comando desconhecido. Use ?.")); return;
  }

  long requested[3] = {pos[0], pos[1], pos[2]};
  requested[selectedMotor] += jog;
  startMove(requested, false);
}

void setup() {
  for (uint8_t m = 0; m < 3; ++m) {
    digitalWrite(STEP_PINS[m], HIGH); pinMode(STEP_PINS[m], OUTPUT);
    digitalWrite(DIR_PINS[m], HIGH); pinMode(DIR_PINS[m], OUTPUT);
  }
  Serial.begin(115200);
  help();
  askConfirmation();
}

void loop() {
  updateMotion();
  for (uint8_t n = 0; n < 16 && Serial.available(); ++n) command(Serial.read());
  updateMotion();
}
