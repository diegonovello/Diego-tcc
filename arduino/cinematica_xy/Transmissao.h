#pragma once
#include <math.h>
#include <stdint.h>

// Aproximacao inicial flexao -> cabo -> pulsos. Nao aciona saidas.
namespace Transmissao {
constexpr float PI_F = 3.14159265358979323846f;
// Diametro informado pelo autor: 30 mm = 3 cm; raio geometrico = 1,5 cm.
// Conferir o raio efetivo no centro do cabo, especialmente com varias camadas.
constexpr float DIAMETRO_CARRETEL_CM = 3.0f;
constexpr float RAIO_CARRETEL_CM = DIAMETRO_CARRETEL_CM / 2.0f;
// Referencia preliminar da secao 3.3 do PDF: motor gira 3x para uma volta
// da saida. Confirmar a montagem; nao e uma relacao medida nesta sessao.
constexpr float REDUCAO_MOTOR_SAIDA = 3.0f;
// Meio passo para motor de 1,8 grau. Deve coincidir com as chaves do driver.
constexpr float PULSOS_POR_VOLTA_MOTOR = 400.0f;
constexpr float PULSOS_POR_CM = PULSOS_POR_VOLTA_MOTOR * REDUCAO_MOTOR_SAIDA
                              / (2.0f * PI_F * RAIO_CARRETEL_CM);

// Interpretacao da cota dZ=18,98 mm enviada pelo autor: cabo paralelo a X,
// eixos das articulacoes em Y e flexao fisica no plano XZ do CAD.
// O firmware usa nomes XY para as duas coordenadas desse plano.
// Conferir essa interpretacao e a distancia no centro do cabo na montagem.
constexpr float AFASTAMENTO_CABO_CM = 1.898f;
constexpr uint8_t SEGMENTOS = 3;

// Cada cabo desliza pelos guias e ancora no final de seu segmento.
// Confirmado: cabos 2 e 3 atravessam os segmentos anteriores, pela parede.
// Modelo ideal: raio de offset constante e mesma face/sinal em todo o trajeto.
// Recolhimento POSITIVO significa encurtar o cabo em relacao ao robo reto.
// delta_l[j] = d * soma(beta[k], k=0..j), com beta em radianos.
// Isto e uma aproximacao de arco paralelo; guias discretos e atrito alteram
// os comprimentos reais. Nao confundir beta com angulo de eixo do motor.
inline void recolhimentosCm(const float *flexoesRad, float *cabosCm) {
  float acumulado = 0.0f;
  for (uint8_t j = 0; j < SEGMENTOS; ++j) {
    acumulado += flexoesRad[j];
    cabosCm[j] = AFASTAMENTO_CABO_CM * acumulado;
  }
}

// Coordenadas IDEAIS relativas ao corpo reto, arredondadas de forma absoluta.
// Nao representam encoder nem posicao fisica medida. Os sentidos eletricos,
// offsets de montagem e referencia real ainda precisam ser calibrados.
inline void passosIdeais(const float *flexoesRad, long *passos) {
  float cabosCm[SEGMENTOS];
  recolhimentosCm(flexoesRad, cabosCm);
  for (uint8_t j = 0; j < SEGMENTOS; ++j) {
    passos[j] = lroundf(cabosCm[j] * PULSOS_POR_CM);
  }
}

// Resultado assinado em float; converter para passos absolutos inteiros
// A conversao acima usa arredondamento absoluto; nao acumular incrementos
// arredondados, que introduziriam deriva a cada comando.
inline float pulsosPorDeslocamentoCm(float deslocamento) {
  return deslocamento * PULSOS_POR_CM;
}
}
