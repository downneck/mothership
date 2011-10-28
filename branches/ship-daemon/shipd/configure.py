import yaml
from sqlalchemy import create_engine, orm, sql, MetaData

class Shipd(object):
    def __init__(self, cfg):
        yaml_config = open(cfg).read()
        all_configs = yaml.load(yaml_config)
        dbconfig = all_configs['db']
        dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
        engine = create_engine("postgresql://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
        Session = orm.sessionmaker(bind=engine)
        dbsession = Session()
        self.dbconfig = dbconfig
        self.metadata = MetaData()
        self.metadata.bind = engine
        self.metadata.create_all()
        self.dbconn = engine.connect()
        self.dbengine = engine
        self.dbsess = dbsession
        self.dbnull = sql.expression.null()
