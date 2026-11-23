#include <Arduino.h>
#include <string.h>

// Teste isolado M1 - Arduino Uno / DM556 - 2026-11-18.
// Mesma interface STEP ativo em LOW do firmware existente.
// M1: STEP 2, DIR 5. M2/M3 ficam sem pulsos, preservando a sustentacao.
// Sem offsets, encoder, homing ou medicao de comprimento/angulo.
const uint8_t STEP_M1 = 2, DIR_M1 = 5;
const uint8_t STEP_M2 = 6, STEP_M3 = 8;
const uint8_t DIR_M2 = 7, DIR_M3 = 9;
const uint32_t PULSE_US = 2000;
const uint32_t PERIOD_US = 20000; // 50 pulsos/s; DIR estabiliza antes da ida.
const int16_t TEST_PULSES = 65;
const uint8_t BLOCK_PULSES = 10;

bool referenced = false, moving = false, pulseLow = false;
bool sequenceActive = false;
int8_t direction = 1, testDirection = 1;
int16_t balance = 0;           // saldo assinado de pulsos completos
uint8_t remaining = 0;        // pulsos restantes do bloco atual
uint8_t testRemaining = 0;    // pulsos de ida ainda nao concluidos
uint32_t lastStart = 0, pulseStart = 0;
char line[24];
uint8_t lineLength = 0;
bool discardLine = false;

void status() {
  Serial.print(F("Saldo M1: ")); Serial.print(balance);
  Serial.println(F(" pulsos. M2/M3: nenhum pulso comandado."));
  Serial.print(F("Estado: "));
  if (moving) Serial.println(F("EM MOVIMENTO"));
  else if (sequenceActive) {
    Serial.print(F("PAUSA; faltam ")); Serial.print(testRemaining);
    Serial.println(F(" pulsos de ida. Confira e envie av."));
  } else Serial.println(F("PARADO"));
}

void help() {
  Serial.println(F("TESTE ISOLADO M1 - 115200 baud - final de linha Nova linha"));
  Serial.println(F("ok: confirma inicio fisicamente reto e cordoes tensionados"));
  Serial.println(F("+65 ou -65: inicia teste, primeiro bloco de 10 pulsos"));
  Serial.println(F("av: proximo bloco; seis blocos de 10 e um de 5"));
  Serial.println(F("1: retorna pelo saldo emitido, inclusive teste parcial"));
  Serial.println(F("x: interrompe imediatamente; NAO corta potencia"));
  Serial.println(F("zero: pede nova confirmacao, apenas com saldo zero"));
  Serial.println(F("?: ajuda e saldo. Sem offsets ou movimento automatico ao ligar."));
}

void startBlock(int8_t sign, uint8_t count) {
  direction = sign;
  remaining = count;
  digitalWrite(DIR_M1, sign > 0 ? HIGH : LOW);
  lastStart = micros(); // espera 20 ms antes do primeiro pulso
  moving = count > 0;
}

void finishPulse() {
  digitalWrite(STEP_M1, HIGH);
  pulseLow = false;
  balance += direction;
  --remaining;
  if (sequenceActive) --testRemaining;
}

void reportCompletion() {
  moving = false;
  if (sequenceActive && testRemaining == 0) {
    sequenceActive = false;
    Serial.println(F("IDA COMPLETA: 65 pulsos. Meca cordao e ponta; depois envie 1."));
  } else if (!sequenceActive && balance == 0) {
    Serial.println(F("RETORNO CONCLUIDO. Meca retorno fisico antes de reposicionar."));
  }
  status();
}

void updateMotion() {
  if (!moving) return;
  const uint32_t now = micros();
  if (pulseLow) {
    if ((uint32_t)(now - pulseStart) < PULSE_US) return;
    finishPulse();
    if (!remaining) { reportCompletion(); return; }
  }
  if ((uint32_t)(now - lastStart) < PERIOD_US) return;
  digitalWrite(STEP_M1, LOW);
  pulseLow = true;
  pulseStart = micros();
  lastStart = pulseStart;
}

void stopMotion() {
  // Completa o pulso ja iniciado para nao perder sua contabilizacao.
  if (pulseLow) {
    while ((uint32_t)(micros() - pulseStart) < PULSE_US) {}
    finishPulse();
  }
  moving = false;
  sequenceActive = false;
  remaining = testRemaining = 0;
  lineLength = 0;
  discardLine = true; // descarta ate fim de linha; nao executa sufixos
  Serial.println(F("INTERROMPIDO. Registre o saldo parcial. Use 1 para retornar."));
  status();
}

void handleLine(const char* cmd) {
  if (!strcmp(cmd, "?")) { help(); status(); return; }
  if (!referenced) {
    if (!strcmp(cmd, "ok")) {
      referenced = true;
      Serial.println(F("Referencia confirmada. Registre X0/Y0 e a marca do cordao."));
    } else Serial.println(F("Confira fisicamente reto/tensionado e envie ok."));
    return;
  }
  if (!strcmp(cmd, "1")) {
    sequenceActive = false;
    testRemaining = 0;
    if (balance == 0) { Serial.println(F("Saldo ja zerado; confira a posicao fisica.")); return; }
    Serial.println(F("Retorno sem offsets pelo saldo emitido."));
    startBlock(balance > 0 ? -1 : 1, (uint8_t)abs(balance));
    return;
  }
  if (!strcmp(cmd, "zero")) {
    if (balance != 0 || sequenceActive) {
      Serial.println(F("Retorne com 1 antes de redefinir a referencia.")); return;
    }
    referenced = false;
    Serial.println(F("Registre a intervencao; reposicione fisicamente e envie ok."));
    return;
  }
  if (!strcmp(cmd, "av")) {
    if (!sequenceActive) { Serial.println(F("Nenhuma ida pendente.")); return; }
    const uint8_t count = testRemaining < BLOCK_PULSES ? testRemaining : BLOCK_PULSES;
    startBlock(testDirection, count);
    return;
  }
  if (!strcmp(cmd, "+65") || !strcmp(cmd, "-65")) {
    if (balance != 0 || sequenceActive) {
      Serial.println(F("Uma ida por vez. Retorne com 1 e confira o zero.")); return;
    }
    testDirection = cmd[0] == '+' ? 1 : -1;
    sequenceActive = true;
    testRemaining = TEST_PULSES;
    Serial.println(F("Primeiro bloco. Confira movimento e tensao em cada pausa."));
    startBlock(testDirection, BLOCK_PULSES);
    return;
  }
  Serial.println(F("Comando invalido. Use +65, -65, av, 1, zero, ok ou ?."));
}

void readSerial() {
  // Limita o trabalho por ciclo para atender o temporizador de pulsos.
  for (uint8_t count = 0; count < 16 && Serial.available(); ++count) {
    const char c = Serial.read();
    if (c == 'x' || c == 'X') { stopMotion(); continue; }
    if (c == '\r' || c == '\n') {
      if (!discardLine && lineLength && !moving) {
        line[lineLength] = '\0';
        handleLine(line);
      }
      lineLength = 0;
      discardLine = false;
      continue;
    }
    if (moving) { discardLine = true; lineLength = 0; continue; }
    if (discardLine) continue;
    if (lineLength < sizeof(line)-1) line[lineLength++] = c;
    else {
      discardLine = true;
      lineLength = 0;
      Serial.println(F("Linha longa descartada."));
    }
  }
}

void setup() {
  const uint8_t steps[] = {STEP_M1, STEP_M2, STEP_M3};
  const uint8_t dirs[] = {DIR_M1, DIR_M2, DIR_M3};
  for (uint8_t i = 0; i < 3; ++i) {
    digitalWrite(steps[i], HIGH); pinMode(steps[i], OUTPUT);
    digitalWrite(dirs[i], HIGH); pinMode(dirs[i], OUTPUT);
  }
  Serial.begin(115200);
  help();
  Serial.println(F("Confira fisicamente o inicio reto/tensionado e envie ok."));
}

void loop() {
  updateMotion();
  readSerial();
  updateMotion();
}
