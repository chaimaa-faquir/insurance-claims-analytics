"""Etape 3 - Construction du modele en etoile (DuckDB) et export pour Power BI.

- Execute sql/01_star_schema.sql puis sql/02_kpi_views.sql
- Exporte chaque table du modele en Parquet dans data/powerbi/ (source du rapport Power BI)
- Ecrit reports/kpi_summary.md : chiffres de reference pour valider les mesures DAX
"""
from pathlib import Path
import os

import duckdb

ROOT = Path(__file__).resolve().parents[1]
EXPORT, REPORTS = ROOT / "data" / "powerbi", ROOT / "reports"
TABLES = ["fact_policy", "fact_claim", "dim_region", "dim_area", "dim_driver_age_band",
          "dim_vehicle_age_band", "dim_bonus_malus_band", "dim_vehicle_power_band",
          "dim_fuel", "dim_vehicle_brand"]
SEGMENT_ORDER = {
    "Âge conducteur": ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"],
    "Âge véhicule": ["0", "1-2", "3-5", "6-10", "11-15", "16+"],
    "Bonus-malus": ["50 (bonus max)", "51-74", "75-99", "100 (départ)", "101+ (malus)"],
}


def num(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def pct(value, decimals=1):
    return num(value * 100, decimals) + " %"


def eur(value, decimals=0):
    return num(value, decimals) + " €"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---:" if i else "---" for i in range(len(header))) + "|"]
    return out + ["| " + " | ".join(r) + " |" for r in rows]


def main():
    os.chdir(ROOT)  # les chemins des fichiers SQL sont relatifs a la racine du projet
    EXPORT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "model.duckdb"))
    for sql_file in ["sql/01_star_schema.sql", "sql/02_kpi_views.sql"]:
        con.execute(Path(sql_file).read_text(encoding="utf-8"))

    for t in TABLES:
        con.execute(f"COPY {t} TO '{(EXPORT / t).as_posix()}.parquet' (FORMAT PARQUET)")
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:<24} {n:>9,} lignes")

    g = con.sql("SELECT * FROM v_kpi_global").fetchone()
    g = dict(zip(con.sql("SELECT * FROM v_kpi_global").columns, g))
    portfolio = table(["Indicateur", "Valeur"], [
        ["Contrats", num(g["policies"])],
        ["Exposition (années-contrats)", num(g["exposure_years"])],
        ["Sinistres déclarés", num(g["claims_declared"])],
        ["dont sans montant", f"{num(g['claims_without_amount'])} ({pct(g['missing_amount_share'])})"],
        ["Fréquence déclarée (qualité des données)", pct(g["frequency_declared"], 2)],
        ["Sinistres valorisés (avec montant)", num(g["claims_with_amount"])],
        ["**Fréquence** (sinistres valorisés)", pct(g["frequency"], 2)],
        ["Charge sinistres", eur(g["claims_cost"])],
        ["Coût moyen", eur(g["avg_cost"])],
        ["Coût moyen écrêté (50 000 €)", eur(g["avg_cost_capped"])],
        ["**Prime pure**", eur(g["pure_premium"], 1)],
        ["Prime pure écrêtée", eur(g["pure_premium_capped"], 1)],
        ["Sinistres graves (> 50 000 €)", num(g["large_claims"])],
        ["Part de la charge portée par les sinistres graves", pct(g["large_claims_cost_share"])],
    ])

    concentration = table(["Plus gros sinistres", "Nombre de sinistres", "Part de la charge"], [
        [pct(r[0], 1), num(r[1]), pct(r[2])]
        for r in con.sql("SELECT * FROM v_claims_concentration").fetchall()
    ])

    segments = []
    rows = con.sql("""
        SELECT axis, segment, exposure_share, frequency_declared, missing_amount_share, frequency,
               avg_cost_capped, pure_premium_capped, index_vs_portfolio, risk_rank
        FROM v_kpi_by_segment ORDER BY axis, index_vs_portfolio DESC
    """).fetchall()
    for axis in ["Âge conducteur", "Âge véhicule", "Bonus-malus", "Densité", "Région"]:
        axis_rows = [r for r in rows if r[0] == axis]
        if axis in SEGMENT_ORDER:
            axis_rows.sort(key=lambda r: SEGMENT_ORDER[axis].index(r[1]))
        elif axis == "Densité":
            axis_rows.sort(key=lambda r: r[1])
        else:
            axis_rows = [r for r in axis_rows if r[9] <= 5]  # regions : top 5
        segments += [f"### {axis}" + (" (top 5)" if axis == "Région" else ""), ""]
        segments += table(["Segment", "Part exposition", "Fréq. déclarée", "Part sans montant", "Fréquence",
                           "Coût moyen écrêté", "Prime pure écrêtée", "Indice"],
                          [[r[1], pct(r[2]), pct(r[3], 2), pct(r[4]), pct(r[5], 2), eur(r[6]), eur(r[7], 1), str(r[8])]
                           for r in axis_rows]) + [""]

    quality = table(["Lot de contrats", "Contrats", "Part du portefeuille", "Avec un sinistre déclaré", "Fréquence déclarée",
                     "Fréquence valorisée", "Sinistres sans montant", "Part des sinistres sans montant", "Véhicules neufs"], [
        [r[0], num(r[1]), pct(r[2]), pct(r[3]), pct(r[4], 2), pct(r[5], 2), num(r[6]), pct(r[7]), pct(r[8])]
        for r in con.sql("SELECT * FROM v_data_quality_by_block").fetchall()
    ])

    naive = con.sql("SELECT * FROM v_naive_vs_corrected").fetchone()
    naive_va = table(["Âge du véhicule", "Indice, méthode naïve", "Indice, méthode corrigée"], [
        [r[0], num(r[2]), num(r[3])] for r in con.sql("SELECT * FROM v_naive_vs_corrected_by_vehicle_age").fetchall()
    ])
    buckets = table(["Identifiants de contrat", "Contrats", "Avec un sinistre déclaré", "Avec un sinistre valorisé"], [
        [f"{num(r[0])} et plus" if r[0] == 50000 else f"{num(r[0])} à {num(r[0] + 4999)}", num(r[1]), pct(r[2]), pct(r[3])]
        for r in con.sql("SELECT * FROM v_declared_share_by_id_bucket").fetchall()
    ])
    cross_rows = con.sql("SELECT * FROM v_driver_age_by_bonus_malus").fetchall()
    bm_bands = SEGMENT_ORDER["Bonus-malus"]
    cross = table(["Âge du conducteur"] + bm_bands, [
        [age] + [next((f"{num(r[4])} ({pct(r[3], 0)})" for r in cross_rows if r[0] == age and r[1] == bm), "-") for bm in bm_bands]
        for age in SEGMENT_ORDER["Âge conducteur"]
    ])

    large = table(["Région", "Part exposition", "Sinistres graves", "Attendus selon l'exposition", "Charge brute", "Charge écrêtée"], [
        [r[0], pct(r[1]), num(r[2]), num(r[3], 1), eur(r[4]), eur(r[5])]
        for r in con.sql("SELECT * FROM v_large_claims_by_region LIMIT 5").fetchall()
    ])

    summary = [
        "# Indicateurs de référence",
        "",
        "Chiffres calculés en SQL (DuckDB) : ils servent à valider les mesures DAX du rapport Power BI.",
        "La fréquence et la prime pure sont calculées sur les sinistres valorisés ; la fréquence déclarée est",
        "suivie à part : 99,8 % des sinistres déclarés sans montant viennent d'un lot de contrats anormal.",
        "",
        "## Qualité des données : lot de contrats anormal",
        "",
        *quality,
        "",
        "## Méthode naïve vs méthode corrigée",
        "",
        f"Prime pure calculée avec la fréquence déclarée : {eur(naive[0], 1)}, contre {eur(naive[1], 1)} sur les sinistres "
        f"valorisés, soit une surestimation de {pct(naive[2])}.",
        "",
        *naive_va,
        "",
        "## Rupture dans les identifiants de contrat",
        "",
        *buckets,
        "",
        "## Portefeuille",
        "",
        *portfolio,
        "",
        "## Concentration de la charge",
        "",
        *concentration,
        "",
        "## Segments (indice 100 = prime pure écrêtée moyenne du portefeuille)",
        "",
        *segments,
        "## Âge du conducteur × bonus-malus",
        "",
        "Indice de risque de chaque cellule (100 = portefeuille) et, entre parenthèses, part de l'exposition de la tranche",
        "d'âge. Tout nouveau conducteur démarre au coefficient 100 : l'âge et le bonus-malus sont liés.",
        "",
        *cross,
        "",
        "## Sinistres graves par région (top 5)",
        "",
        *large,
        "",
    ]
    (REPORTS / "kpi_summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"\nModele exporte dans {EXPORT.relative_to(ROOT)} | resume : reports/kpi_summary.md")
    con.close()


if __name__ == "__main__":
    main()
