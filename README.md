# Cinematica do Robo Snake

Este repositorio contem os codigos usados para a modelagem cinematica direta e inversa de um robo do tipo snake composto por tres modulos, com tres juntas equivalentes por modulo.

## Estrutura

- `src/`: scripts Python da modelagem cinematica.
- `notebooks/`: notebooks Jupyter usados no desenvolvimento e validacao.
- `figuras/`: imagens geradas para visualizacao das poses e resultados.
- `docs/`: relatorio em PDF da cinematica direta e inversa.

## Parametros principais

- Numero de modulos: 3
- Juntas por modulo: 3
- Numero total de juntas equivalentes: 9
- Distancia centro-centro entre juntas: 15,17 mm
- Ponto de referencia da ponta: (-62,39; 115,51) mm

## Como executar

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Execute os scripts principais:

```bash
python src/cinematica_direta_basica.py
python src/cinematica_inversa_basica.py
```

Ou abra os notebooks da pasta `notebooks/` no Jupyter, VS Code ou ambiente equivalente.

## Observacao

Os materiais de aula do professor foram usados como referencia metodologica para a formulacao com matrizes homogeneas, mas nao foram incluidos neste repositorio.
