# -*- coding: utf-8 -*-
"""
Fig. 2: Spatial relationship between the compound hazard exposure index (CHEI) and infrastructure access (IA).

This script generates:
1. Fig. 2b: Country-level scatterplot of CHEI and IA rankings.
2. Fig. 2c: Population distribution by income group and CHEI-IA category.
3. Fig. 2d: Global population share by CHEI-IA category.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# =============================================================================
# Read data
# =============================================================================

fname_country = './data/hazard_exposure_infrastructure_access_country_level.xlsx'
fname_county = './data/hazard_exposure_infrastructure_access_county_level.xlsx'

dfcountry = pd.read_excel(fname_country)
dfcounty = pd.read_excel(fname_county)

dfcountry['population'] = dfcountry['POP_EST_2017'] / 1000000  # million
dfcountry['rank_CHEI'] = dfcountry['CHEI_float'].rank(method='min', ascending=True)
dfcountry['rank_IA'] = dfcountry['IA'].rank(method='min', ascending=True)

dfcounty['rank_CHEI'] = dfcounty['CHEI_float'].rank(method='min', ascending=True)
dfcounty['rank_IA'] = dfcounty['IA'].rank(method='min', ascending=True)


# =============================================================================
# Fig. 2b: Country-level CHEI and IA rankings
# =============================================================================

color_map = {
    11: '#31B57B',
    12: '#3165C8',
    21: '#FDE624',
    22: '#FF5500',
}

population_categories = [10, 50, 150, 1000]
population_labels = ['0-30', '30-100', '100-1000', '>1000']
size_categories = [30, 200, 800, 2000]

pop_size_map = dict(zip(population_categories, size_categories))

dfcountry['circle_size'] = dfcountry['population'].apply(
    lambda x: pop_size_map[min(population_categories, key=lambda p: abs(p - x))]
)

dfcountry_sorted = dfcountry.sort_values('population', ascending=False)

sns.set(font_scale=1.35, style="ticks")
plt.figure(figsize=(10, 4.75), dpi=300)

sns.scatterplot(
    x='rank_CHEI',
    y='rank_IA',
    data=dfcountry_sorted,
    size='circle_size',
    sizes=(min(size_categories), max(size_categories)),
    edgecolor='black',
    hue='combined_level',
    palette=color_map,
    legend=False,
)

plt.xlabel('Compound hazard exposure index (#)')
plt.ylabel('Infrastructure access (#)')
plt.ylim(-5, 195)
plt.xlim(-5, 180)

selected_countries = [
    "China", "United States", "India", "Indonesia", "Pakistan",
    "Bangladesh", "Russia", "Nigeria", "Japan", "Brazil",
    "Philippines", "Congo", "Ethiopia", "Morocco", "Mexico",
    "Germany", "Italy", "France", "Spain", "Canada", "South Africa"
]

top_countries = dfcountry_sorted[dfcountry_sorted['NAME_EN'].isin(selected_countries)]

xy_positions = {
    'Mexico': (-4, -6),
    'Brazil': (4, 0),
    'Indonesia': (-4, -6),
    'Philippines': (0, 0),
    'Nigeria': (-4, -6),
    'Pakistan': (4, 4),
    'Bangladesh': (1, -5),
    'India': (5, 4),
    'Italy': (0, 0),
    'France': (0, 0),
    'Congo': (1, -1),
    "Turkey": (0, 0),
    "Morocco": (0, 0),
    "Spain": (1, 1),
    "Canada": (-0.5, -1),
    "Germany": (-1, 0),
    "South Africa": (0, -1),
}

xytext_positions = {
    'Mexico': (-20, -28),
    'Brazil': (40, 0),
    'United States': (60, 20),
    'Indonesia': (-22, -20),
    'China': (50, 50),
    'India': (45, 20),
    'Pakistan': (45, 10),
    'Bangladesh': (35, -20),
    'Thailand': (50, 20),
    'Vietnam': (40, 10),
    'Nigeria': (-25, -20),
    'Philippines': (0, 30),
    'Italy': (-35, -5),
    'France': (-30, 20),
    'Congo': (30, -30),
    "Morocco": (-32, -25),
    "Spain": (37, 12),
    "Canada": (-40, 45),
    "Germany": (-20, 30),
    "South Africa": (60, -8),
}

for _, row in top_countries.iterrows():
    country_name = row['NAME_EN']
    xy = xy_positions.get(country_name, (3, 3))
    xytext = xytext_positions.get(country_name, (35, 15))

    plt.annotate(
        country_name,
        (row['rank_CHEI'] + xy[0], row['rank_IA'] + xy[1]),
        xytext=(xytext[0], xytext[1]),
        textcoords='offset points',
        fontsize=12.5,
        color='black',
        ha='center',
        arrowprops=dict(arrowstyle='<-', color='black', lw=1)
    )

legend_handles = [
    plt.scatter([], [], s=size_categories[0], edgecolor='black', facecolor='none', label=population_labels[0]),
    plt.scatter([], [], s=size_categories[1], edgecolor='black', facecolor='none', label=population_labels[1]),
    plt.scatter([], [], s=size_categories[2], edgecolor='black', facecolor='none', label=population_labels[2]),
    plt.scatter([], [], s=size_categories[3], edgecolor='black', facecolor='none', label=population_labels[3])
]

plt.legend(
    handles=legend_handles,
    title="Population (million)",
    bbox_to_anchor=(1.12, 0.75),
    loc='upper left',
    borderaxespad=0,
    handletextpad=1,
    labelspacing=2.25,
    frameon=False,
    fontsize=14,
    title_fontsize=14
)

ax = plt.gca()
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

plt.tight_layout()
#plt.savefig('./results/fig2b_scatterplot_country.jpg', dpi=600, bbox_inches='tight')
plt.show()


# =============================================================================
# Fig. 2c: Population by income group and CHEI-IA category
# =============================================================================

level_mapping = {11: 'LL', 12: 'LH', 21: 'HL', 22: 'HH'}
region_order = ['Low', 'Lower-middle', 'Upper-middle', 'High']

custom_palette = {
    'HL': '#FDE624',
    'HH': '#FF5500',
    'LL': '#31B57B',
    'LH': '#3165C8',
}

dfsum = (
    dfcounty[['WorldPop', 'INCOME_GRP', 'combined_level']]
    .groupby(['combined_level'])
    .sum()
    .reset_index()
)

dfsum['level'] = dfsum['combined_level'].replace(level_mapping)

order = ['LL', 'LH', 'HL', 'HH']
dfsum = dfsum.set_index('level').loc[order].reset_index()

labels = dfsum['level']
sizes = dfsum['WorldPop']
colors = [custom_palette[level] for level in dfsum['level']]

sns.set(font_scale=1.8, style="ticks", palette='bright')
fig, ax = plt.subplots(figsize=(7, 5), dpi=300)

ax.pie(
    sizes,
    autopct='%1.0f%%',
    startangle=90,
    colors=colors,
    wedgeprops={'edgecolor': 'black'}
)

#plt.savefig('./results/fig2c_piechart_county.jpg', dpi=600, bbox_inches='tight')
plt.show()


# =============================================================================
# Fig. 2d: Global population share by CHEI-IA category
# =============================================================================

dfsum2 = (
    dfcounty[['WorldPop', 'INCOME_GRP', 'combined_level']]
    .groupby(['INCOME_GRP', 'combined_level'])
    .sum()
    .reset_index()
)

dfsum2['level'] = dfsum2['combined_level'].replace(level_mapping)

sns.set(font_scale=2, style="ticks", palette='bright')
fig, ax = plt.subplots(1, 1, figsize=(10, 5), dpi=300)

sns.barplot(
    data=dfsum2,
    x="INCOME_GRP",
    y="WorldPop",
    hue="level",
    order=region_order,
    palette=custom_palette,
    errwidth=1,
    capsize=0.1,
)

plt.xlabel('Income group')
plt.ylabel('Population')
plt.yticks([0, 0.5e9, 1e9, 1.5e9, 2e9])
ax.legend_.remove()

fig.tight_layout()
#plt.savefig('./results/fig2d_barplot_income_group.jpg', dpi=600, bbox_inches='tight')
plt.show()

