# Reanálise estatística final

Dados definitivos confirmados pelo autor; mesma origem física de referência declarada. Análise direta sobre 30 leituras por condição, marcador em 445 mm.

## sem offsets
- angle_rotation_deg: 0.754669
- angle_joint_deg: 0.817798
- joint_gain_g: 1.124989
- relative_nominal: 4.477947
- relative_rot_fit: 4.435538
- relative_joint_fit: 2.525467
- LOO_rotation: 4.752419
- LOO_rotation_gain: 3.466235
- absolute_mean: 4.359606
- rmse_absolute: 4.894223
## com offsets
- angle_rotation_deg: -0.895023
- angle_joint_deg: -0.863311
- joint_gain_g: 1.121052
- relative_nominal: 4.302795
- relative_rot_fit: 4.279621
- relative_joint_fit: 1.961516
- LOO_rotation: 4.414749
- LOO_rotation_gain: 2.762875
- absolute_mean: 3.944287
- rmse_absolute: 4.327889

## Bootstrap
- absolute: {'sem_mean': 4.360024929408036, 'com_mean': 3.9446347196004035, 'diff_observed': 0.4153187009883972, 'CI95_difference': [0.26398785593320895, 0.5680903337839263], 'CI95_reduction_pct': [6.211941893291815, 12.665376732368026], 'fraction_non_positive': 0.0}
- relative: {'sem_mean': 4.479722747720265, 'com_mean': 4.302506367990882, 'diff_observed': 0.17515176977933677, 'CI95_difference': [-0.04026396458096837, 0.37625856507519984], 'CI95_reduction_pct': [-0.9248266376877965, 8.108609211556816], 'fraction_non_positive': 0.0517}
- rotation: {'sem_mean': 4.435949839124625, 'com_mean': 4.279129175877707, 'diff_observed': 0.155916882485859, 'CI95_difference': [-0.07396246018420771, 0.36756889195555914], 'CI95_reduction_pct': [-1.7336690970560475, 7.957190545168619], 'fraction_non_positive': 0.0886}

## Limitações
Offsets selecionados em posições também avaliadas; leave-one-out retém os offsets, e assim valida somente rotação/g, não offsets. Amostra de 5 baterias por condição; bootstrap independente de condições, e diferenças sistemáticas não representadas.
