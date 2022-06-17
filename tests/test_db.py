import unittest

import sqlalchemy as sa
import testing.postgresql
from sqlalchemy import select
from sqlalchemy.ext.declarative import declarative_base

import lvtn_utils
from lvtn_utils import ProjectWorker

base = declarative_base()


class Model(base):
    __tablename__ = "testdb"
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(lvtn_utils.UTCDateTime, default=lvtn_utils.get_date)
    updated = sa.Column(lvtn_utils.UTCDateTime)
    value = sa.Column(sa.String, unique=True)


class BaseDatabase(unittest.TestCase):
    def create_app(self):
        raise Exception("Not implemented")

    def setUp(self):
        super().setUp()
        self.app = self.create_app()
        base.metadata.bind = self.app._session.get_bind()
        base.metadata.create_all()

    def tearDown(self):
        super().tearDown()
        base.metadata.bind = self.app._session.get_bind()
        base.metadata.drop_all(bind=self.app._engine)
        self.app.close_app()


class Cases:
    def test_utcdatetime_type(self):

        with self.app.db_session() as session:
            session.add(Model(value="x"))
            m = session.query(Model).first()
            assert m.created
            assert m.created.tzname() == "UTC"
            assert "+00:00" in str(m.created)

            current = lvtn_utils.get_date("2018-09-07T20:22:02.249389+00:00")
            m.updated = current
            session.commit()

            m = session.query(Model).first()
            assert str(m.updated) == str(current)

            t = lvtn_utils.get_date()
            m.created = t
            session.commit()
            m = session.query(Model).first()
            assert m.created == t

            # new sqlalchemy 2.0 query style

            result = session.execute(select(Model).filter_by(id=1)).first()
            assert result[0].created == t

        with self.app.db_session() as session:
            t = Model(value="foo")
            session.add(t)
            session.commit()

        # do nothing (no error raised)
        with self.app.db_session() as session:
            t = Model(value="foo")
            upsert = self.app.upsert_stmt(t, conflicts=["value"])
            session.execute(upsert)

        # update value on conflict
        with self.app.db_session() as session:
            t = Model(value="foo")
            upsert = self.app.upsert_stmt(t, conflicts=["value"], update={"value": "bar"})
            session.execute(upsert)

        with self.app.db_session() as session:
            t = session.query(Model).filter_by(id=2).one()
            assert t.value == "bar"


class TestSqlite(BaseDatabase, Cases):
    def create_app(self):
        return ProjectWorker(
            "testsqlite",
            local_config={"SQLALCHEMY_URL": "sqlite:///", "SQLALCHEMY_ECHO": False},
        )


class TestPostgres(BaseDatabase, Cases):
    postgresql_url_dict = {
        "port": 1234,
        "host": "127.0.0.1",
        "user": "postgres",
        "database": "test",
    }
    postgresql_url = "postgresql://{user}@{host}:{port}/{database}".format(
        user=postgresql_url_dict["user"],
        host=postgresql_url_dict["host"],
        port=postgresql_url_dict["port"],
        database=postgresql_url_dict["database"],
    )

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(**cls.postgresql_url_dict)

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()

    def create_app(self):
        """Start the wsgi application"""

        a = ProjectWorker(
            "testpostgres",
            local_config={
                "SQLALCHEMY_URL": self.postgresql_url,
                "SQLALCHEMY_ECHO": False,
            },
        )
        return a


if __name__ == "__main__":
    unittest.main()
