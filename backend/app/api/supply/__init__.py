from apiflask import APIBlueprint

supply_bp = APIBlueprint('supply', __name__, url_prefix='/supply', tag='Supply-供应链')

from . import routes

