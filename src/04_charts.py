"""Etape 4 - Figure de synthese du README (docs/analyse_qualite_donnees.png).

Deux panneaux, calcules a partir des vues SQL du modele :
- rupture dans les identifiants de contrat : part des contrats declarant un sinistre (v_declared_share_by_id_bucket)
- indice de risque par age du vehicule, methode naive vs corrigee (v_naive_vs_corrected_by_vehicle_age)
Couleurs : paire bleu / orange verifiee pour le daltonisme et le contraste.
"""
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BLUE, ORANGE = "#2a78d6", "#eb6834"
NAVY, INK, INK2, MUTED, GRID = "#1F4E79", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
ANOMALY_ID_THRESHOLD = 25_000


def fr(value, decimals=0):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def style(ax):
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, labelcolor=MUTED)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    con = duckdb.connect(str(ROOT / "data" / "model.duckdb"), read_only=True)
    buckets = con.sql("SELECT id_bucket_start, share_with_declared_claim FROM v_declared_share_by_id_bucket").fetchall()
    vehicle = con.sql("SELECT vehicle_age_band, index_naive, index_corrected FROM v_naive_vs_corrected_by_vehicle_age").fetchall()
    naive = con.sql("SELECT * FROM v_naive_vs_corrected").fetchone()
    block = con.sql("SELECT policies, share_of_missing FROM v_data_quality_by_block WHERE data_block LIKE 'Lot anormal%'").fetchone()
    con.close()

    plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK, "ytick.color": INK2, "axes.edgecolor": "#c3c2b7"})
    fig = plt.figure(figsize=(14, 5.8), dpi=200)
    fig.text(0.02, 0.95, f"Un lot de {fr(block[0])} contrats faussait la mesure du risque", fontsize=19,
             fontweight="bold", color=NAVY, va="top")
    fig.text(0.02, 0.887, f"Il concentre {fr(block[1] * 100, 1)} % des sinistres déclarés sans montant ; calculée sur les "
             f"sinistres déclarés, la prime pure serait surestimée de {fr(naive[2] * 100)} % "
             f"({fr(naive[0])} € au lieu de {fr(naive[1])} €).", fontsize=11.5, color=INK2, va="top")

    # Panneau A : rupture dans les identifiants
    ax = fig.add_axes([0.045, 0.17, 0.42, 0.55])
    labels = [f"{fr(b)} +" if b >= 50_000 else fr(b) for b, _ in buckets]
    values = [s * 100 for _, s in buckets]
    colors = [ORANGE if b < ANOMALY_ID_THRESHOLD else BLUE for b, _ in buckets]
    ax.bar(range(len(values)), values, width=0.72, color=colors, edgecolor="white", linewidth=2)
    ax.set_xticks(range(len(values)), labels, fontsize=9.5, rotation=0)
    ax.set_xlabel("Identifiant de contrat (début de tranche de 5 000)", color=INK2)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100], ["0 %", "25 %", "50 %", "75 %", "100 %"])
    style(ax)
    first_normal = next(i for i, (b, _) in enumerate(buckets) if b >= ANOMALY_ID_THRESHOLD)
    ax.axvline(first_normal - 0.5, color=INK2, linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(first_normal - 0.6, 104, "rupture à 25 000", ha="right", va="center", fontsize=10, color=INK2)
    ax.text(0, values[0] + 2, f"{fr(values[0])} %", ha="center", va="bottom", fontsize=11.5, fontweight="bold")
    ax.text(first_normal, values[first_normal] + 2, f"{fr(values[first_normal], 1)} %", ha="center", va="bottom",
            fontsize=11.5, fontweight="bold")
    ax.set_title("Part des contrats déclarant un sinistre,\npar tranche d'identifiant", loc="left", fontsize=13,
                 fontweight="bold", pad=12)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=ORANGE), plt.Rectangle((0, 0), 1, 1, color=BLUE)],
              labels=["Lot anormal (identifiant < 25 000)", "Reste du portefeuille"], loc="upper left",
              bbox_to_anchor=(0, -0.16), ncol=2, frameon=False, fontsize=10.5)

    # Panneau B : indice naif vs corrige par age du vehicule
    bx = fig.add_axes([0.55, 0.17, 0.43, 0.55])
    x, w = range(len(vehicle)), 0.36
    bx.bar([i - w / 2 for i in x], [r[1] for r in vehicle], width=w, color=ORANGE, edgecolor="white", linewidth=2,
           label="Méthode naïve (sinistres déclarés)")
    bx.bar([i + w / 2 for i in x], [r[2] for r in vehicle], width=w, color=BLUE, edgecolor="white", linewidth=2,
           label="Méthode corrigée (sinistres valorisés)")
    bx.axhline(100, color=INK2, linestyle=(0, (4, 3)), linewidth=1.2)
    bx.text(len(vehicle) - 0.45, 104, "moyenne = 100", ha="right", va="bottom", color=INK2, fontsize=10)
    for dx, value in [(-w / 2, vehicle[0][1]), (w / 2, vehicle[0][2])]:
        bx.text(dx, value + 6, fr(value), ha="center", va="bottom", fontsize=13, fontweight="bold")
    bx.set_xticks(list(x), [f"{r[0]} an" if r[0] == "0" else f"{r[0]} ans" for r in vehicle])
    bx.set_xlabel("Âge du véhicule", color=INK2)
    bx.set_ylim(0, max(r[1] for r in vehicle) * 1.15)
    style(bx)
    bx.set_title(f"Indice de risque par âge du véhicule : les véhicules neufs\npassent de {fr(vehicle[0][1])} "
                 f"à {fr(vehicle[0][2])} une fois l'anomalie traitée", loc="left", fontsize=13, fontweight="bold", pad=12)
    bx.legend(loc="upper left", bbox_to_anchor=(0, -0.16), ncol=2, frameon=False, fontsize=10.5)

    out = ROOT / "docs" / "analyse_qualite_donnees.png"
    fig.savefig(out, facecolor="white")
    print(f"Figure : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
