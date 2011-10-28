#[u'hostname',
# u'site_id',
# u'realm',
# u'tag',
# u'tag_index',
# u'cores',
# u'ram',
# u'disk',
# u'hw_tag',
# u'os',
# u'cobbler_profile',
# u'comment',
# u'id',
# u'virtual',
# u'provision_date',
# u'security_level',
# u'cost',
# u'active',
# u'zabbix_template']

from sqlalchemy import orm, Table, MetaData

class Server(object):
    def __init__(self, shipd):
        self.shipd = shipd
        self.servers = Table('servers', self.shipd.metadata, autoload=True)
        self.kv = Table('kv', self.shipd.metadata, autoload=True)
        
    def return_servers(self):
        q = self.servers.select().execute()
        res = q.fetchall()
        servers = {'servers' : [] }
        for server in res:
            servers['servers'].append(server[0])
        return servers
    
    def return_servertag(self, tag):
        class SV(object):
            pass
    
        servermapper = orm.mapper(SV, self.servers)
        res = { 'server' : [] }
        try:
            q = self.shipd.dbsess.query(SV).filter(SV.tag==tag).all()
            for s in q:
                res['server'].append({'hostname': s.hostname,
                                      'realm': s.realm,
                                      'tag': s.tag
                                      })
        except orm.exc.NoResultFound:
            return 'No results found'

        class KV(object):
            pass
        kvmapper = orm.mapper(KV, self.kv)
        srv = []
        q = self.shipd.dbsess.query(KV).filter(KV.value==tag).all()
        for v in q:
            srv.append(v.hostname)
        for hostname in srv:
            try:
                q = self.shipd.dbsess.query(SV).filter(SV.hostname==hostname).one()
                res['server'].append({'hostname': hostname,
                                      'realm': q.realm,
                                      'tag': q.tag
                                      })
            except orm.exc.NoResultFound:
                pass
        return res
               
    def return_server(self, server):
        class SV(object):
            pass

        servermapper = orm.mapper(SV, self.servers)
        try:
            q = self.shipd.dbsess.query(SV).filter(SV.hostname==server).one()
        except orm.exc.NoResultFound:
            return 'No results found'
        res = {'hostname': q.hostname,
               'realm': q.realm,
               'tag' : q.tag,
               'cores': q.cores,
               'ram' : q.ram,
               'disk' : q.disk,
               'provision_date': str(q.provision_date)
               }
        return res
