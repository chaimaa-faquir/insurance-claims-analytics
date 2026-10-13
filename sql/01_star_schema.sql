-- Etape 3a - Modele en etoile (constellation de faits) pour Power BI
-- Deux tables de faits partagent les memes dimensions :
--   fact_policy : une ligne par contrat (exposition, sinistres declares / valorises / sans montant, lot de donnees)
--   fact_claim  : une ligne par sinistre avec montant (cle du contrat + cles de dimensions)
-- Les dimensions de tranches portent un sort_order pour le tri dans Power BI.

-- Dimensions --------------------------------------------------------------------------------
CREATE OR REPLACE TABLE dim_region AS
SELECT * FROM (VALUES
    ('R11', 'Île-de-France'), ('R21', 'Champagne-Ardenne'), ('R22', 'Picardie'),
    ('R23', 'Haute-Normandie'), ('R24', 'Centre'), ('R25', 'Basse-Normandie'),
    ('R26', 'Bourgogne'), ('R31', 'Nord-Pas-de-Calais'), ('R41', 'Lorraine'),
    ('R42', 'Alsace'), ('R43', 'Franche-Comté'), ('R52', 'Pays de la Loire'),
    ('R53', 'Bretagne'), ('R54', 'Poitou-Charentes'), ('R72', 'Aquitaine'),
    ('R73', 'Midi-Pyrénées'), ('R74', 'Limousin'), ('R82', 'Rhône-Alpes'),
    ('R83', 'Auvergne'), ('R91', 'Languedoc-Roussillon'),
    ('R93', 'Provence-Alpes-Côte d''Azur'), ('R94', 'Corse')
) AS t(region_code, region_name);

CREATE OR REPLACE TABLE dim_area AS
SELECT * FROM (VALUES
    ('A', 'A - Densité très faible', 1), ('B', 'B - Densité faible', 2), ('C', 'C - Densité moyenne', 3),
    ('D', 'D - Densité élevée', 4), ('E', 'E - Densité très élevée', 5), ('F', 'F - Urbain dense', 6)
) AS t(area_code, area_label, sort_order);

CREATE OR REPLACE TABLE dim_driver_age_band AS
SELECT * FROM (VALUES
    ('18-24', 1), ('25-34', 2), ('35-44', 3), ('45-54', 4), ('55-64', 5), ('65-74', 6), ('75+', 7)
) AS t(driver_age_band, sort_order);

CREATE OR REPLACE TABLE dim_vehicle_age_band AS
SELECT * FROM (VALUES ('0', 1), ('1-2', 2), ('3-5', 3), ('6-10', 4), ('11-15', 5), ('16+', 6))
AS t(vehicle_age_band, sort_order);

CREATE OR REPLACE TABLE dim_bonus_malus_band AS
SELECT * FROM (VALUES ('50 (bonus max)', 1), ('51-74', 2), ('75-99', 3), ('100 (départ)', 4), ('101+ (malus)', 5))
AS t(bonus_malus_band, sort_order);

CREATE OR REPLACE TABLE dim_vehicle_power_band AS
SELECT * FROM (VALUES ('4-5', 1), ('6-7', 2), ('8-9', 3), ('10+', 4))
AS t(vehicle_power_band, sort_order);

CREATE OR REPLACE TABLE dim_fuel AS
SELECT * FROM (VALUES ('Diesel', 'Diesel'), ('Regular', 'Essence')) AS t(fuel, fuel_label);

-- Marques anonymisees dans la source (B1...B14) : tri numerique pour eviter B1, B10, B11, ..., B2
CREATE OR REPLACE TABLE dim_vehicle_brand AS
SELECT DISTINCT
    vehicle_brand,
    CAST(SUBSTR(vehicle_brand, 2) AS INTEGER) AS sort_order
FROM read_parquet('data/processed/clean_policies.parquet');

-- Faits -------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE fact_policy AS
SELECT *
FROM read_parquet('data/processed/clean_policies.parquet');

-- Les cles de dimensions sont recopiees sur fact_claim pour eviter de filtrer les sinistres
-- "a travers" la table des contrats (relations simples, sens unique, dans Power BI).
CREATE OR REPLACE TABLE fact_claim AS
SELECT
    c.claim_id,
    c.policy_id,
    c.claim_amount,
    c.claim_amount_capped,
    c.is_large_claim,
    p.region_code,
    p.area_code,
    p.driver_age_band,
    p.vehicle_age_band,
    p.bonus_malus_band,
    p.vehicle_power_band,
    p.vehicle_brand,
    p.fuel
FROM read_parquet('data/processed/clean_claims.parquet') AS c
JOIN fact_policy AS p USING (policy_id);
