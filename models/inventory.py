from tortoise import fields
from tortoise.models import Model


class Inventory(Model):
    id = fields.IntField(primary_key=True, unique=True, index=True)
    item = fields.ForeignKeyField('models.Item', related_name='item')
    quantity_on_sunday = fields.IntField(min=0, default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "inventories"
