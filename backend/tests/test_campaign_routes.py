from app.main import app


def test_campaign_endpoints_use_english_paths() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/campaigns/{id_campaign}/publish" in paths
    assert "/api/v1/campaigns/{id_campaign}/close" in paths
    assert "/api/v1/campaigns/{id_campaign}/gauge" in paths
    assert "/api/v1/catalogue/campaigns" in paths
    assert "/api/v1/campagnes" not in paths
    assert "/api/v1/campagnes/{id_campaign}/cloturer" not in paths
    assert "/api/v1/campagnes/{id_campaign}/publier" not in paths
    assert "/api/v1/campagnes/{id_campaign}/jauge" not in paths
    assert "/api/v1/catalogue/campagnes" not in paths
    gauge_schema = paths["/api/v1/campaigns/{id_campaign}/gauge"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert gauge_schema == "#/components/schemas/GaugeOut"
    schemas = app.openapi()["components"]["schemas"]
    assert set(schemas["PublicationIn"]["properties"]) == {
        "is_published",
        "published_at",
    }
    assert set(schemas["GaugeOut"]["properties"]) == {
        "id_campaign",
        "goal",
        "collected_amount",
        "percentage",
    }
