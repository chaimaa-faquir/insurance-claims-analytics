# Dictionnaire des indicateurs

Référentiel commun aux requêtes SQL ([`sql/02_kpi_views.sql`](../sql/02_kpi_views.sql)) et aux mesures DAX du
rapport Power BI : chaque indicateur a une seule définition, une seule règle de calcul et une source identifiée.
Les valeurs de référence sont dans [`reports/kpi_summary.md`](../reports/kpi_summary.md).

## Indicateurs

| Indicateur | Définition métier | Règle de calcul | Source | Valeur portefeuille | Point de vigilance |
|---|---|---|---|---:|---|
| Contrats | Nombre de contrats du portefeuille | Nombre de lignes | `fact_policy` | 678 013 | — |
| Exposition | Durée de couverture cumulée, en années-contrats | Somme de `exposure` (plafonnée à 1 an par contrat) | `fact_policy` | 358 360 | Base de toutes les fréquences : un contrat de 3 mois compte pour 0,25 |
| Sinistres déclarés | Sinistres renseignés sur les contrats | Somme de `claim_nb` (plafonné à 4 par contrat) | `fact_policy` | 36 056 | Inclut 9 651 sinistres sans montant, venant presque tous d'un lot anormal |
| Sinistres valorisés | Sinistres dotés d'un montant | Nombre de lignes | `fact_claim` | 26 444 | Base de la fréquence et du coût moyen |
| Sinistres sans montant | Sinistres déclarés absents de la table des sinistres | Somme par contrat de max(déclarés − valorisés, 0) | `fact_policy` | 9 651 | 99,8 % dans le lot de contrats d'identifiant < 25 000 |
| Fréquence | Nombre moyen de sinistres par année-contrat | Sinistres valorisés / exposition | `fact_claim`, `fact_policy` | 7,38 % | Indicateur de pilotage |
| Fréquence déclarée | Même calcul sur les sinistres déclarés | Sinistres déclarés / exposition | `fact_policy` | 10,06 % | Indicateur de qualité des données uniquement (gonflée par le lot anormal) |
| Charge sinistres | Coût total des sinistres | Somme de `claim_amount` | `fact_claim` | 59,9 M€ | Très concentrée : 1 % des sinistres = 38 % de la charge |
| Charge écrêtée | Coût total avec chaque sinistre plafonné | Somme de `claim_amount_capped` (plafond 50 000 €) | `fact_claim` | 46,4 M€ | Sert à comparer les segments, pas à tarifer |
| Coût moyen | Coût moyen d'un sinistre | Charge sinistres / sinistres valorisés | `fact_claim` | 2 266 € | Sensible aux sinistres graves |
| Coût moyen écrêté | Coût moyen d'un sinistre plafonné | Charge écrêtée / sinistres valorisés | `fact_claim` | 1 754 € | — |
| Prime pure | Coût attendu des sinistres par année-contrat | Fréquence × coût moyen = charge / exposition | `fact_claim`, `fact_policy` | 167,2 € | Avec la fréquence déclarée, elle serait surestimée de 36 % (228 €) |
| Prime pure écrêtée | Prime pure sur la charge écrêtée | Fréquence × coût moyen écrêté | `fact_claim`, `fact_policy` | 129,5 € | Base de l'indice de risque |
| Indice de risque | Risque relatif d'un segment | Prime pure écrêtée du segment / prime pure écrêtée de la sélection × 100 | mesure | 100 | 100 = moyenne de la sélection en cours (les filtres actifs sont respectés) ; indice univarié |
| Part exposition | Poids d'un segment dans le portefeuille | Exposition du segment / exposition totale | `fact_policy` | 100 % | Un indice sur une faible exposition est peu fiable (ex. Corse, 0,5 %) |
| Sinistres graves | Sinistres de plus de 50 000 € | Nombre de sinistres où `is_large_claim` | `fact_claim` | 88 | 0,3 % des sinistres |
| Charge sinistres graves | Coût des sinistres graves | Somme de `claim_amount` où `is_large_claim` | `fact_claim` | 17,9 M€ | — |
| Part charge sinistres graves | Poids des sinistres graves dans le coût total | Charge sinistres graves / charge sinistres | `fact_claim` | 29,9 % | — |
| Part sinistres sans montant | Indicateur de qualité des données | Sinistres sans montant / sinistres déclarés | `fact_policy` | 26,8 % | 0,1 % hors du lot anormal |

## Règles de gestion

| Règle | Valeur | Justification |
|---|---|---|
| Plafond d'exposition | 1 an par contrat | Le portefeuille est observé sur une année au plus (1 224 contrats corrigés) ; règle usuelle sur ce jeu (Noll, Salzmann et Wüthrich, 2018) |
| Plafond de sinistres déclarés | 4 par contrat | Valeurs au-delà jugées aberrantes (9 contrats) |
| Seuil de sinistre grave | 50 000 € | Sépare les sinistres exceptionnels (88) du risque courant |
| Lot anormal | Contrats d'identifiant < 25 000 | 9 412 contrats où presque chaque contrat déclare un sinistre sans montant : anomalie de chargement à remonter au propriétaire des données |
| Sinistres sans contrat | Exclus | 195 sinistres dont l'identifiant de contrat est inconnu |
| Tranches bonus-malus | 50 · 51-74 · 75-99 · 100 (départ) · 101+ (malus) | Tout nouveau conducteur démarre au coefficient 100 (clause type de réduction-majoration) : il est isolé des conducteurs en malus |
| Contrôles bloquants | Doublons, valeurs manquantes, volumétrie, valeurs hors tranches | Le pipeline s'arrête plutôt que de produire des indicateurs faux |
