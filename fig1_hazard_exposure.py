# -*- coding: utf-8 -*-
"""
Fig. 1: Global human exposure to combined hazards of flood and extreme heat between 2000-2018.

This script generates:
1. Fig. 1b: Country-level scatterplot of flood and heat exposure rankings.
2. Fig. 1c: Barplots of flood and heat exposure by World Bank income group.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# =============================================================================
# Read data
# =============================================================================

fname_country = './data/hazard_exposure_infrastructure_access_country_level.xlsx'
dfcountry = pd.read_excel(fname_country)

dfcountry['rank_flood'] = dfcountry['exposure_flood'].rank(method='min', ascending=True)
dfcountry['rank_heat'] = dfcountry['exposure_heat'].rank(method='min', ascending=True)
dfcountry['population'] = dfcountry['POP_EST_2017'] / 1000000  # million


# =============================================================================
# Fig. 1b: Country-level flood and heat exposure rankings
# =============================================================================

color_map = {
    11: '#E9E9E9',
    12: '#E2B0AF',
    13: '#DB7777',
    14: '#D43F39',
    21: '#A1CEEA',
    22: '#A69DB9',
    23: '#AD6D8A',
    24: '#B63D5A',
    31: '#55B3E8',
    32: '#6C8BC5',
    33: '#80629E',
    34: '#973A7B',
    41: '#0A98E8',
    42: '#2E79CF',
    43: '#5457B5',
    44: '#79379D'
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
plt.figure(figsize=(10, 5), dpi=300)

sns.scatterplot(
    x='rank_flood',
    y='rank_heat',
    data=dfcountry_sorted,
    size='circle_size',
    sizes=(min(size_categories), max(size_categories)),
    edgecolor='black',
    hue='hazard_level',
    palette=color_map,
    legend=False,
)

plt.xlabel('Flood exposure (#)')
plt.ylabel('Heat exposure (#)')
plt.ylim(-5, 195)
plt.xlim(-5, 195)

uids = [
    8, 7,
    149, 0, 42, 16, 96, 123, 45, 174, 151, 12, 168,
    133, 15, 87, 1,
    76, 47, 122, 106, 53, 31, 83, 102, 56,
    90, 63, 20, 101, 291, 34, 25,
    # 18, 88, 156, 78, 4, 117,
]

labels = [
    'China', 'India',
    'United States', 'Indonesia', 'Brazil', 'Pakistan', 'Nigeria',
    'Bangladesh', 'Russia', 'Japan', 'Mexico', 'Ethiopia', 'Philippines',
    'Colombia', 'Kenya', 'Iraq', 'Malaysia',
    'United Kingdom', 'Germany', 'Myanmar', 'Thailand', 'Vietnam', 'Ukraine',
    'Sudan', 'Saudi Arabia', 'United Arab Emirates',
    'Iran', 'Turkey', 'France', 'Qatar', 'Congo', 'South Africa', 'Morocco',
]

uid_to_label = dict(zip(uids, labels))

xytext_positions = {
    'China': (30, -19),
    'United States': (-24, 3.5),
    'India': (12, 23),
    'United Kingdom': (10, -18),
    'Mexico': (2, 20),
    'Germany': (3, -20),
    'Indonesia': (22, -27),
    'Russia': (-5, 28),
    'Pakistan': (-18, 10),
    'Bangladesh': (30, 8),
    'Philippines': (22, -13),
    'Myanmar': (30, -11),
    'Thailand': (35, 0),
    'Vietnam': (50, -8),
    'Ukraine': (0, -22),
    'Sudan': (0, 15),
    'Saudi Arabia': (20, 8),
    'Nigeria': (-4, 20),
    'Iran': (0, -25),
    'Japan': (-20, -2),
    'Brazil': (-10, -20),
    'Turkey': (10, -18),
    'Ethiopia': (2, -25),
    'United Arab Emirates': (-5, 12),
    'Qatar': (-2, -18),
    'Congo': (-15, -12),
    'South Africa': (-5, -20),
    'Morocco': (-12, 11),
    'Colombia': (0, -22),
    'Kenya': (0, 15),
    'Iraq': (-12, -12),
    'Malaysia': (-12, -15),
}

xy_positions = {
    'India': (3, 9.5),
    'United States': (0, -6),
    'Bangladesh': (0, 1),
    'Thailand': (-1, 1),
    'Turkey': (-1, 0),
    'Vietnam': (0, -2),
}

for i in range(dfcountry_sorted.shape[0]):
    if dfcountry_sorted['UID'].iloc[i] in uid_to_label:
        country_name = uid_to_label[dfcountry_sorted['UID'].iloc[i]]
        x = dfcountry_sorted['rank_flood'].iloc[i]
        y = dfcountry_sorted['rank_heat'].iloc[i]

        xy = xy_positions.get(country_name, (0, 0))
        xytext = xytext_positions.get(country_name, (20, 5))

        plt.annotate(
            country_name,
            xy=(x + xy[0], y + xy[1]),
            xytext=(x + xytext[0], y + xytext[1]),
            fontsize=12,
            arrowprops=dict(facecolor='black', color='black', arrowstyle="<-"),
            ha='center'
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
    bbox_to_anchor=(1.07, 0.6),
    loc='upper left',
    borderaxespad=0,
    handletextpad=1,
    labelspacing=2.1,
    frameon=False,
    fontsize=14,
    title_fontsize=14
)

ax = plt.gca()
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

plt.tight_layout()
#plt.savefig('./results/fig1b_scatterplot_country.jpg', dpi=600, bbox_inches='tight')
plt.show()


# =============================================================================
# Fig. 1c: Exposure by income group
# =============================================================================

dfcountry["INCOME_GRP"] = (
    dfcountry["INCOME_GRP"]
    .str.replace("-", " ", regex=False)
    + " income"
)

income_order = [
    "Low income",
    "Lower middle income",
    "Upper middle income",
    "High income",
]

sns.set(font_scale=2, style="ticks")
fig, axs = plt.subplots(1, 2, figsize=(16, 4), dpi=600)

ax = axs[0]

sns.barplot(
    data=dfcountry,
    x="INCOME_GRP",
    y="exposure_flood",
    order=income_order,
    palette="Blues",
    ax=ax,
    ci=95,
    width=0.6,
    errwidth=1.5,
    capsize=0.2,
)

ax.set_xlabel("")
ax.set_ylabel("Flood exposure")
ax.set_xticks([])
ax.set_yticks([0.00, 0.05, 0.10, 0.15])

handles = [
    mpatches.Patch(
        color=sns.color_palette("Blues", len(income_order))[i],
        label=income_order[i],
    )
    for i in range(len(income_order))
]

ax.legend(handles=handles, title="", loc="upper right", frameon=False, fontsize=20)

ax = axs[1]

sns.barplot(
    data=dfcountry,
    x="INCOME_GRP",
    y="exposure_heat",
    order=income_order,
    palette="Reds",
    ax=ax,
    ci=95,
    width=0.6,
    errwidth=1.5,
    capsize=0.2,
)

ax.set_xlabel("")
ax.set_ylabel("Heat exposure")
ax.set_xticks([])
ax.set_ylim(0, 34)

handles = [
    mpatches.Patch(
        color=sns.color_palette("Reds", len(income_order))[i],
        label=income_order[i],
    )
    for i in range(len(income_order))
]

ax.legend(handles=handles, title="", loc="upper right", frameon=False, fontsize=20)

plt.tight_layout()
#plt.savefig("./results/fig1c_barplot_income_group.jpg", dpi=600, bbox_inches="tight")
plt.show()