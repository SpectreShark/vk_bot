from tortoise import fields
from tortoise.models import Model


class Item(Model):
    id = fields.IntField(primary_key=True, unique=True, index=True)
    name = fields.CharField(unique=True, max_length=255)
    price = fields.FloatField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "items"
