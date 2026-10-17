#pragma once
#include <stdint.h>
#include <math.h>

// Exclusao mutua: completa M1(base/A), depois M2(B), depois M3(distal/C).
// Pula somente motores cujo delta e zero. proximo() retorna no maximo UM bit.
// Nao existe modo simultaneo. O chamador encerra o ultimo pulso antes de avancar.
namespace Planejador {
struct Sequencial {
  uint32_t total = 0, feitos = 0, modulo[3] = {};
  int8_t sentido[3] = {};
  uint8_t motor = 0;
  bool selecionar() {
    while (motor < 3 && modulo[motor] == 0) ++motor;
    feitos = 0;
    total = motor < 3 ? modulo[motor] : 0;
    return motor < 3;
  }
  void iniciar(const int32_t *origem, const int32_t *destino) {
    total = feitos = 0;
    for (uint8_t i = 0; i < 3; ++i) {
      const int32_t delta = destino[i] - origem[i]; // limites conferidos antes
      sentido[i] = delta > 0 ? 1 : (delta < 0 ? -1 : 0);
      modulo[i] = delta < 0 ? uint32_t(-delta) : uint32_t(delta);
    }
    motor = 0;
    selecionar();
  }
  bool avancar() {
    ++motor;
    return selecionar();
  }
  uint8_t proximo() {
    if (feitos >= total) return 0;
    ++feitos;
    return uint8_t(1U << motor);
  }
};

// Velocidade em funcao da distancia discreta ate as extremidades.
// Perfil triangular em trajetos curtos; patamar limitado em trajetos longos.
inline uint32_t intervaloUs(uint32_t indice, uint32_t total,
                           float inicial, float maxima, float aceleracao) {
  if (!total) return 0;
  const uint32_t faltam = total - 1 - indice;
  const uint32_t distancia = indice < faltam ? indice : faltam;
  float velocidade = sqrtf(inicial * inicial + 2.0f * aceleracao * distancia);
  if (velocidade > maxima) velocidade = maxima;
  return uint32_t(ceilf(1000000.0f / velocidade));
}
}
