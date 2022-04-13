from .crud_project import project
from .crud_user import user
from .crud_project_model import project_model
from .crud_datasets import dataset
from .crud_feedback import feedback
from .crud_reply import feedback_reply

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
