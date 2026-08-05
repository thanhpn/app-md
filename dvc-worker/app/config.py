from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://dvcworker:dvcworker@localhost:5433/dvcworker"
    session_secret_key: str = "dev-secret-change-me"
    admin_username: str = "admin"
    admin_password: str = "admin"
    log_level: str = "INFO"

    # dvc-api/apps/reviews push target — see app/services/reviews_client.py.
    # reviews_api_base_url is the gateway path for the reviews app itself
    # (…/api/v1/reviews); admin auth (login/refresh) lives at the IAM root,
    # derived from this by stripping the "/api/v1/reviews" suffix.
    reviews_api_base_url: str = ""
    reviews_app_key: str = ""
    reviews_admin_email: str = ""
    reviews_admin_password: str = ""

    # Shopee Affiliate Open API — see app/adapters/shopee_affiliate.py.
    # app_id/secret come from Shopee's affiliate dashboard after approval,
    # never from Source.config (secrets don't belong in a DB JSON column
    # editable from the admin UI's plain textarea).
    shopee_affiliate_api_base_url: str = "https://open-api.affiliate.shopee.vn/graphql"
    shopee_affiliate_app_id: str = ""
    shopee_affiliate_secret: str = ""


settings = Settings()
