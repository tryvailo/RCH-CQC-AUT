# Funding Eligibility Report

**RightCareHome - Comprehensive Care Funding Analysis**

---

## Fair Cost Gap Analysis

| Period | Amount |
|--------|--------|
| **Per Week** | £{{ weekly_gap | round(2) }} |
| **Per Year** | £{{ yearly_gap | int | format_number }} |
| **Over 5 Years** | £{{ five_year_gap | int | format_number }} |

{{ emotional_text }}

---

{% if potential_savings_per_year > 0 %}
## Potential Savings

| Period | Amount |
|--------|--------|
| **Per Week** | £{{ potential_savings_per_week | round(2) }} |
| **Per Year** | £{{ potential_savings_per_year | int | format_number }} |
| **Over 5 Years** | £{{ potential_savings_5_years | int | format_number }} |

These savings are based on potential CHC eligibility and Local Authority funding options.

---

{% endif %}
## CHC Eligibility Assessment

**Probability:** {{ chc_probability }}%

**Status:** {% if chc_likely_eligible %}Likely Eligible{% else %}May Not Meet Threshold{% endif %}

{{ chc_reasoning }}

{% if chc_key_factors %}
### Key Factors:

{% for factor in chc_key_factors %}
- {{ factor }}
{% endfor %}
{% endif %}

---

## Local Authority Funding

**Top-up Probability:** {{ top_up_probability }}%

**Deferred Payment Eligible:** {% if deferred_payment_eligible %}Yes{% else %}No{% endif %}

{% if weekly_contribution %}
**Weekly Contribution:** £{{ weekly_contribution | round(2) }}
{% endif %}

{{ deferred_payment_reasoning }}

---

{% if recommendations %}
## Recommendations

{% for rec in recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}
{% endif %}

---

## Get Your Full Funding Report

**Detailed analysis, personalized recommendations, and step-by-step guidance**

### £119

Contact us to receive your comprehensive funding report.

