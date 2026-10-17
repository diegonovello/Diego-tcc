#pragma once
#include <stdint.h>

// Codigo elaborado com auxilio de IA (Codex/OpenAI). Revisar antes de energizar.
// Nao trocar estes flags so para remover o bloqueio: confirmar cada item na bancada.
namespace ConfigMov {
constexpr bool GEOMETRIA_CONFIRMADA = false; // raio efetivo, reducao, offset e microstep
constexpr bool SENTIDOS_CONFIRMADOS = false; // confirmar A, B e C no teste individual
constexpr bool RETORNO_E_TENSAO_CONFIRMADOS = false; // liberar cabo NAO empurra o segmento
constexpr bool FONTE_CONFIRMADA = false; // um motor em movimento + consumo dos drivers parados
constexpr uint8_t STEP[3] = {2, 3, 4}; // PUL-; PUL+ em 5 V (anodo comum)
constexpr uint8_t DIR[3] = {5, 6, 7}; // DIR-; DIR+ em 5 V
// true: LOW em DIR- significa recolher; false inverte SOMENTE o sentido eletrico.
// Os tres valores abaixo sao hipoteses de partida, nao calibracao realizada.
constexpr bool DIR_RECOLHER_LOW[3] = {true, true, true};
constexpr uint8_t INTERTRAVA_PIN = 8;
// Contato normalmente fechado entre D8 e GND: fechado=LOW; aberto=HIGH bloqueia.
// Esta intertrava de software NAO e parada de emergencia certificada.
constexpr uint32_t PULSO_US = 40; // LOW ativo >=40 us; nunca encurtar no aborto
constexpr uint32_t DIR_ESPERA_US = 100;
constexpr uint32_t PAUSA_ENTRE_MOTORES_US = 1000000UL; // sem pulsos entre etapas; mantem torque
constexpr float VELOCIDADE_INICIAL = 2.0f; // pulsos/s; reinicia lentamente apos pausa
constexpr float VELOCIDADE_MAXIMA = 15.0f; // somente um motor por vez
constexpr float ACELERACAO = 4.0f; // pulsos/s^2; rampa independente por motor
constexpr uint32_t PERMISSAO_MS = 150; // heartbeat do PC a cada 50 ms; expirar = pausar
constexpr int32_t LIMITE_ABSOLUTO = 600; // por motor, relativo ao corpo reto
constexpr uint32_t LIMITE_DELTA = 600; // por motor e por comando
constexpr uint32_t TEMPO_MAXIMO_MS = 300000; // tempo ATIVO acumulado; pausa nao conta
inline bool confirmada() {
  return GEOMETRIA_CONFIRMADA && SENTIDOS_CONFIRMADOS && RETORNO_E_TENSAO_CONFIRMADOS && FONTE_CONFIRMADA;
}
}
