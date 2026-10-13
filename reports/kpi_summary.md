# Indicateurs de référence

Chiffres calculés en SQL (DuckDB) : ils servent à valider les mesures DAX du rapport Power BI.
La fréquence et la prime pure sont calculées sur les sinistres valorisés ; la fréquence déclarée est
suivie à part : 99,8 % des sinistres déclarés sans montant viennent d'un lot de contrats anormal.

## Qualité des données : lot de contrats anormal

| Lot de contrats | Contrats | Part du portefeuille | Avec un sinistre déclaré | Fréquence déclarée | Fréquence valorisée | Sinistres sans montant | Part des sinistres sans montant | Véhicules neufs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lot anormal (IDpol < 25 000) | 9 412 | 1,4 % | 99,7 % | 206,22 % | 6,41 % | 9 628 | 99,8 % | 41,2 % |
| Reste du portefeuille | 668 601 | 98,6 % | 3,7 % | 7,39 % | 7,39 % | 23 | 0,2 % | 8,1 % |

## Méthode naïve vs méthode corrigée

Prime pure calculée avec la fréquence déclarée : 227,9 €, contre 167,2 € sur les sinistres valorisés, soit une surestimation de 36,3 %.

| Âge du véhicule | Indice, méthode naïve | Indice, méthode corrigée |
|---|---:|---:|
| 0 | 344 | 106 |
| 1-2 | 95 | 104 |
| 3-5 | 94 | 102 |
| 6-10 | 97 | 108 |
| 11-15 | 81 | 95 |
| 16+ | 62 | 71 |

## Rupture dans les identifiants de contrat

| Identifiants de contrat | Contrats | Avec un sinistre déclaré | Avec un sinistre valorisé |
|---|---:|---:|---:|
| 0 à 4 999 | 2 400 | 100,0 % | 2,2 % |
| 5 000 à 9 999 | 2 148 | 100,0 % | 1,9 % |
| 10 000 à 14 999 | 503 | 100,0 % | 0,4 % |
| 15 000 à 19 999 | 1 765 | 100,0 % | 4,1 % |
| 20 000 à 24 999 | 2 596 | 99,1 % | 4,8 % |
| 25 000 à 29 999 | 2 781 | 4,5 % | 4,5 % |
| 30 000 à 34 999 | 2 708 | 5,1 % | 5,1 % |
| 35 000 à 39 999 | 2 726 | 5,8 % | 5,8 % |
| 40 000 à 44 999 | 2 771 | 6,4 % | 6,4 % |
| 45 000 à 49 999 | 2 753 | 5,3 % | 5,3 % |
| 50 000 et plus | 654 862 | 3,7 % | 3,7 % |

## Portefeuille

| Indicateur | Valeur |
|---|---:|
| Contrats | 678 013 |
| Exposition (années-contrats) | 358 360 |
| Sinistres déclarés | 36 056 |
| dont sans montant | 9 651 (26,8 %) |
| Fréquence déclarée (qualité des données) | 10,06 % |
| Sinistres valorisés (avec montant) | 26 444 |
| **Fréquence** (sinistres valorisés) | 7,38 % |
| Charge sinistres | 59 909 216 € |
| Coût moyen | 2 266 € |
| Coût moyen écrêté (50 000 €) | 1 754 € |
| **Prime pure** | 167,2 € |
| Prime pure écrêtée | 129,5 € |
| Sinistres graves (> 50 000 €) | 88 |
| Part de la charge portée par les sinistres graves | 29,9 % |

## Concentration de la charge

| Plus gros sinistres | Nombre de sinistres | Part de la charge |
|---|---:|---:|
| 0,1 % | 27 | 21,6 % |
| 1,0 % | 265 | 38,0 % |
| 5,0 % | 1 323 | 52,1 % |
| 10,0 % | 2 645 | 59,9 % |
| 20,0 % | 5 289 | 68,8 % |

## Segments (indice 100 = prime pure écrêtée moyenne du portefeuille)

### Âge conducteur

| Segment | Part exposition | Fréq. déclarée | Part sans montant | Fréquence | Coût moyen écrêté | Prime pure écrêtée | Indice |
|---|---:|---:|---:|---:|---:|---:|---:|
| 18-24 | 3,5 % | 18,93 % | 14,9 % | 16,10 % | 2 102 € | 338,5 € | 261 |
| 25-34 | 18,0 % | 9,91 % | 22,2 % | 7,70 % | 1 740 € | 134,0 € | 103 |
| 35-44 | 24,4 % | 9,32 % | 24,0 % | 7,09 % | 1 697 € | 120,3 € | 93 |
| 45-54 | 25,1 % | 10,55 % | 28,6 % | 7,57 % | 1 739 € | 131,7 € | 102 |
| 55-64 | 15,7 % | 9,12 % | 29,7 % | 6,41 % | 1 624 € | 104,2 € | 80 |
| 65-74 | 9,0 % | 9,25 % | 37,2 % | 5,81 % | 1 789 € | 104,0 € | 80 |
| 75+ | 4,4 % | 9,97 % | 37,0 % | 6,29 % | 1 995 € | 125,4 € | 97 |

### Âge véhicule

| Segment | Part exposition | Fréq. déclarée | Part sans montant | Fréquence | Coût moyen écrêté | Prime pure écrêtée | Indice |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4,7 % | 31,17 % | 77,3 % | 7,07 % | 1 948 € | 137,8 € | 106 |
| 1-2 | 17,4 % | 9,13 % | 19,9 % | 7,31 % | 1 845 € | 134,9 € | 104 |
| 3-5 | 20,1 % | 9,36 % | 20,7 % | 7,42 % | 1 780 € | 132,1 € | 102 |
| 6-10 | 27,6 % | 9,94 % | 18,6 % | 8,09 % | 1 721 € | 139,2 € | 108 |
| 11-15 | 21,8 % | 8,48 % | 14,6 % | 7,29 % | 1 685 € | 122,8 € | 95 |
| 16+ | 8,4 % | 6,48 % | 15,1 % | 5,50 % | 1 683 € | 92,5 € | 71 |

### Bonus-malus

| Segment | Part exposition | Fréq. déclarée | Part sans montant | Fréquence | Coût moyen écrêté | Prime pure écrêtée | Indice |
|---|---:|---:|---:|---:|---:|---:|---:|
| 50 (bonus max) | 62,8 % | 8,00 % | 35,9 % | 5,15 % | 1 690 € | 87,0 € | 67 |
| 51-74 | 23,5 % | 11,20 % | 18,5 % | 9,13 % | 1 705 € | 155,6 € | 120 |
| 75-99 | 10,9 % | 14,18 % | 17,4 % | 11,71 % | 1 835 € | 214,9 € | 166 |
| 100 (départ) | 1,7 % | 27,58 % | 23,3 % | 21,15 % | 2 258 € | 477,6 € | 369 |
| 101+ (malus) | 1,0 % | 37,58 % | 6,4 % | 35,17 % | 1 827 € | 642,6 € | 496 |

### Densité

| Segment | Part exposition | Fréq. déclarée | Part sans montant | Fréquence | Coût moyen écrêté | Prime pure écrêtée | Indice |
|---|---:|---:|---:|---:|---:|---:|---:|
| A - Densité très faible | 17,3 % | 8,16 % | 33,5 % | 5,43 % | 1 786 € | 97,0 € | 75 |
| B - Densité faible | 12,0 % | 8,84 % | 30,7 % | 6,12 % | 1 760 € | 107,8 € | 83 |
| C - Densité moyenne | 29,1 % | 9,46 % | 28,2 % | 6,79 % | 1 679 € | 114,1 € | 88 |
| D - Densité élevée | 21,5 % | 10,88 % | 23,5 % | 8,38 % | 1 792 € | 150,2 € | 116 |
| E - Densité très élevée | 17,8 % | 12,23 % | 21,6 % | 9,60 % | 1 822 € | 174,8 € | 135 |
| F - Urbain dense | 2,3 % | 13,92 % | 31,6 % | 9,53 % | 1 434 € | 136,6 € | 106 |

### Région (top 5)

| Segment | Part exposition | Fréq. déclarée | Part sans montant | Fréquence | Coût moyen écrêté | Prime pure écrêtée | Indice |
|---|---:|---:|---:|---:|---:|---:|---:|
| Corse | 0,5 % | 13,99 % | 46,6 % | 7,47 % | 2 376 € | 177,6 € | 137 |
| Provence-Alpes-Côte d'Azur | 10,0 % | 10,93 % | 23,6 % | 8,35 % | 2 064 € | 172,4 € | 133 |
| Rhône-Alpes | 12,7 % | 11,10 % | 15,9 % | 9,34 % | 1 723 € | 160,9 € | 124 |
| Picardie | 1,0 % | 12,29 % | 28,5 % | 8,79 % | 1 702 € | 149,6 € | 116 |
| Nord-Pas-de-Calais | 3,2 % | 10,24 % | 19,7 % | 8,22 % | 1 707 € | 140,3 € | 108 |

## Âge du conducteur × bonus-malus

Indice de risque de chaque cellule (100 = portefeuille) et, entre parenthèses, part de l'exposition de la tranche
d'âge. Tout nouveau conducteur démarre au coefficient 100 : l'âge et le bonus-malus sont liés.

| Âge du conducteur | 50 (bonus max) | 51-74 | 75-99 | 100 (départ) | 101+ (malus) |
|---|---:|---:|---:|---:|---:|
| 18-24 | 94 (4 %) | 61 (8 %) | 162 (62 %) | 606 (17 %) | 576 (9 %) |
| 25-34 | 43 (17 %) | 80 (51 %) | 149 (26 %) | 256 (3 %) | 365 (2 %) |
| 35-44 | 62 (62 %) | 116 (28 %) | 181 (8 %) | 234 (1 %) | 642 (1 %) |
| 45-54 | 79 (80 %) | 178 (15 %) | 193 (4 %) | 314 (1 %) | 380 (0 %) |
| 55-64 | 63 (83 %) | 157 (13 %) | 165 (4 %) | 138 (0 %) | 528 (0 %) |
| 65-74 | 59 (87 %) | 211 (10 %) | 233 (2 %) | 72 (0 %) | 742 (0 %) |
| 75+ | 73 (86 %) | 225 (11 %) | 310 (2 %) | 215 (0 %) | 689 (0 %) |

## Sinistres graves par région (top 5)

| Région | Part exposition | Sinistres graves | Attendus selon l'exposition | Charge brute | Charge écrêtée |
|---|---:|---:|---:|---:|---:|
| Centre | 28,7 % | 33 | 25,2 | 19 074 802 € | 11 326 670 € |
| Provence-Alpes-Côte d'Azur | 10,0 % | 11 | 8,8 | 6 871 025 € | 6 163 682 € |
| Rhône-Alpes | 12,7 % | 10 | 11,1 | 10 278 304 € | 7 292 198 € |
| Bretagne | 7,7 % | 8 | 6,8 | 3 901 051 € | 3 289 718 € |
| Île-de-France | 8,4 % | 7 | 7,4 | 4 563 222 € | 4 222 363 € |
