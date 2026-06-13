# -*- coding: utf-8 -*-
"""
Fig. 4:  Future human exposure to extreme heat days at the country scale.

This script generates:
1. Fig. 4k: Lineplot of future heat exposure trajectories under SSP scenarios.
2. Fig. 4i: Barplot of future heat exposure by income group and SSP scenario.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =============================================================================
# Settings
# =============================================================================

models = ['CanESM5', 'CNRM-ESM2-1', 'GFDL-ESM4', 'MPI-ESM1-2-LR', 'UKESM1-0-LL']
ssps = ['ssp126', 'ssp245', 'ssp585']
yearlist = [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]

income_order = ['Low', 'Lower middle', 'Upper middle', 'High']


# =============================================================================
# Read country metadata
# =============================================================================

dfcountry = pd.read_excel('./data/hazard_exposure_infrastructure_access_country_level.xlsx')

dfcountry["INCOME_GRP"] = (
    dfcountry["INCOME_GRP"]
    .str.replace("-", " ", regex=False)
)

dfhead = dfcountry[['UID', 'CONTINENT', 'NAME_EN', 'INCOME_GRP']]


# =============================================================================
# Read and combine future heat exposure data
# =============================================================================

dfall = []

for model in models:
    for sce in ssps:
        fname = f'./data/future_hazard_exposure/future_exposure_heat_{model}_{sce}_level0.csv'
        df = pd.read_csv(fname)
        dfall.append(df)

dfall = pd.concat(dfall, axis=0)


# =============================================================================
# Reshape and calculate multi-model mean exposure
# =============================================================================

exp_columns = [f'exp_{year}' for year in yearlist]

df_melted = dfall.melt(
    id_vars=['UID', 'Model', 'Scenario'],
    value_vars=exp_columns,
    var_name='Year',
    value_name='Exposure'
)

df_melted['Year'] = df_melted['Year'].str.extract('(\d+)').astype(int)
df_melted2 = df_melted.loc[df_melted['Year'] > 2020]

dfmean = (
    df_melted
    .groupby(['UID', 'Scenario', 'Year'])['Exposure']
    .mean()
    .reset_index()
)

dfmean = pd.merge(dfhead, dfmean, on='UID')


# =============================================================================
# Fig. 4k: Future heat exposure trajectories
# =============================================================================

sns.set(font_scale=2.5, style="ticks")

plt.figure(figsize=(12, 5), dpi=300)

sns.lineplot(
    data=dfmean.loc[dfmean['Year'] > 2020],
    x='Year',
    y='Exposure',
    hue='Scenario',
    ci=95,
    marker='o',
    palette="Reds",
    lw=3
)

plt.xlabel('Year')
plt.ylabel('Heat exposure')
plt.ylim(5, 35)
plt.xticks(df_melted2['Year'].unique())
plt.legend(title='', frameon=False)

# plt.savefig('./results/fig4k_lineplot_heat_exposure.png', dpi=600, bbox_inches='tight')
plt.show()


# =============================================================================
# Fig. 4l: Future heat exposure by income group
# =============================================================================

fig, ax = plt.subplots(1, 1, figsize=(12, 5), dpi=600)

sns.barplot(
    data=dfmean.loc[dfmean['Year'] > 2020],
    x='INCOME_GRP',
    y='Exposure',
    hue='Scenario',
    order=income_order,
    palette="Reds",
    ax=ax,
    ci=95,
    width=0.75,
    errwidth=1,
    capsize=0.1
)

ax.set_xlabel('Income group')
ax.set_ylabel('Heat exposure')
ax.set_ylim(0, 35)

plt.legend(title='', frameon=False, ncol=1)

# plt.savefig('./results/fig4l_barplot_heat_exposure_income_group.jpg', dpi=600, bbox_inches='tight')
plt.show()