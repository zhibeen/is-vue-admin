from apiflask import APIBlueprint

customs_bp = APIBlueprint('customs', __name__, url_prefix='/customs', tag='关务管理')

from . import routes
from . import files


