# Note de synthèse

**À :** Direction technique automobile  
**De :** Chaimaa FAQUIR, Data Analyst  
**Date :** Octobre 2026  
**Objet :** Sinistralité du portefeuille auto RC : fiabilité des données, segments à risque, sinistres graves  

| 7,38 % | 167 € | 29,9 % | 99,8 % |
|---:|---:|---:|---:|
| fréquence (sinistres valorisés) | prime pure par année-contrat | de la charge portée par 88 sinistres graves | des sinistres sans montant dans 1,4 % des contrats |

## Questions posées

- Les données de sinistres sont-elles assez fiables pour piloter le portefeuille ?
- Quel est le coût attendu d'un contrat et quels segments s'écartent de la moyenne ?
- Quel poids représentent les sinistres graves et où se concentrent-ils ?

## Ce qu'il faut retenir

1. **Une anomalie de données faussait la mesure du risque.** 9 412 contrats (1,4 % du portefeuille, identifiants < 25 000) portent 99,8 % des 9 651 sinistres déclarés sans montant. Calculés sur les sinistres déclarés, la fréquence et la prime pure seraient surestimées de 36 % (prime pure de 228 € au lieu de 167 €), et les véhicules neufs paraîtraient 3,4 fois plus risqués que la moyenne (indice 344) alors qu'ils sont dans la moyenne (106).
2. **Le risque se concentre chez les conducteurs débutants et en malus.** Indice de 67 au bonus maximal (63 % de l'exposition), 369 au coefficient de départ (100) et 496 en malus. L'âge et le bonus-malus sont liés : les 18-24 ans ont un indice de 261, mais de 606 quand ils débutent contre 162 une fois entre 75 et 99.
3. **Le coût est très concentré.** 88 sinistres graves (> 50 000 €, 0,3 % des sinistres) représentent 29,9 % de la charge ; le 1 % de sinistres les plus coûteux en représente 38 %.
4. **Deux régions pèsent financièrement au-dessus de la moyenne.** Provence-Alpes-Côte d'Azur (10 % de l'exposition, indice 133) et Rhône-Alpes (13 %, indice 124). La région Centre compte 33 sinistres graves pour 25 attendus, mais son indice écrêté (85) reste inférieur à la moyenne : pas de surrisque structurel.

## Recommandations

1. Bloquer le lot anormal à l'intégration et remonter l'anomalie au propriétaire des données ; ajouter un contrôle automatique « fréquence déclarée vs fréquence valorisée » par lot de chargement.
2. Piloter la sinistralité sur les sinistres valorisés ; suivre la fréquence déclarée comme indicateur de qualité.
3. Mesurer l'effet propre de l'âge et de l'expérience par un modèle multivarié (GLM fréquence et coût) avant toute décision sur les jeunes conducteurs ; l'échelle du bonus-malus étant réglementée, c'est la tarification de base qui peut s'ajuster.
4. Traiter les sinistres graves à part (écrêtement et chargement spécifique) et ne pas réagir à la seule charge brute d'une région.

## Limites

Indices univariés ; pas de données de primes, donc pas de ratio sinistres / primes ; segments de faible exposition peu fiables (Corse : 0,5 %) ; cause exacte de l'anomalie à confirmer avec le propriétaire des données. Données publiques freMTPL2 (licence CC0). Détail et code : github.com/chaimaa-faquir/insurance-claims-analytics.
