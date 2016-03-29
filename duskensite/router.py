def is_routed_model(model):
    return hasattr(model, 'connection_name')


class Router(object):
    """
    A router to point database operations on models to the right db.
    Using the attribute connection_name referring to the
    DATABASES-label in settings.py.

    Ref: https://docs.djangoproject.com/en/dev/topics/db/multi-db/
    """

    def allow_syncdb(self, db, model):
        """Do not create tables on the default db for models on $./manage.py sync,
         but this function maybe used know which db a model is on"""
        if is_routed_model(model):
            return db == model.connection_name
        return db == 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        model = hints.get('model')
        if is_routed_model(model):
            return db == model.connection_name
        return None

    def db_for_read(self, model, **hints):
        "Point all operations on models connection_name to db=connection_name"
        if is_routed_model(model):
            return model.connection_name
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on models connection_name to db=connection_name"
        if is_routed_model(model):
            return model.connection_name
        return None
