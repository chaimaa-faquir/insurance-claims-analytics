-- Etape 3b - Indicateurs de sinistralite (servent a valider les mesures DAX de Power BI)
--   Frequence            = sinistres valorises (avec montant) / exposition (annees-contrats)
--   Frequence declaree   = sinistres declares / exposition : suivie comme indicateur de qualite,
--                          car la part des sinistres declares sans montant varie selon les segments
--   Cout moyen           = charge des sinistres / nombre de sinistres valorises
--   Prime pure           = frequence x cout moyen = charge / exposition (cout attendu par annee-contrat)
--   Indice               = prime pure ecretee du segment / prime pure ecretee du portefeuille (100 = moyenne)

CREATE OR REPLACE VIEW v_kpi_global AS
WITH p AS (
    SELECT COUNT(*) AS policies, SUM(exposure) AS exposure, SUM(claim_nb) AS claims_declared,
           SUM(claims_without_amount) AS claims_without_amount
    FROM fact_policy
), c AS (
    SELECT COUNT(*) AS claims_with_amount,
           SUM(claim_amount) AS claims_cost,
           SUM(claim_amount_capped) AS claims_cost_capped,
           COUNT(*) FILTER (WHERE is_large_claim) AS large_claims,
           SUM(claim_amount) FILTER (WHERE is_large_claim) AS large_claims_cost
    FROM fact_claim
)
SELECT
    p.policies,
    p.exposure                                         AS exposure_years,
    p.claims_declared,
    p.claims_without_amount,
    p.claims_without_amount / p.claims_declared        AS missing_amount_share,
    p.claims_declared / p.exposure                     AS frequency_declared,
    c.claims_with_amount,
    c.claims_with_amount / p.exposure                  AS frequency,
    c.claims_cost,
    c.claims_cost / c.claims_with_amount               AS avg_cost,
    c.claims_cost_capped / c.claims_with_amount        AS avg_cost_capped,
    c.claims_cost / p.exposure                         AS pure_premium,
    c.claims_cost_capped / p.exposure                  AS pure_premium_capped,
    c.large_claims,
    c.large_claims_cost / c.claims_cost                AS large_claims_cost_share
FROM p, c;

-- Un meme calcul decline par axe d'analyse (format long, pratique pour comparer les segments).
-- Les cles de segment sont portees par fact_policy : on agrege les sinistres par contrat puis par segment.
CREATE OR REPLACE VIEW v_kpi_by_segment AS
WITH claims_per_policy AS (
    SELECT policy_id, COUNT(*) AS n_amount, SUM(claim_amount_capped) AS cost_capped
    FROM fact_claim GROUP BY policy_id
), base AS (
    SELECT p.*, r.region_name, a.area_label,
           COALESCE(c.n_amount, 0) AS n_amount, COALESCE(c.cost_capped, 0) AS cost_capped
    FROM fact_policy p
    JOIN dim_region r USING (region_code)
    JOIN dim_area a USING (area_code)
    LEFT JOIN claims_per_policy c USING (policy_id)
), long AS (
    SELECT 'Région' AS axis, region_name AS segment, exposure, claim_nb, claims_without_amount, n_amount, cost_capped FROM base
    UNION ALL SELECT 'Âge conducteur', driver_age_band, exposure, claim_nb, claims_without_amount, n_amount, cost_capped FROM base
    UNION ALL SELECT 'Bonus-malus', bonus_malus_band, exposure, claim_nb, claims_without_amount, n_amount, cost_capped FROM base
    UNION ALL SELECT 'Âge véhicule', vehicle_age_band, exposure, claim_nb, claims_without_amount, n_amount, cost_capped FROM base
    UNION ALL SELECT 'Densité', area_label, exposure, claim_nb, claims_without_amount, n_amount, cost_capped FROM base
), agg AS (
    SELECT axis, segment, SUM(exposure) AS exposure, SUM(claim_nb) AS claims_declared,
           SUM(claims_without_amount) AS claims_without_amount, SUM(n_amount) AS n_amount,
           SUM(cost_capped) AS cost_capped
    FROM long GROUP BY ALL
), portfolio AS (
    SELECT pure_premium_capped AS pp FROM v_kpi_global
)
SELECT
    axis,
    segment,
    exposure                                                    AS exposure_years,
    exposure / SUM(exposure) OVER (PARTITION BY axis)           AS exposure_share,
    claims_declared / exposure                                  AS frequency_declared,
    claims_without_amount / claims_declared                     AS missing_amount_share,
    n_amount / exposure                                         AS frequency,
    cost_capped / n_amount                                      AS avg_cost_capped,
    cost_capped / exposure                                      AS pure_premium_capped,
    CAST(ROUND(100 * cost_capped / exposure / portfolio.pp, 0) AS INTEGER) AS index_vs_portfolio,
    RANK() OVER (PARTITION BY axis ORDER BY cost_capped / exposure DESC) AS risk_rank
FROM agg, portfolio;

-- Concentration de la charge : quelle part du cout total portent les plus gros sinistres ?
CREATE OR REPLACE VIEW v_claims_concentration AS
WITH ranked AS (
    SELECT claim_amount,
           ROW_NUMBER() OVER (ORDER BY claim_amount DESC)                 AS rnk,
           COUNT(*) OVER ()                                               AS n,
           SUM(claim_amount) OVER (ORDER BY claim_amount DESC
                                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_cost,
           SUM(claim_amount) OVER ()                                      AS total_cost
    FROM fact_claim
)
SELECT
    top_pct,
    MAX(rnk)                          AS claims_in_top,
    MAX(cum_cost) / MAX(total_cost)   AS cost_share
FROM ranked
JOIN (VALUES (0.001), (0.01), (0.05), (0.10), (0.20)) AS t(top_pct) ON rnk <= CEIL(top_pct * n)
GROUP BY top_pct
ORDER BY top_pct;

-- Sinistres graves par region, rapportes a ce que l'exposition laisserait attendre
CREATE OR REPLACE VIEW v_large_claims_by_region AS
WITH expo AS (
    SELECT r.region_name, SUM(p.exposure) AS exposure
    FROM fact_policy p JOIN dim_region r USING (region_code) GROUP BY ALL
), claims_by_region AS (
    SELECT r.region_name, SUM(c.claim_amount) AS cost, SUM(c.claim_amount_capped) AS cost_capped
    FROM fact_claim c JOIN dim_region r USING (region_code) GROUP BY ALL
), large_only AS (
    SELECT r.region_name, COUNT(*) AS n_large
    FROM fact_claim c JOIN dim_region r USING (region_code) WHERE c.is_large_claim GROUP BY ALL
)
SELECT
    e.region_name,
    e.exposure / SUM(e.exposure) OVER ()                               AS exposure_share,
    COALESCE(lo.n_large, 0)                                            AS large_claims,
    SUM(COALESCE(lo.n_large, 0)) OVER () * e.exposure / SUM(e.exposure) OVER () AS large_claims_expected,
    l.cost                                                             AS claims_cost,
    l.cost_capped                                                      AS claims_cost_capped
FROM expo e
LEFT JOIN claims_by_region l USING (region_name)
LEFT JOIN large_only lo USING (region_name)
ORDER BY large_claims DESC;

-- Analyse de cause racine : frequence declaree vs valorisee par lot de contrats
CREATE OR REPLACE VIEW v_data_quality_by_block AS
SELECT
    data_block,
    COUNT(*)                                            AS policies,
    COUNT(*) / SUM(COUNT(*)) OVER ()                    AS policies_share,
    AVG((claim_nb > 0)::INTEGER)                        AS share_with_declared_claim,
    SUM(claim_nb) / SUM(exposure)                       AS frequency_declared,
    SUM(claims_with_amount) / SUM(exposure)             AS frequency,
    SUM(claims_without_amount)                          AS claims_without_amount,
    SUM(claims_without_amount) / SUM(SUM(claims_without_amount)) OVER () AS share_of_missing,
    AVG((vehicle_age = 0)::INTEGER)                     AS share_new_vehicles
FROM fact_policy
GROUP BY data_block
ORDER BY data_block;

-- Methode naive (frequence declaree x cout moyen) vs methode corrigee (sinistres valorises) : portefeuille
CREATE OR REPLACE VIEW v_naive_vs_corrected AS
SELECT
    frequency_declared * avg_cost                          AS pure_premium_naive,
    pure_premium                                           AS pure_premium_corrected,
    frequency_declared * avg_cost / pure_premium - 1       AS overestimation
FROM v_kpi_global;

-- Meme comparaison par age du vehicule : indice de risque (prime pure ecretee, 100 = portefeuille)
CREATE OR REPLACE VIEW v_naive_vs_corrected_by_vehicle_age AS
WITH claims_per_policy AS (
    SELECT policy_id, COUNT(*) AS n_amount, SUM(claim_amount_capped) AS cost_capped FROM fact_claim GROUP BY policy_id
), seg AS (
    SELECT p.vehicle_age_band, v.sort_order, SUM(p.exposure) AS exposure, SUM(p.claim_nb) AS declared,
           SUM(COALESCE(c.n_amount, 0)) AS n_amount, SUM(COALESCE(c.cost_capped, 0)) AS cost_capped
    FROM fact_policy p
    JOIN dim_vehicle_age_band v USING (vehicle_age_band)
    LEFT JOIN claims_per_policy c USING (policy_id)
    GROUP BY ALL
), total AS (
    SELECT SUM(exposure) AS exposure, SUM(declared) AS declared, SUM(n_amount) AS n_amount, SUM(cost_capped) AS cost_capped FROM seg
)
SELECT
    seg.vehicle_age_band,
    seg.sort_order,
    100 * (seg.declared / seg.exposure * seg.cost_capped / seg.n_amount)
        / (total.declared / total.exposure * total.cost_capped / total.n_amount)  AS index_naive,
    100 * (seg.cost_capped / seg.exposure) / (total.cost_capped / total.exposure) AS index_corrected
FROM seg, total
ORDER BY seg.sort_order;

-- Rupture dans les identifiants : part des contrats declarant au moins un sinistre, par tranche de 5 000 identifiants
CREATE OR REPLACE VIEW v_declared_share_by_id_bucket AS
SELECT
    CASE WHEN policy_id < 50000 THEN CAST(FLOOR(policy_id / 5000) * 5000 AS INTEGER) ELSE 50000 END AS id_bucket_start,
    COUNT(*)                                   AS policies,
    AVG((claim_nb > 0)::INTEGER)               AS share_with_declared_claim,
    AVG((claims_with_amount > 0)::INTEGER)     AS share_with_valued_claim
FROM fact_policy
GROUP BY ALL
ORDER BY id_bucket_start;

-- Age du conducteur x bonus-malus : les deux facteurs sont lies (tout nouveau conducteur demarre a 100)
CREATE OR REPLACE VIEW v_driver_age_by_bonus_malus AS
WITH claims_per_policy AS (
    SELECT policy_id, SUM(claim_amount_capped) AS cost_capped FROM fact_claim GROUP BY policy_id
), cells AS (
    SELECT p.driver_age_band, p.bonus_malus_band, b.sort_order AS bm_order, SUM(p.exposure) AS exposure,
           SUM(COALESCE(c.cost_capped, 0)) AS cost_capped
    FROM fact_policy p
    JOIN dim_bonus_malus_band b USING (bonus_malus_band)
    LEFT JOIN claims_per_policy c USING (policy_id)
    GROUP BY ALL
)
SELECT
    driver_age_band,
    bonus_malus_band,
    bm_order,
    exposure / SUM(exposure) OVER (PARTITION BY driver_age_band)            AS exposure_share_within_age,
    100 * (cost_capped / exposure) / (SELECT pure_premium_capped FROM v_kpi_global) AS index_vs_portfolio
FROM cells
ORDER BY driver_age_band, bm_order;
