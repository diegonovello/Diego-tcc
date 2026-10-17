#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "ModeloPlanar.h"
#include "Transmissao.h"
#include "ConfiguracaoMovimento.h"
#include "PlanejadorPassos.h"

// VERSAO EXPERIMENTAL SEQUENCIAL: somente M1 -> M2 -> M3, nunca simultaneos.
// VERSAO EXPERIMENTAL COM SAIDAS REAIS. Elaborada com auxilio de IA (Codex/OpenAI).
// Preserva o sketch cinematica_xy como simulacao separada.
// X lateral e Y vertical, em cm. Posicao reta: 0;13.653.
// Sequencia: conferir configuracao -> referenciar RETO -> armar -> X;Y -> mover.
// "caso 1" ... "caso 6" preparam os ANGULOS dos desenhos, sem a ambiguidade da IK.
// ! (sem Enter) e x interrompem. A interrupcao perde a referencia e desarma.
// Nao ha sensor, encoder, PI, homing automatico, leitura ALM ou controle ENA.
// Pulsos contados sao comandos eletricos, nao comprovacao de deslocamento.
using namespace ModeloPlanar;

char linha[64];
uint8_t tamanho = 0;
bool excesso = false, referenciado = false, armado = false;
bool calculando = false, previa = false, movendo = false;
uint8_t tentativa = 0;
uint16_t iteracao = 0;
float qAtual[3] = {}, qBusca[3] = {}, qDestino[3] = {};
Ponto alvo = {0, 0};
int32_t posicao[3] = {}, destino[3] = {};
Planejador::Sequencial sequencia;
uint8_t pulsoAtivo = 0;
uint32_t inicioPulso = 0, ultimoTick = 0, intervalo = 0, inicioMovimento = 0;
enum Evento : uint8_t { NENHUM, CONCLUIDO, CANCELADO, INTERTRAVA, TEMPO_ESGOTADO };
Evento evento = NENHUM;

bool intertravaFechada() { return digitalRead(ConfigMov::INTERTRAVA_PIN) == LOW; }

void inativarPulsos() {
  // Nunca truncar um pulso no stop: esperar no maximo mais 40 us antes de HIGH.
  // HIGH e repouso no anodo comum. Nao modifica ENA nem corta potencia.
  if (pulsoAtivo) delayMicroseconds(ConfigMov::PULSO_US);
  for (uint8_t i = 0; i < 3; ++i) digitalWrite(ConfigMov::STEP[i], HIGH);
  pulsoAtivo = 0;
}

void interromper(Evento motivo) {
  inativarPulsos();
  movendo = calculando = previa = armado = referenciado = false;
  tamanho = 0;
  excesso = false;
  evento = motivo;
}

void atualizarEstimativa() {
  // Inverte o mapa triangular de cabos a partir dos pulsos comandados.
  // Evita guardar a pose ideal como se o arredondamento nao existisse.
  float anterior = 0;
  for (uint8_t i = 0; i < 3; ++i) {
    const float soma = (float(posicao[i]) / Transmissao::PULSOS_POR_CM)
                       / Transmissao::AFASTAMENTO_CABO_CM;
    qAtual[i] = soma - anterior;
    anterior = soma;
  }
}

void imprimirPassos(const int32_t *p) {
  for (uint8_t i = 0; i < 3; ++i) { if (i) Serial.print(';'); Serial.print(p[i]); }
  Serial.println();
}

void estado() {
  Serial.print(F("Referenciado/armado: ")); Serial.print(referenciado);
  Serial.print('/'); Serial.println(armado);
  Serial.print(F("Intertrava fechada: ")); Serial.println(intertravaFechada());
  Serial.print(F("Pulsos COMANDADOS relativos ao reto: ")); imprimirPassos(posicao);
  if (referenciado) {
    const Ponto p = direta(qAtual);
    Serial.print(F("Ponta ESTIMADA, nao medida [cm]: "));
    Serial.print(p.x, 5); Serial.print(';'); Serial.println(p.y, 5);
  } else Serial.println(F("Sem referencia fisica confirmada; posicao nao confiavel."));
  Serial.print(F("Previa pronta: ")); Serial.println(previa);
}

void ajuda() {
  Serial.println(F("UNO XY COM MOVIMENTO EXPERIMENTAL - 115200, New Line."));
  Serial.println(F("X;Y em cm -> PREVIA; mover -> M1(base), M2, M3(distal)."));
  Serial.println(F("caso 1..6 -> prepara flexoes dos desenhos, sem IK."));
  Serial.println(F("referenciar RETO: confirma MANUALMENTE robo reto e tensionado."));
  Serial.println(F("armar | desarmar | estado | config | ?"));
  Serial.println(F("! sem Enter ou x: aborta, desarma e exige nova referencia."));
  Serial.println(F("Durante movimento, outros caracteres sao ignorados."));
  Serial.println(F("ENA nao e controlado; parar pulsos NAO corta potencia."));
}

bool numeros(char *s, float &v) {
  char *fim;
  const double n = strtod(s, &fim);
  if (fim == s) return false;
  while (*fim && isspace(static_cast<unsigned char>(*fim))) ++fim;
  if (*fim || !isfinite(n) || fabs(n) > 1000) return false;
  v = float(n);
  return true;
}

bool preparar(const float *q) {
  previa = false;
  for (uint8_t i = 0; i < 3; ++i) {
    if (!isfinite(q[i]) || fabsf(q[i]) > LIMITE_RAD + 0.00001f) {
      Serial.println(F("ERRO: flexao fora de +/-45 graus.")); return false;
    }
  }
  long p[3];
  Transmissao::passosIdeais(q, p);
  for (uint8_t i = 0; i < 3; ++i) {
    if (p[i] < -ConfigMov::LIMITE_ABSOLUTO || p[i] > ConfigMov::LIMITE_ABSOLUTO) {
      Serial.println(F("ERRO: destino excede limite absoluto de pulsos.")); return false;
    }
  }
  copiar(q, qDestino);
  for (uint8_t i = 0; i < 3; ++i) destino[i] = int32_t(p[i]);
  previa = true;
  const Ponto ponto = direta(qDestino);
  Serial.print(F("PREVIA ideal [cm]: ")); Serial.print(ponto.x, 5);
  Serial.print(';'); Serial.println(ponto.y, 5);
  Serial.print(F("Flexoes de segmento [graus]: "));
  for (uint8_t i = 0; i < 3; ++i) { if (i) Serial.print(';'); Serial.print(q[i] / RAD, 3); }
  Serial.println();
  Serial.print(F("Destinos absolutos [pulsos A;B;C]: ")); imprimirPassos(destino);
  Serial.println(F("Revisar previa. Enviar mover somente com bancada conferida."));
  return true;
}

// Mover M1 sem compensar M2/M3 altera temporariamente suas flexoes.
// O mapa ideal e linear em passos: basta conferir os extremos de cada etapa.
// Isso NAO detecta colisao, folga ou falta de tensao na montagem real.
bool validarEtapasSequenciais() {
  int32_t p[3] = {posicao[0], posicao[1], posicao[2]};
  for (uint8_t etapa = 0; etapa < 4; ++etapa) {
    if (etapa) p[etapa-1] = destino[etapa-1];
    float anterior = 0;
    for (uint8_t i = 0; i < 3; ++i) {
      const float soma = (float(p[i]) / Transmissao::PULSOS_POR_CM)
                         / Transmissao::AFASTAMENTO_CABO_CM;
      const float flexao = soma - anterior;
      if (!isfinite(flexao) || fabsf(flexao) > LIMITE_RAD) return false;
      anterior = soma;
    }
  }
  return true;
}

void iniciarMovimento() {
  if (evento != NENHUM) {
    Serial.println(F("Aguarde o relatorio de estado e reenvie mover.")); return;
  }
  if (!previa || !armado || !referenciado || !ConfigMov::confirmada() || !intertravaFechada()) {
    Serial.println(F("BLOQUEADO: previa, referencia, armar e configuracao sao obrigatorios.")); return;
  }
  for (uint8_t i = 0; i < 3; ++i) {
    const int32_t delta = destino[i] - posicao[i];
    if (uint32_t(delta < 0 ? -delta : delta) > ConfigMov::LIMITE_DELTA) {
      previa = false;
      Serial.println(F("ERRO: deslocamento excede limite por comando.")); return;
    }
  }
  if (!validarEtapasSequenciais()) {
    previa = false;
    Serial.println(F("BLOQUEADO: etapa M1/M2/M3 excede flexao intermediaria."));
    Serial.println(F("Necessario planejar alvos intermediarios e conferir cabos.")); return;
  }
  sequencia.iniciar(posicao, destino);
  previa = false;
  if (!sequencia.total) {
    Serial.println(F("Sem pulsos adicionais: destino ja comandado.")); return;
  }
  Serial.println(F("MOVENDO SEQUENCIAL M1 -> M2 -> M3. ! ou x aborta."));
  Serial.flush(); // termina as mensagens ANTES de iniciar o temporizador
  for (uint8_t i = 0; i < 3; ++i) {
    const bool low = sequencia.sentido[i] > 0 ? ConfigMov::DIR_RECOLHER_LOW[i]
                                        : !ConfigMov::DIR_RECOLHER_LOW[i];
    digitalWrite(ConfigMov::DIR[i], low ? LOW : HIGH);
  }
  delayMicroseconds(ConfigMov::DIR_ESPERA_US);
  inicioMovimento = millis();
  ultimoTick = micros();
  intervalo = Planejador::intervaloUs(0, sequencia.total, ConfigMov::VELOCIDADE_INICIAL,
                                    ConfigMov::VELOCIDADE_MAXIMA, ConfigMov::ACELERACAO);
  movendo = true;
}

void atualizarMovimento() {
  if (!movendo) return;
  if (!intertravaFechada()) { interromper(INTERTRAVA); return; }
  if (uint32_t(millis() - inicioMovimento) > ConfigMov::TEMPO_MAXIMO_MS) {
    interromper(TEMPO_ESGOTADO); return;
  }
  uint32_t agora = micros();
  if (pulsoAtivo) {
    if (uint32_t(agora - inicioPulso) < ConfigMov::PULSO_US) return;
    for (uint8_t i = 0; i < 3; ++i)
      if (pulsoAtivo & (1U << i)) digitalWrite(ConfigMov::STEP[i], HIGH);
    pulsoAtivo = 0;
    if (sequencia.feitos == sequencia.total) {
      if (sequencia.avancar()) {
        // A ultima entrada PUL voltou a HIGH antes da troca. Nenhuma sobreposicao.
        ultimoTick = micros();
        intervalo = ConfigMov::PAUSA_ENTRE_MOTORES_US + Planejador::intervaloUs(
          0, sequencia.total, ConfigMov::VELOCIDADE_INICIAL,
          ConfigMov::VELOCIDADE_MAXIMA, ConfigMov::ACELERACAO);
        return;
      }
      movendo = false;
      atualizarEstimativa();
      evento = CONCLUIDO;
    }
    return;
  }
  // Subtracao unsigned permanece valida na virada de micros(). Sem catch-up:
  // se o loop atrasar, nao despejar pulsos acumulados para recuperar o tempo.
  if (uint32_t(agora - ultimoTick) < intervalo) return;
  pulsoAtivo = sequencia.proximo();
  for (uint8_t i = 0; i < 3; ++i) if (pulsoAtivo & (1U << i)) {
    digitalWrite(ConfigMov::STEP[i], LOW);
    posicao[i] += sequencia.sentido[i]; // conta somente pulsos efetivamente iniciados
  }
  inicioPulso = ultimoTick = micros();
  if (sequencia.feitos < sequencia.total)
    intervalo = Planejador::intervaloUs(sequencia.feitos, sequencia.total, ConfigMov::VELOCIDADE_INICIAL,
                                      ConfigMov::VELOCIDADE_MAXIMA, ConfigMov::ACELERACAO);
}

void tratarLinha(char *s) {
  if (!strcmp(s, "x")) { interromper(CANCELADO); return; }
  if (!strcmp(s, "desarmar")) { interromper(CANCELADO); return; }
  if (!strcmp(s, "?")) { ajuda(); return; }
  if (!strcmp(s, "estado")) { estado(); return; }
  if (!strcmp(s, "config")) {
    Serial.print(F("Geometria/sentidos/retorno/fonte confirmados: "));
    Serial.print(ConfigMov::GEOMETRIA_CONFIRMADA); Serial.print('/');
    Serial.print(ConfigMov::SENTIDOS_CONFIRMADOS); Serial.print('/');
    Serial.print(ConfigMov::RETORNO_E_TENSAO_CONFIRMADOS); Serial.print('/');
    Serial.println(ConfigMov::FONTE_CONFIRMADA);
    Serial.print(F("Pulsos/mm de cabo: ")); Serial.println(Transmissao::PULSOS_POR_CM / 10, 5);
    Serial.print(F("Limite absoluto/delta: ")); Serial.print(ConfigMov::LIMITE_ABSOLUTO);
    Serial.print('/'); Serial.println(ConfigMov::LIMITE_DELTA);
    return;
  }
  if (calculando) { Serial.println(F("Busca em andamento. ! cancela.")); return; }
  if (!strcmp(s, "referenciar RETO")) {
    if (!intertravaFechada()) { Serial.println(F("BLOQUEADO: intertrava D8 aberta.")); return; }
    armado = previa = false;
    for (uint8_t i = 0; i < 3; ++i) { qAtual[i] = 0; posicao[i] = 0; }
    referenciado = true;
    Serial.println(F("Referencia MANUAL aceita. Isto NAO movimenta nem mede o robo.")); return;
  }
  if (!strcmp(s, "armar")) {
    if (!referenciado || !intertravaFechada() || !ConfigMov::confirmada()) {
      Serial.println(F("BLOQUEADO: confirmar parametros, referencia e intertrava.")); return;
    }
    armado = true;
    Serial.println(F("ARMADO. Mover pode gerar pulsos reais.")); return;
  }
  if (!strcmp(s, "mover")) { iniciarMovimento(); return; }
  previa = false; // um novo pedido invalida a previa anterior, mesmo se for invalido
  if (!strncmp(s, "caso ", 5) && s[5] >= '1' && s[5] <= '6' && !s[6]) {
    const int8_t casos[6][3] = {{0,0,0},{20,20,20},{0,0,20},{10,20,15},{-10,-20,-15},{30,-10,20}};
    float q[3];
    for (uint8_t i = 0; i < 3; ++i) q[i] = casos[s[5] - '1'][i] * RAD;
    preparar(q); return;
  }
  char *sep = strchr(s, ';');
  if (!sep || strchr(sep + 1, ';')) {
    Serial.println(F("ERRO: X;Y em cm, caso 1..6, ou ?. Zero nao faz homing.")); return;
  }
  *sep = 0;
  if (!numeros(s, alvo.x) || !numeros(sep+1, alvo.y)) {
    Serial.println(F("ERRO: coordenadas invalidas.")); return;
  }
  if (sqrtf(alvo.x*alvo.x + alvo.y*alvo.y) > ALCANCE_CM + 0.00001f) {
    Serial.println(F("ERRO: fora do alcance radial de 13.653 cm.")); return;
  }
  tentativa = 0; iteracao = 0;
  semente(0, qAtual, qBusca);
  calculando = true;
  Serial.println(F("Calculando PREVIA; nenhum movimento durante a busca."));
}

void atualizarCalculo() {
  if (!calculando) return;
  if (erro(alvo, direta(qBusca)) <= TOLERANCIA_CM) {
    calculando = false; preparar(qBusca); return;
  }
  if (++iteracao < MAX_ITER && iterar(alvo, qBusca)) return;
  if (++tentativa < 5) { iteracao = 0; semente(tentativa, qAtual, qBusca); return; }
  calculando = false;
  Serial.println(F("SEM CONVERGENCIA. Nenhum movimento; previa descartada."));
}

void setup() {
  // Gravar HIGH no latch ANTES de tornar a porta saida evita um LOW de partida.
  // Durante reset/boot os pinos ficam em alta impedancia: a eletrica deve impedir
  // pulsos espurios; energizar a potencia somente apos o Uno estar pronto.
  for (uint8_t i = 0; i < 3; ++i) {
    digitalWrite(ConfigMov::STEP[i], HIGH); pinMode(ConfigMov::STEP[i], OUTPUT);
    digitalWrite(ConfigMov::DIR[i], HIGH); pinMode(ConfigMov::DIR[i], OUTPUT);
  }
  pinMode(ConfigMov::INTERTRAVA_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  ajuda();
  Serial.println(F("INICIO DESARMADO E SEM REFERENCIA. Verificar confirmacoes em config."));
}

void loop() {
  atualizarMovimento();
  if ((armado || referenciado) && !intertravaFechada()) interromper(INTERTRAVA);
  // Limita a leitura por passagem para uma rajada serial nao bloquear o scheduler.
  for (uint8_t lidos = 0; lidos < 16 && Serial.available(); ++lidos) {
    const char c = char(Serial.read());
    if (c == '!' || (movendo && c == 'x')) { interromper(CANCELADO); break; }
    if (movendo) continue; // sem prints nem comandos novos durante o trajeto
    if (c == '\r' || c == '\n') {
      if (excesso) { previa = false; Serial.println(F("ERRO: linha longa descartada.")); }
      else if (tamanho) { linha[tamanho] = 0; tratarLinha(linha); }
      tamanho = 0; excesso = false;
    } else if (!excesso) {
      if (tamanho < sizeof(linha)-1) linha[tamanho++] = c;
      else excesso = true;
    }
  }
  atualizarMovimento();
  atualizarCalculo();
  if (evento != NENHUM) {
    if (evento == CONCLUIDO) Serial.println(F("TRAJETO DE PULSOS CONCLUIDO; posicao fisica nao medida."));
    else {
      Serial.print(F("PARADA: "));
      if (evento == INTERTRAVA) Serial.println(F("intertrava aberta."));
      else if (evento == TEMPO_ESGOTADO) Serial.println(F("tempo maximo excedido."));
      else Serial.println(F("cancelamento/desarmar."));
      Serial.println(F("Referencia INVALIDADA. Reposicionar e referenciar RETO antes de rearmar."));
    }
    evento = NENHUM;
    estado();
  }
}
