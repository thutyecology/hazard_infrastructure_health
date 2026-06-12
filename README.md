# Global disparities in compound hazard exposure and infrastructure access jeopardize health equity

This repository contains the data and code supporting the manuscript:

> **Tu et al.** "Global disparities in compound hazard exposure and infrastructure access jeopardize health equity." *Nature Communications* (under review).

---

## Repository Structure

```
├── data/
│   ├── hazard_exposure_infrastructure_access_country_level.xlsx   # Country-level hazard exposure and infrastructure access
│   ├── hazard_exposure_infrastructure_access_county_level.xlsx    # County-level hazard exposure and infrastructure access
│   ├── panel_data.xlsx                                            # Regression input data (HALE, GDP, population)
│   ├── future_hazard_exposure/                                    # Projected future hazard exposure
│   │   ├── future_exposure_flood_{GCM}_{SSP}_level0.csv          # Country-level flood exposure by GCM and SSP
│   │   ├── future_exposure_heat_{GCM}_{SSP}_level0.csv           # Country-level heat exposure by GCM and SSP
│   │   ├── future_exposure_flood_mean_{SSP}_level0.csv           # Multi-model mean flood exposure
│   │   ├── future_exposure_heat_mean_{SSP}_level0.csv            # Multi-model mean heat exposure
│   │   └── future_exposure_combined_{SSP}_level2.csv             # County-level combined hazard exposure levels
│   └── worldbank_administrative_units/                            # World Bank administrative boundaries (Shapefile)
│       ├── WB_level0_country.*                                    # Country-level boundaries (Admin 0)
│       └── WB_level2_county.*                                     # County-level boundaries (Admin 2)
├── fig1_hazard_exposure.py
├── fig2_hazard_exposure_infrastructure_access.py
├── fig3_future_exposure_flood.py
├── fig4_future_exposure_heat.py
├── fig5_future_exposure.py
├── table1_regression_analysis.py
└── results/                                                        # Pre-generated figure outputs
```

---

## Data Description

### `hazard_exposure_infrastructure_access_country_level.xlsx`
Country-level summary statistics. Key columns:

| Column | Description |
|--------|-------------|
| `UID` | Country unique identifier |
| `NAME_EN` | Country name |
| `INCOME_GRP` | World Bank income group |
| `exposure_flood` | Population-weighted flood exposure (days) averaged over 2000–2018 |
| `exposure_heat` | Population-weighted extreme heat exposure (days) averaged over 2000–2016 |
| `flood_level` / `heat_level` | Quartile-based classification (1–4) of flood/heat exposure |
| `CHEI` | Combined Hazard Exposure Index (1–4) |
| `IA` | Population-weighted infrastructure access score |
| `combined_level` | CHEI–IA combined category (11=LL, 12=LH, 21=HL, 22=HH) |

### `panel_data.xlsx`
Regression input data. Key columns:

| Column | Description |
|--------|-------------|
| `HALE` | Health-adjusted life expectancy (2020, from IHME) |
| `LnGDP` | Natural log of GDP |
| `LnPop` | Natural log of population |
| `LnPGDP` | Natural log of GDP per capita |
| `combined_level` | CHEI–IA category (used for one-hot encoding in regression) |

### `future_hazard_exposure/`
Projected human exposure to floods and extreme heat from 2020 to 2100 at decadal intervals, derived from Random Forest models trained on five CMIP6 GCMs under three SSP scenarios.

- **GCMs**: `CanESM5`, `CNRM-ESM2-1`, `GFDL-ESM4`, `MPI-ESM1-2-LR`, `UKESM1-0-LL`
- **Scenarios**: `ssp126`, `ssp245`, `ssp585`
- **Columns** (level0 files): `UID`, `exp_2020`, `exp_2030`, ..., `exp_2100`
- **Columns** (combined level2 files): flood/heat exposure values and quartile-based combined exposure levels (`level_2020`, ..., `level_2100`) at the county level

---

## Scripts

| Script | Description | Outputs |
|--------|-------------|---------|
| `fig1_hazard_exposure.py` | Country-level flood and heat exposure rankings and income-group comparisons | Fig. 1b,c |
| `fig2_hazard_exposure_infrastructure_access.py` | CHEI–IA relationship, population distribution by category | Fig. 2b–d |
| `fig3_future_exposure_flood.py` | Future flood exposure trajectories and income-group comparisons | Fig. 3k,l |
| `fig4_future_exposure_heat.py` | Future heat exposure trajectories and income-group comparisons | Fig. 4k,l |
| `fig5_future_exposure.py` | Proportion of counties with high compound exposure under each SSP | Fig. 5j–l |
| `table1_regression_analysis.py` | Multiple linear regression and ridge regression of HALE on hazard–infrastructure categories | Table 1 |

> **Note:** Global maps (Fig. 1a, 2a, 3a–j, 4a–j, 5a–i) were produced using ArcGIS.

---

## Requirements

Python 3.9+ is recommended. Install dependencies with:

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
seaborn>=0.12.0
statsmodels>=0.13.0
openpyxl>=3.0.0
```

---

## Usage

Run scripts from the repository root directory:

```bash
python fig1_hazard_exposure.py
python fig2_hazard_exposure_infrastructure_access.py
python fig3_future_exposure_flood.py
python fig4_future_exposure_heat.py
python fig5_future_exposure.py
python table1_regression_analysis.py
```

All scripts use relative paths and expect to be run from the repository root. Output figures are saved to `./results/`.

---

## Citation

If you use this code or data, please cite:

> Tu, Y., Chen, B., Zhao, Q., Meng, Q., Guan, D., Sun, Y., Wang, Y., Wei, H., Zhou, H., Xu, G., Song, Y., Xu, B., & Liao, C. (2026). Global disparities in compound hazard exposure and infrastructure access jeopardize health equity. *Nature Communications*. [DOI to be added upon publication]

---

## License

The code in this repository is released under the [Creative Commons Attribution 4.0 International License](LICENSE).

---

## Contact

Ying Tu (ying.tu@uconn.edu)
