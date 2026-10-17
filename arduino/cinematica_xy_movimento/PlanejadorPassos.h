#pragma once
#include <stdint.h>
#include <math.h>

// DDA/Bresenham em tres eixos. Nao acessa GPIO: cada bit de proximo() pede
// exatamente um pulso no motor correspondente. Nenhum motor recebe rajadas.
// Interpola destinos de cabos/motores, NAO uma reta cartesiana da ponta.
namespace Planejador {
struct DDA {
  uint32_t total = 0, feitos = 0, modulo[3] = {}, acumulador[3] = {};
  int8_t sentido[3] = {};
  void iniciar(const int32_t *origem, const int32_t *destino) {
    total = feitos = 0;
    for (uint8_t i = 0; i < 3; ++i) {
      const int32_t delta = destino[i] - origem[i]; // limites conferidos antes
      sentido[i] = delta > 0 ? 1 : (delta < 0 ? -1 : 0);
      modulo[i] = delta < 0 ? uint32_t(-delta) : uint32_t(delta);
      acumulador[i] = 0;
      if (modulo[i] > total) total = modulo[i];
    }
  }
  uint8_t proximo() {
    if (feitos >= total) return 0;
    uint8_t mascara = 0;
    for (uint8_t i = 0; i < 3; ++i) {
      acumulador[i] += modulo[i];
      if (acumulador[i] >= total) {
        acumulador[i] -= total;
        mascara |= uint8_t(1U << i);
      }
    }
    ++feitos;
    return mascara;
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
