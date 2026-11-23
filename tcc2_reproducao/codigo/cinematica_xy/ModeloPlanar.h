#pragma once
#include <math.h>
#include <stdint.h>

// Adaptacao do modelo do TCC aos tres segmentos acionados informados.
// HIPOTESE PROVISORIA: as tres juntas de cada segmento dobram igualmente.
// Cada variavel q[m] e a flexao TOTAL do segmento, nao o angulo do motor.
// Unidades: centimetros e radianos. Origem na base; cadeia reta no eixo +Y; X lateral, flexao positiva para +X.
namespace ModeloPlanar {
constexpr uint8_t N = 3;
constexpr uint8_t JUNTAS_POR_SEGMENTO = 3;
constexpr uint8_t JUNTAS = N * JUNTAS_POR_SEGMENTO;
constexpr float ELO_CM = 1.517f;
constexpr float ALCANCE_CM = JUNTAS * ELO_CM;
constexpr float RAD = 0.017453292519943295f;
constexpr float LIMITE_JUNTA_RAD = 15.0f * RAD;
constexpr float LIMITE_RAD = JUNTAS_POR_SEGMENTO * LIMITE_JUNTA_RAD;
constexpr float TOLERANCIA_CM = 0.01f; // tolerancia NUMERICA de 0,1 mm
constexpr float AMORTECIMENTO_CM = 0.05f;
constexpr float PASSO_MAX_RAD = 5.0f * RAD;
constexpr uint16_t MAX_ITER = 300;

struct Ponto { float x, y; };

inline void copiar(const float *origem, float *destino) {
  for (uint8_t i = 0; i < N; ++i) destino[i] = origem[i];
}

inline float limitar(float q) {
  return fmaxf(-LIMITE_RAD, fminf(LIMITE_RAD, q));
}

// Mesma cadeia de nove elos do TCC, agora com q_junta = q_segmento / 3.
// Jacobiano opcional: derivadas de X e Y em relacao aos TRES segmentos.
// Regra da cadeia: J_segmento[m] = soma(J_junta[3m:3m+3]) / 3.
inline Ponto direta(const float *q, float *jx = nullptr, float *jy = nullptr) {
  float seno[JUNTAS], cosseno[JUNTAS], phi = 0.0f;
  Ponto p = {0.0f, 0.0f};
  for (uint8_t i = 0; i < JUNTAS; ++i) {
    phi += q[i / JUNTAS_POR_SEGMENTO] / JUNTAS_POR_SEGMENTO;
    seno[i] = sinf(phi);
    cosseno[i] = cosf(phi);
    p.x += ELO_CM * seno[i];
    p.y += ELO_CM * cosseno[i];
  }
  if (jx && jy) {
    for (uint8_t m = 0; m < N; ++m) { jx[m] = 0.0f; jy[m] = 0.0f; }
    float sx = 0.0f, sy = 0.0f;
    for (int8_t i = JUNTAS - 1; i >= 0; --i) {
      sx += ELO_CM * cosseno[i];
      sy -= ELO_CM * seno[i];
      jx[i / JUNTAS_POR_SEGMENTO] += sx / JUNTAS_POR_SEGMENTO;
      jy[i / JUNTAS_POR_SEGMENTO] += sy / JUNTAS_POR_SEGMENTO;
    }
  }
  return p;
}

inline float erro(Ponto alvo, Ponto atual) {
  const float dx = alvo.x - atual.x, dy = alvo.y - atual.y;
  return sqrtf(dx * dx + dy * dy);
}

// Uma iteracao DLS: dq = J^T (J J^T + lambda^2 I)^-1 (alvo - ponta).
// Inverte apenas uma matriz 2x2; dispensa bibliotecas de matrizes no Uno.
// Faz busca de passo e clipping para nao aceitar aumento do erro nem sair
// do limite de +/-45 graus por segmento (+/-15 por junta). false significa tentativa estagnada,
// nao prova que o alvo e geometricamente impossivel.
inline bool iterar(Ponto alvo, float *q) {
  float jx[N], jy[N], dq[N];
  const Ponto p = direta(q, jx, jy);
  const float ex = alvo.x - p.x, ey = alvo.y - p.y;
  const float anterior = erro(alvo, p);
  float a = AMORTECIMENTO_CM * AMORTECIMENTO_CM;
  float b = 0.0f, d = a;
  for (uint8_t i = 0; i < N; ++i) {
    a += jx[i] * jx[i];
    b += jx[i] * jy[i];
    d += jy[i] * jy[i];
  }
  const float det = a * d - b * b;
  if (!isfinite(det) || det <= 1e-9f) return false;
  const float ux = (d * ex - b * ey) / det;
  const float uy = (a * ey - b * ex) / det;
  float maximo = 0.0f;
  for (uint8_t i = 0; i < N; ++i) {
    dq[i] = jx[i] * ux + jy[i] * uy;
    if (!isfinite(dq[i])) return false;
    maximo = fmaxf(maximo, fabsf(dq[i]));
  }
  if (maximo < 1e-8f) return false;
  float escala = maximo > PASSO_MAX_RAD ? PASSO_MAX_RAD / maximo : 1.0f;
  float candidato[N];
  for (uint8_t tentativa = 0; tentativa < 8; ++tentativa) {
    for (uint8_t i = 0; i < N; ++i) candidato[i] = limitar(q[i] + escala * dq[i]);
    const float novo = erro(alvo, direta(candidato));
    if (isfinite(novo) && novo < anterior) {
      copiar(candidato, q);
      return true;
    }
    escala *= 0.5f;
  }
  return false;
}

// Tentativas alternativas ajudam a sair da configuracao reta/singular.
// Nao garantem encontrar todas as solucoes de um manipulador redundante.
inline void semente(uint8_t tentativa, const float *atual, float *q) {
  for (uint8_t i = 0; i < N; ++i) {
    switch (tentativa) {
      case 0: q[i] = atual[i]; break;
      case 1: q[i] = 5.0f * RAD; break;
      case 2: q[i] = -5.0f * RAD; break;
      case 3: q[i] = (i % 2 ? -8.0f : 8.0f) * RAD; break;
      default: q[i] = (i % 2 ? 8.0f : -8.0f) * RAD; break;
    }
  }
}
} // namespace ModeloPlanar
