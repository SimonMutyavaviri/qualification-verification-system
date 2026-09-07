"""HTTP blueprints. Routes stay thin and delegate to the service layer."""

from app.routes.admin_routes import bp as admin_bp
from app.routes.auth_routes import bp as auth_bp
from app.routes.main_routes import bp as main_bp
from app.routes.qualification_routes import bp as qualifications_bp
from app.routes.verification_routes import bp as verification_bp

ALL_BLUEPRINTS = (
    main_bp,
    auth_bp,
    qualifications_bp,
    verification_bp,
    admin_bp,
)

__all__ = [
    "ALL_BLUEPRINTS",
    "admin_bp",
    "auth_bp",
    "main_bp",
    "qualifications_bp",
    "verification_bp",
]
