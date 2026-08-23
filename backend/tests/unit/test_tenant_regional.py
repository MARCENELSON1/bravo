from __future__ import annotations

from app.application.identity.dtos import OnboardTenantInput
from app.domain.tenant.regional import TaxEngine, TaxRegime, regional_defaults
from tests.fakes import Harness

# --- regional_defaults (pure) ------------------------------------------------


def test_ar_defaults():
    d = regional_defaults("AR")
    assert d.tax_regime is TaxRegime.AR_AFIP
    assert d.currency == "ARS"
    assert d.locale == "es-AR"
    assert d.timezone == "America/Argentina/Buenos_Aires"
    assert d.tax_engine is TaxEngine.NONE


def test_us_defaults():
    d = regional_defaults("US")
    assert d.tax_regime is TaxRegime.US_SALES_TAX
    assert d.currency == "USD"
    assert d.locale == "en-US"
    assert d.tax_engine is TaxEngine.TAXJAR


def test_case_insensitive():
    assert regional_defaults("us") == regional_defaults("US")


def test_unknown_country_falls_back_to_ar():
    assert regional_defaults("ZZ") == regional_defaults("AR")


def test_none_and_empty_fall_back_to_ar():
    assert regional_defaults(None) == regional_defaults("AR")
    assert regional_defaults("") == regional_defaults("AR")


# --- onboarding derives the spine -------------------------------------------


async def _onboard(h: Harness, *, slug: str, country: str | None = None) -> object:
    kwargs = {
        "tenant_name": "Resto",
        "tenant_slug": slug,
        "owner_email": "owner@resto.com",
        "owner_password": "Sup3rSecret!",
    }
    if country is not None:
        kwargs["country"] = country
    await h.onboard_tenant().execute(OnboardTenantInput(**kwargs))
    return await h.tenants.get_by_slug(slug)


async def test_onboard_us_sets_us_spine():
    h = Harness()
    tenant = await _onboard(h, slug="brooklyn", country="US")
    assert tenant is not None
    assert tenant.country == "US"
    assert tenant.currency == "USD"
    assert tenant.tax_regime is TaxRegime.US_SALES_TAX
    assert tenant.locale == "en-US"
    assert tenant.tax_engine is TaxEngine.TAXJAR


async def test_onboard_default_is_ar_parity():
    # No country passed → AR spine, exactly as before the spine existed.
    h = Harness()
    tenant = await _onboard(h, slug="palermo")
    assert tenant is not None
    assert tenant.country == "AR"
    assert tenant.currency == "ARS"
    assert tenant.tax_regime is TaxRegime.AR_AFIP
    assert tenant.locale == "es-AR"
    assert tenant.tax_engine is TaxEngine.NONE


async def test_onboard_lowercase_country_is_normalized():
    h = Harness()
    tenant = await _onboard(h, slug="miami", country="us")
    assert tenant is not None
    assert tenant.country == "US"
    assert tenant.tax_regime is TaxRegime.US_SALES_TAX
