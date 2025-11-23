from apiflask import APIBlueprint

system_bp = APIBlueprint('system', __name__, url_prefix='/system', tag='System Management')

# Import views to register routes
from . import roles
from . import users # Import Role CRUD API