"""
Table 1. Associations between hazard exposure, infrastructure access, and 
health-adjusted life expectancy (HALE) estimated using 
multiple linear regression (Model I) and ridge regression (Model II).

Dependent variable:
    HALE : Health-adjusted life expectancy.

Independent variables:
    combined_level : Combined hazard exposure and infrastructure access category.
                     11 = low exposure-low access (LL, reference category),
                     12 = low exposure-high access (LH),
                     21 = high exposure-low access (HL),
                     22 = high exposure-high access (HH).
    LnGDP          : Natural logarithm of gross domestic product (GDP).
    LnPop          : Natural logarithm of population.
"""


import pandas as pd
import numpy as np
import statsmodels.api as sm


# =============================================================================
# Read data
# =============================================================================

df = pd.read_excel('./data/panel_data.xlsx')


# =============================================================================
# Prepare variables
# =============================================================================

xvars = ['combined_level', 'LnGDP', 'LnPop']
# xvars = ['combined_level', 'LnPGDP', 'LnPop']

yvar = 'HALE'

X = df[xvars]
y = df[yvar]

# One-hot encode compound hazard exposure categories
X_encoded = pd.get_dummies(X, columns=['combined_level'])

# Reference category
drop_category = '11'
# drop_category = '12'
# drop_category = '21'
# drop_category = '22'

X_encoded = X_encoded.drop(columns=['combined_level_' + drop_category])

# Add intercept
X_encoded = sm.add_constant(X_encoded)
X_encoded = X_encoded.astype(int)

# =============================================================================
# Ordinary least squares regression
# =============================================================================

model = sm.OLS(y, X_encoded).fit()

print("Model I: Multiple Linear Regression")
print(model.summary())

ols_summary_table = pd.DataFrame({
    "Variable": model.params.index,
    "Coefficient": model.params.values,
    "Standard Error": model.bse.values,
    "t-Statistic": model.tvalues.values,
    "p-Value": model.pvalues.values,
    "95% CI Lower": model.conf_int()[0],
    "95% CI Upper": model.conf_int()[1],
})


# =============================================================================
# Ridge regression
# =============================================================================

def ridge_regression(X, y, alpha):
    """Estimate ridge regression coefficients without penalizing the intercept."""
    n, p = X.shape
    I = np.eye(p)
    I[0, 0] = 0
    ridge_coef = np.linalg.inv(X.T @ X + alpha * I) @ X.T @ y
    return ridge_coef


alpha_ridge = 0.5
y_array = df[yvar].values

ridge_coef = ridge_regression(X_encoded, y_array, alpha_ridge)

ridge_model = sm.OLS(y_array, X_encoded).fit()
ridge_model.params[:] = ridge_coef

print("\nModel II: Ridge Regression")
print(ridge_model.summary())

ridge_summary_table = pd.DataFrame({
    "Variable": ridge_model.params.index,
    "Coefficient": ridge_model.params.values,
    "Standard Error": ridge_model.bse.values,
    "t-Statistic": ridge_model.tvalues.values,
    "p-Value": ridge_model.pvalues.values,
    "95% CI Lower": ridge_model.conf_int()[0],
    "95% CI Upper": ridge_model.conf_int()[1],
})

