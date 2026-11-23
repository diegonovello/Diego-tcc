#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "ModeloPlanar.h"
#include "Transmissao.h"

// PRIMEIRA ETAPA DA VERSAO CARTESIANA: calculo no proprio Uno.
// Nao ha digitalWrite nem geracao de pulsos. Cada motor foi associado pelo
// usuario a um segmento de 3 juntas. Assume-se flexao igual nas 3 juntas.
// Conversao preliminar de arco paralelo: cabos atravessam segmentos anteriores.
// Mostra recolhimentos e passos ideais; faltam calibracao e acionamento fisico.
// Usar com a potencia dos drivers desligada.
// Digitar X;Y em CENTIMETROS e enviar com New Line, por exemplo 0;13.653.
// Ponto decimal: ponto, nunca virgula. A configuracao reta inicial esta em +Y (vertical); X e lateral.
using namespace ModeloPlanar;

char linha[64];
uint8_t tamanho = 0;
bool overflowLinha = false;
float qAtual[N] = {}; // configuracao virtual, nao medida do robo
float qBusca[N];
Ponto alvo = {0.0f, 0.0f};
bool calculando = false;
uint8_t tentativa = 0;
uint16_t iteracao = 0;
float melhorErro = 0.0f;

void mostrarAjuda() {
  Serial.println(F("SIMULACAO CINEMATICA XY - sem acionamento de motores"));
  Serial.println(F("Entrada: X;Y em cm (ponto decimal), com New Line."));
  Serial.println(F("Exemplo reto: 0;13.653 | 20;20 excede o alcance."));
  Serial.println(F("?: ajuda | estado: configuracao virtual | x: cancelar calculo"));
  Serial.println(F("config: geometria e conversao cabo/pulsos preliminar."));
  Serial.println(F("zero: zerar angulos VIRTUAIS; nao faz homing fisico."));
  Serial.println(F("Modelo: 3 segmentos x 3 juntas x 1.517 cm."));
  Serial.println(F("Hipotese: flexao igual nas 3 juntas; +/-45 graus/segmento."));
}

void mostrarTransmissao() {
  Serial.print(F("Diametro do carretel [mm]: "));
  Serial.println(Transmissao::DIAMETRO_CARRETEL_CM * 10.0f, 2);
  Serial.print(F("Reducao motor/saida PRELIMINAR: "));
  Serial.println(Transmissao::REDUCAO_MOTOR_SAIDA, 3);
  Serial.print(F("Pulsos por volta de motor: "));
  Serial.println(Transmissao::PULSOS_POR_VOLTA_MOTOR, 0);
  Serial.print(F("Pulsos por mm de cabo (raio constante): "));
  Serial.println(Transmissao::PULSOS_POR_CM / 10.0f, 5);
  Serial.print(F("Afastamento do cabo INTERPRETADO [mm]: "));
  Serial.println(Transmissao::AFASTAMENTO_CABO_CM * 10.0f, 2);
  Serial.println(F("Rota cumulativa: cabo 1=seg1; cabo 2=seg1+2; cabo 3=seg1+2+3."));
  Serial.println(F("Modelo de arco aproximado. Nenhum pulso e gerado."));
}

void mostrarPreviaPassos(const float *configuracao) {
  float cabos[Transmissao::SEGMENTOS];
  long passos[Transmissao::SEGMENTOS];
  Transmissao::recolhimentosCm(configuracao, cabos);
  Transmissao::passosIdeais(configuracao, passos);
  Serial.print(F("Recolhimento IDEAL dos cabos [mm]: "));
  for (uint8_t j = 0; j < Transmissao::SEGMENTOS; ++j) {
    if (j) Serial.print(';');
    Serial.print(cabos[j] * 10.0f, 3);
  }
  Serial.println();
  Serial.print(F("Passos IDEAIS relativos ao corpo reto: "));
  for (uint8_t j = 0; j < Transmissao::SEGMENTOS; ++j) {
    if (j) Serial.print(';');
    Serial.print(passos[j]);
  }
  Serial.println();
  Serial.println(F("Positivo=recolher; negativo=liberar. Nao e leitura dos motores."));
}

void mostrarEstado() {
  const Ponto p = direta(qAtual);
  Serial.print(F("Ponta VIRTUAL [cm]: "));
  Serial.print(p.x, 4); Serial.print(';'); Serial.println(p.y, 4);
  Serial.print(F("3 flexoes TOTAIS de segmento [graus]: "));
  for (uint8_t i = 0; i < N; ++i) {
    if (i) Serial.print(';');
    Serial.print(qAtual[i] / RAD, 3);
  }
  Serial.println();
  Serial.print(F("9 angulos de junta [graus]: "));
  for (uint8_t i = 0; i < JUNTAS; ++i) {
    if (i) Serial.print(';');
    Serial.print(qAtual[i / JUNTAS_POR_SEGMENTO] / (JUNTAS_POR_SEGMENTO * RAD), 3);
  }
  Serial.println();
  mostrarPreviaPassos(qAtual);
  Serial.println(F("SIMULACAO: geometria, sentidos e retorno a calibrar."));
}

// strtod deve consumir o numero inteiro; rejeita letras e NaN/Inf.
bool lerNumero(char *texto, float &valor) {
  char *fim;
  const double convertido = strtod(texto, &fim);
  if (fim == texto) return false;
  while (*fim && isspace(static_cast<unsigned char>(*fim))) ++fim;
  if (*fim || !isfinite(convertido) || fabs(convertido) > 1000.0) return false;
  valor = static_cast<float>(convertido);
  return true;
}

void tratarLinha(char *texto) {
  if (!strcmp(texto, "x")) {
    calculando = false;
    Serial.println(F("Calculo cancelado; estado virtual anterior preservado."));
    return;
  }
  if (!strcmp(texto, "?")) { mostrarAjuda(); return; }
  if (!strcmp(texto, "estado")) { mostrarEstado(); return; }
  if (!strcmp(texto, "config")) { mostrarTransmissao(); return; }
  if (calculando) {
    Serial.println(F("Calculo em andamento. Aguarde ou envie x com Enter."));
    return;
  }
  if (!strcmp(texto, "zero")) {
    for (uint8_t i = 0; i < N; ++i) qAtual[i] = 0.0f;
    mostrarEstado();
    return;
  }
  char *separador = strchr(texto, ';');
  if (!separador || strchr(separador + 1, ';')) {
    Serial.println(F("ERRO: use exatamente X;Y em cm, por exemplo 0;13.653."));
    return;
  }
  *separador = '\0';
  Ponto pedido;
  if (!lerNumero(texto, pedido.x) || !lerNumero(separador + 1, pedido.y)) {
    Serial.println(F("ERRO: coordenadas invalidas; use numeros finitos e ponto decimal."));
    return;
  }
  const float distancia = sqrtf(pedido.x * pedido.x + pedido.y * pedido.y);
  if (distancia > ALCANCE_CM + 0.00001f) {
    Serial.print(F("FORA DO ALCANCE: distancia ")); Serial.print(distancia, 3);
    Serial.print(F(" cm > comprimento total ")); Serial.println(ALCANCE_CM, 3);
    return;
  }
  alvo = pedido;
  tentativa = 0;
  iteracao = 0;
  melhorErro = erro(alvo, direta(qAtual));
  semente(tentativa, qAtual, qBusca);
  calculando = true;
  Serial.print(F("Calculando alvo [cm]: "));
  Serial.print(alvo.x, 4); Serial.print(';'); Serial.println(alvo.y, 4);
}

// Uma iteracao por passagem: o monitor serial segue atendido durante a busca.
void atualizarCalculo() {
  if (!calculando) return;
  const float e = erro(alvo, direta(qBusca));
  melhorErro = fminf(melhorErro, e);
  if (e <= TOLERANCIA_CM) {
    // Diferenca entre destinos absolutos arredondados evita deriva numerica.
    // A referencia anterior aqui e VIRTUAL, nao uma medicao fisica.
    long anteriores[Transmissao::SEGMENTOS], proximos[Transmissao::SEGMENTOS];
    Transmissao::passosIdeais(qAtual, anteriores);
    Transmissao::passosIdeais(qBusca, proximos);
    copiar(qBusca, qAtual);
    calculando = false;
    Serial.print(F("SOLUCAO NUMERICA | erro [cm]: ")); Serial.println(e, 5);
    mostrarEstado();
    Serial.print(F("Delta de passos desde o estado VIRTUAL anterior: "));
    for (uint8_t j = 0; j < Transmissao::SEGMENTOS; ++j) {
      if (j) Serial.print(';');
      Serial.print(proximos[j] - anteriores[j]);
    }
    Serial.println();
    return;
  }
  ++iteracao;
  if (iteracao < MAX_ITER && iterar(alvo, qBusca)) return;
  if (++tentativa < 5) {
    iteracao = 0;
    semente(tentativa, qAtual, qBusca);
    return;
  }
  calculando = false;
  Serial.print(F("SEM CONVERGENCIA: melhor erro [cm]: ")); Serial.println(melhorErro, 5);
  Serial.println(F("Pode ser limite geometrico ou busca numerica. Estado preservado."));
}

void setup() {
  Serial.begin(115200);
  mostrarAjuda();
  mostrarEstado();
}

void loop() {
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r' || c == '\n') {
      if (overflowLinha) {
        Serial.println(F("ERRO: linha longa; comando descartado."));
      } else if (tamanho) {
        linha[tamanho] = '\0';
        tratarLinha(linha);
      }
      tamanho = 0;
      overflowLinha = false;
    } else if (!overflowLinha) {
      if (tamanho < sizeof(linha) - 1) linha[tamanho++] = c;
      else overflowLinha = true;
    }
  }
  atualizarCalculo();
}
