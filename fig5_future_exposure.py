# -*- coding: utf-8 -*-
"""
Fig. 5: Projected human exposure to combined hazards of flood and extreme heat.

This script generates:
1. Fig. 5j-l: Lineplots of the proportion of high flood-high heat exposure areas under SSP scenarios.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =============================================================================
# Settings
# =============================================================================

ssps = ['ssp126', 'ssp245', 'ssp585']
years = list(range(2020, 2110, 10))


# =============================================================================
# Fig. 5j-l: Proportion of high flood-high heat areas
# =============================================================================

for ssp in ssps:
    fname = f'./data/future_hazard_exposure/future_exposure_combined_{ssp}_level2.csv'
    dfcombined = pd.read_csv(fname)

    ratios = []

    for year in years:
        col = f'level_{year}'

        ratio = 100 * (dfcombined[col] == 44).sum() / len(dfcombined)
        ratio1 = 100 * (dfcombined[col] == 41).sum() / len(dfcombined)
        ratio2 = 100 * (dfcombined[col] == 14).sum() / len(dfcombined)

        ratios.append([year, ratio, ratio1, ratio2])

    df_ratio = pd.DataFrame(ratios, columns=['year', 'HH', 'HL', 'LH'])

    sns.set(font_scale=2.25, style="ticks")

    fig, ax = plt.subplots(1, 1, figsize=(11, 3), dpi=600)

    sns.lineplot(
        data=df_ratio.loc[df_ratio['year'] > 2020],
        x='year',
        y='HH',
        color='#79379D',
        marker='o',
        markersize=15,
        lw=5
    )

    plt.ylabel("Proportion (%)")
    plt.xlabel("Year")
    ax.set_ylim(0, 60)

    # plt.savefig(f'./results/fig5j-l_lineplot_high_exposure_proportion_{ssp}.jpg',
    #             dpi=600, bbox_inches='tight')
    plt.show()