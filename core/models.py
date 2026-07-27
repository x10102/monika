from peewee import (AutoField, CharField, Model, SqliteDatabase)

database = SqliteDatabase(None)

class ModelBase(Model):
    class Meta:
        database = database

class User(ModelBase):
    user_id = AutoField()
    discord_id = CharField(max_length=20)
    discord_name = CharField(max_length=128)
    display_name = CharField(max_length=128)

def get_core_models() -> list[type[ModelBase]]:
    return [User]