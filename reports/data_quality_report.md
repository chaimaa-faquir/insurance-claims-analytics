# Rapport de qualité des données

- Contrats : 678 013 | Sinistres valorisés (avec montant) : 26 444
- Sinistres déclarés (après plafonnement) : 36 056, dont 9 651 sans montant (26,8 %)
- Part de la charge portée par les sinistres graves : 29,9 %

## Contrôles

| Contrôle | Lignes concernées |
|---|---:|
| Contrats en double (bloquant) | 0 |
| Valeurs manquantes (bloquant) | 0 |
| Exposition > 1 an (plafonnée à 1) | 1 224 |
| Contrats avec plus de 4 sinistres déclarés (plafonnés) | 9 |
| Âge conducteur > 90 ans | 401 |
| Âge véhicule > 20 ans | 8 322 |
| Sinistres sans contrat (exclus) | 195 |
| Contrats avec sinistre déclaré mais sans montant | 9 116 |
| Sinistres déclarés sans montant | 9 651 |
| Contrats avec plus de sinistres valorisés que déclarés (plafond de 4) | 8 |
| Sinistres graves (> 50 000 EUR) | 88 |

## Sinistres déclarés sans montant : analyse de cause racine

**Symptôme.** Plus d'un sinistre déclaré sur quatre n'a pas de montant, et cette part semble dépendre du
segment : 77 % pour les véhicules de moins d'un an, contre 15 à 21 % ailleurs. En fréquence déclarée, les
véhicules neufs apparaissent ainsi plus de trois fois plus risqués que la moyenne.

| Âge du véhicule | Sinistres déclarés | dont sans montant | Part sans montant |
|---|---:|---:|---:|
| 0 | 5 205 | 4 024 | 77,3 % |
| 1-2 | 5 699 | 1 133 | 19,9 % |
| 3-5 | 6 743 | 1 399 | 20,7 % |
| 6-10 | 9 838 | 1 830 | 18,6 % |
| 11-15 | 6 610 | 968 | 14,6 % |
| 16+ | 1 961 | 297 | 15,1 % |

**Cause.** Les sinistres sans montant ne sont pas répartis dans le portefeuille : 99,8 % d'entre eux se trouvent dans un lot de 9 412 contrats d'identifiant inférieur à 25 000 (1,4 % du portefeuille). Dans ce lot, presque chaque contrat déclare un sinistre, ce qui donne une fréquence déclarée
impossible ; hors de ce lot, fréquence déclarée et fréquence valorisée coïncident.

| Lot | Contrats | Contrats avec un sinistre déclaré | Fréquence déclarée | Fréquence valorisée | Sinistres sans montant | Véhicules neufs |
|---|---:|---:|---:|---:|---:|---:|
| Lot anormal (IDpol < 25 000) | 9 412 | 99,7 % | 206,22 % | 6,41 % | 9 628 | 41,2 % |
| Reste du portefeuille | 668 601 | 3,7 % | 7,39 % | 7,39 % | 23 | 8,1 % |

**Explication de l'effet « véhicules neufs ».** Le lot anormal est composé à 41,2 % de véhicules neufs, contre 8,1 % dans le reste du portefeuille : ses sinistres déclarés sans montant gonflent la fréquence déclarée de ce segment.

**Traitement.** Les indicateurs de sinistralité sont calculés sur les sinistres valorisés. Le lot est conservé
(sa fréquence valorisée est proche de la moyenne) et signalé dans la colonne `data_block` ; l'anomalie est à
remonter au propriétaire des données sources.
