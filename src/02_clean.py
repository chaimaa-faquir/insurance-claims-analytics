"""Etape 2 - Nettoyage et controle qualite.

Regles appliquees (chacune est mesuree dans reports/data_quality_report.md) :
1. Controles bloquants : doublons de contrats ou valeurs manquantes -> le pipeline s'arrete.
2. Exposition plafonnee a 1 an (le portefeuille est observe sur une annee au plus).
3. Nombre de sinistres declares plafonne a 4 par contrat (valeurs au-dela jugees aberrantes).
4. Sinistres "orphelins" (sans contrat correspondant) exclus.
5. Ages extremes conserves mais regroupes dans les tranches hautes (pas de suppression de lignes).
6. Sinistres graves : montant > 50 000 EUR, signales et ecretes pour une vision "charge ecretee".

Point d'attention : 27 % des sinistres declares n'ont pas de montant. Ils sont presque tous (99,8 %)
concentres dans un lot de contrats d'identifiant < 25 000 (1,4 % du portefeuille) ou quasiment chaque
contrat declare un sinistre, sans montant dans la table des sinistres : une anomalie de chargement.
Hors de ce lot, frequence declaree et frequence valorisee coincident. Les indicateurs de sinistralite
sont donc calcules sur les sinistres valorises ; le lot est signale dans la colonne data_block.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, REPORTS = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "reports"

MAX_EXPOSURE = 1.0
MAX_CLAIMS = 4
LARGE_CLAIM_THRESHOLD = 50_000
ANOMALY_ID_THRESHOLD = 25_000  # lot de contrats anormal identifie par l'analyse de cause racine
BLOCK_LABELS = ("Lot anormal (IDpol < 25 000)", "Reste du portefeuille")

# Tranches : bornes inferieures incluses, la derniere tranche est ouverte
BANDS = {
    "driver_age_band": ("DrivAge", [18, 25, 35, 45, 55, 65, 75],
                        ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]),
    "vehicle_age_band": ("VehAge", [0, 1, 3, 6, 11, 16], ["0", "1-2", "3-5", "6-10", "11-15", "16+"]),
    # 100 = coefficient de depart de tout nouveau conducteur (clause type de reduction-majoration), 101+ = malus
    "bonus_malus_band": ("BonusMalus", [50, 51, 75, 100, 101], ["50 (bonus max)", "51-74", "75-99", "100 (départ)", "101+ (malus)"]),
    "vehicle_power_band": ("VehPower", [4, 6, 8, 10], ["4-5", "6-7", "8-9", "10+"]),
}


def fr_int(value):
    return f"{value:,}".replace(",", " ")


def fr_pct(value, decimals=1):
    return f"{value * 100:.{decimals}f}".replace(".", ",") + " %"


def add_band(df, column, source, edges, labels):
    banded = pd.cut(df[source], bins=edges + [np.inf], labels=labels, right=False)
    if banded.isna().any():
        raise ValueError(f"Controle bloquant : {int(banded.isna().sum())} valeurs de {source} hors tranches")
    df[column] = banded.astype(str)


def missing_amount_table(policies, axis_col, axis_label, order):
    g = policies.groupby(axis_col, observed=True)[["claim_nb", "claims_without_amount"]].sum().reindex(order)
    rows = [f"| {axis_label} | Sinistres déclarés | dont sans montant | Part sans montant |", "|---|---:|---:|---:|"]
    for segment, r in g.iterrows():
        rows.append(f"| {segment} | {fr_int(int(r.claim_nb))} | {fr_int(int(r.claims_without_amount))} | "
                    f"{fr_pct(r.claims_without_amount / r.claim_nb)} |")
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    pol = pd.read_parquet(RAW / "freMTPL2freq.parquet")
    sev = pd.read_parquet(RAW / "freMTPL2sev.parquet")
    checks = []

    # --- Contrats ---------------------------------------------------------
    pol["IDpol"] = pol["IDpol"].astype("int64")
    duplicates, missing = int(pol["IDpol"].duplicated().sum()), int(pol.isna().sum().sum())
    if duplicates or missing:
        raise ValueError(f"Controle bloquant : {duplicates} contrats en double, {missing} valeurs manquantes")
    checks.append(("Contrats en double (bloquant)", duplicates))
    checks.append(("Valeurs manquantes (bloquant)", missing))
    checks.append(("Exposition > 1 an (plafonnée à 1)", int((pol["Exposure"] > MAX_EXPOSURE).sum())))
    checks.append((f"Contrats avec plus de {MAX_CLAIMS} sinistres déclarés (plafonnés)", int((pol["ClaimNb"] > MAX_CLAIMS).sum())))
    checks.append(("Âge conducteur > 90 ans", int((pol["DrivAge"] > 90).sum())))
    checks.append(("Âge véhicule > 20 ans", int((pol["VehAge"] > 20).sum())))

    pol["exposure"] = pol["Exposure"].clip(upper=MAX_EXPOSURE)
    pol["claim_nb"] = pol["ClaimNb"].clip(upper=MAX_CLAIMS).astype("int16")
    for column, (source, edges, labels) in BANDS.items():
        add_band(pol, column, source, edges, labels)

    policies = pol.rename(columns={
        "IDpol": "policy_id", "Area": "area_code", "VehPower": "vehicle_power", "VehAge": "vehicle_age",
        "DrivAge": "driver_age", "BonusMalus": "bonus_malus", "VehBrand": "vehicle_brand",
        "VehGas": "fuel", "Density": "density", "Region": "region_code",
    })[["policy_id", "exposure", "claim_nb", "region_code", "area_code", "density", "driver_age",
        "driver_age_band", "vehicle_age", "vehicle_age_band", "vehicle_power", "vehicle_power_band",
        "vehicle_brand", "fuel", "bonus_malus", "bonus_malus_band"]]
    for col in ["region_code", "area_code", "vehicle_brand", "fuel"]:
        policies[col] = policies[col].astype(str)

    # --- Sinistres --------------------------------------------------------
    sev["IDpol"] = sev["IDpol"].astype("int64")
    orphans = ~sev["IDpol"].isin(policies["policy_id"])
    checks.append(("Sinistres sans contrat (exclus)", int(orphans.sum())))
    sev = sev[~orphans].copy()

    # Rapprochement sinistres declares / sinistres valorises, contrat par contrat
    n_valued = sev.groupby("IDpol").size()
    policies["claims_with_amount"] = policies["policy_id"].map(n_valued).fillna(0).astype("int16")
    policies["claims_without_amount"] = (policies["claim_nb"] - policies["claims_with_amount"]).clip(lower=0).astype("int16")
    policies["data_block"] = np.where(policies["policy_id"] < ANOMALY_ID_THRESHOLD, *BLOCK_LABELS)
    over = policies["claims_with_amount"] > policies["claim_nb"]
    checks.append(("Contrats avec sinistre déclaré mais sans montant", int(((policies["claim_nb"] > 0) & (policies["claims_with_amount"] == 0)).sum())))
    checks.append(("Sinistres déclarés sans montant", int(policies["claims_without_amount"].sum())))
    checks.append((f"Contrats avec plus de sinistres valorisés que déclarés (plafond de {MAX_CLAIMS})", int(over.sum())))
    checks.append((f"Sinistres graves (> {fr_int(LARGE_CLAIM_THRESHOLD)} EUR)", int((sev["ClaimAmount"] > LARGE_CLAIM_THRESHOLD).sum())))

    claims = sev.rename(columns={"IDpol": "policy_id", "ClaimAmount": "claim_amount"}).reset_index(drop=True)
    claims.insert(0, "claim_id", claims.index + 1)
    claims["is_large_claim"] = claims["claim_amount"] > LARGE_CLAIM_THRESHOLD
    claims["claim_amount_capped"] = claims["claim_amount"].clip(upper=LARGE_CLAIM_THRESHOLD)

    policies.to_parquet(OUT / "clean_policies.parquet", index=False)
    claims.to_parquet(OUT / "clean_claims.parquet", index=False)

    # --- Rapport qualite ------------------------------------------------------
    declared, without = int(policies["claim_nb"].sum()), int(policies["claims_without_amount"].sum())
    large_share = claims.loc[claims["is_large_claim"], "claim_amount"].sum() / claims["claim_amount"].sum()
    blocks = policies.groupby("data_block").agg(
        contracts=("policy_id", "size"), exposure=("exposure", "sum"), declared=("claim_nb", "sum"),
        valued=("claims_with_amount", "sum"), without=("claims_without_amount", "sum"),
        with_claim=("claim_nb", lambda x: (x > 0).mean()), new_vehicle=("vehicle_age", lambda x: (x == 0).mean()),
    ).reindex(BLOCK_LABELS)
    in_block = blocks.loc[BLOCK_LABELS[0]]
    lines = [
        "# Rapport de qualité des données",
        "",
        f"- Contrats : {fr_int(len(policies))} | Sinistres valorisés (avec montant) : {fr_int(len(claims))}",
        f"- Sinistres déclarés (après plafonnement) : {fr_int(declared)}, dont {fr_int(without)} sans montant "
        f"({fr_pct(without / declared)})",
        f"- Part de la charge portée par les sinistres graves : {fr_pct(large_share)}",
        "",
        "## Contrôles",
        "",
        "| Contrôle | Lignes concernées |",
        "|---|---:|",
    ] + [f"| {label} | {fr_int(value)} |" for label, value in checks] + [
        "",
        "## Sinistres déclarés sans montant : analyse de cause racine",
        "",
        "**Symptôme.** Plus d'un sinistre déclaré sur quatre n'a pas de montant, et cette part semble dépendre du",
        "segment : 77 % pour les véhicules de moins d'un an, contre 15 à 21 % ailleurs. En fréquence déclarée, les",
        "véhicules neufs apparaissent ainsi plus de trois fois plus risqués que la moyenne.",
        "",
        *missing_amount_table(policies, "vehicle_age_band", "Âge du véhicule", BANDS["vehicle_age_band"][2]),
        "",
        f"**Cause.** Les sinistres sans montant ne sont pas répartis dans le portefeuille : "
        f"{fr_pct(in_block.without / without)} d'entre eux se trouvent dans un lot de {fr_int(int(in_block.contracts))} "
        f"contrats d'identifiant inférieur à {fr_int(ANOMALY_ID_THRESHOLD)} ({fr_pct(in_block.contracts / len(policies))} "
        "du portefeuille). Dans ce lot, presque chaque contrat déclare un sinistre, ce qui donne une fréquence déclarée",
        "impossible ; hors de ce lot, fréquence déclarée et fréquence valorisée coïncident.",
        "",
        "| Lot | Contrats | Contrats avec un sinistre déclaré | Fréquence déclarée | Fréquence valorisée | Sinistres sans montant | Véhicules neufs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ] + [
        f"| {name} | {fr_int(int(r.contracts))} | {fr_pct(r.with_claim)} | {fr_pct(r.declared / r.exposure, 2)} | "
        f"{fr_pct(r.valued / r.exposure, 2)} | {fr_int(int(r.without))} | {fr_pct(r.new_vehicle)} |"
        for name, r in blocks.iterrows()
    ] + [
        "",
        "**Explication de l'effet « véhicules neufs ».** Le lot anormal est composé à "
        f"{fr_pct(in_block.new_vehicle)} de véhicules neufs, contre {fr_pct(blocks.loc[BLOCK_LABELS[1]].new_vehicle)} "
        "dans le reste du portefeuille : ses sinistres déclarés sans montant gonflent la fréquence déclarée de ce segment.",
        "",
        "**Traitement.** Les indicateurs de sinistralité sont calculés sur les sinistres valorisés. Le lot est conservé",
        "(sa fréquence valorisée est proche de la moyenne) et signalé dans la colonne `data_block` ; l'anomalie est à",
        "remonter au propriétaire des données sources.",
        "",
    ]
    (REPORTS / "data_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:20]))


if __name__ == "__main__":
    main()
