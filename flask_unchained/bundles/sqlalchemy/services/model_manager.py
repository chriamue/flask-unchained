from flask_unchained import unchained
from flask_sqlalchemy_unchained import BaseQuery
from typing import *

from ..base_model import BaseModel as Model
from .session_manager import SessionManager


class ModelManager(SessionManager):
    """
    Base class for model managers.
    """
    __abstract__ = True

    # FIXME: Is there a way to get these type hints to understand that they're
    # FIXME: returning a specific subclass of db.Model as set by this attr?
    model: Union[str, Type[Model]] = Model
    """
    The model class a manager is for. In bundles this should be the model's class
    name as a string, however in user app bundles it's safe to make it the model
    class itself.
    """

    def __init__(self):
        super().__init__()
        try:
            self.model = unchained.sqlalchemy_bundle.models[self.model.__name__]
        except KeyError:
            pass

    @property
    def q(self) -> BaseQuery:
        """
        Alias for :meth:`query`.
        """
        return self.model.query

    @property
    def query(self) -> BaseQuery:
        """
        Returns the query class for this manager's model
        """
        return self.model.query

    def create(self, commit=False, **kwargs) -> model:
        """
        Creates an instance of the model, adding it to the database session,
        and optionally commits the session.

        :param commit: Whether or not to commit the database session.
        :param kwargs: The data to initialize the model with.
        :return: The model instance.
        """
        instance = self.model(**kwargs)
        self.save(instance, commit=commit)
        return instance

    def update(self, instance, commit=False, **kwargs) -> model:
        """
        Updates a model instance, adding it to the database session,
        and optionally commits the session.

        :param instance: The model instance to update.
        :param commit: Whether or not to commit the database session.
        :param kwargs: The data to update on the model.
        :return: The model instance.
        """
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        self.save(instance, commit=commit)
        return instance

    def get(self, id) -> Union[None, model]:
        """
        Return an instance based on the given primary key identifier,
        or ``None`` if not found.

        For example::

            my_user = session.query(User).get(5)

            some_object = session.query(VersionedFoo).get((5, 10))

        :meth:`~.Query.get` is special in that it provides direct
        access to the identity map of the owning :class:`.Session`.
        If the given primary key identifier is present
        in the local identity map, the object is returned
        directly from this collection and no SQL is emitted,
        unless the object has been marked fully expired.
        If not present,
        a SELECT is performed in order to locate the object.

        :meth:`~.Query.get` also will perform a check if
        the object is present in the identity map and
        marked as expired - a SELECT
        is emitted to refresh the object as well as to
        ensure that the row is still present.
        If not, :class:`~sqlalchemy.orm.exc.ObjectDeletedError` is raised.

        :meth:`~.Query.get` is only used to return a single
        mapped instance, not multiple instances or
        individual column constructs, and strictly
        on a single primary key value.  The originating
        :class:`.Query` must be constructed in this way,
        i.e. against a single mapped entity,
        with no additional filtering criterion.  Loading
        options via :meth:`~.Query.options` may be applied
        however, and will be used if the object is not
        yet locally present.

        A lazy-loading, many-to-one attribute configured
        by :func:`.relationship`, using a simple
        foreign-key-to-primary-key criterion, will also use an
        operation equivalent to :meth:`~.Query.get` in order to retrieve
        the target value from the local identity map
        before querying the database.  See :doc:`/orm/loading_relationships`
        for further details on relationship loading.

        :param id: A scalar or tuple value representing
         the primary key.   For a composite primary key,
         the order of identifiers corresponds in most cases
         to that of the mapped :class:`.Table` object's
         primary key columns.  For a :func:`.mapper` that
         was given the ``primary key`` argument during
         construction, the order of identifiers corresponds
         to the elements present in this collection.

        :return: The model instance, or ``None``.
        """
        return self.q.get(id)

    def get_or_create(self, commit=False, **kwargs) -> Tuple[model, bool]:
        """
        :return: returns a tuple of the instance and a boolean flag specifying
                 whether or not the instance was created
        """
        instance = self.get_by(**kwargs)
        if not instance:
            return self.create(commit=commit, **kwargs), True
        return instance, False

    def get_by(self, **kwargs) -> Union[None, model]:
        return self.q.get_by(**kwargs)

    def find_all(self) -> List[model]:
        return self.q.all()

    def find_by(self, **kwargs) -> List[model]:
        return self.q.filter_by(**kwargs).all()
