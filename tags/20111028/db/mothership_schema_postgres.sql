--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: application_instances; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE application_instances (
    ip inet,
    port integer,
    created_at timestamp with time zone,
    tag character varying(100),
    started_at timestamp with time zone,
    scms_version_id integer,
    id integer NOT NULL
);


ALTER TABLE public.application_instances OWNER TO mothership;

--
-- Name: application_instances_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE application_instances_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.application_instances_id_seq OWNER TO mothership;

--
-- Name: application_instances_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE application_instances_id_seq OWNED BY application_instances.id;


--
-- Name: dns_addendum; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE dns_addendum (
    realm character varying(10),
    site_id character varying(3),
    host character varying(100),
    target character varying(200),
    record_type character varying(10),
    id integer NOT NULL
);


ALTER TABLE public.dns_addendum OWNER TO mothership;

--
-- Name: dns_addendum_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE dns_addendum_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.dns_addendum_id_seq OWNER TO mothership;

--
-- Name: dns_addendum_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE dns_addendum_id_seq OWNED BY dns_addendum.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: mothership; Tablespace: 
--

CREATE TABLE groups (
    description character varying(150),
    sudo_cmds character varying(2000),
    groupname character varying(64) NOT NULL,
    site_id character varying(3) NOT NULL,
    realm character varying(10) NOT NULL,
    gid integer NOT NULL,
    id integer NOT NULL
);


ALTER TABLE public.groups OWNER TO mothership;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: mothership
--

CREATE SEQUENCE groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.groups_id_seq OWNER TO mothership;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mothership
--

ALTER SEQUENCE groups_id_seq OWNED BY groups.id;


--
-- Name: hardware; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE hardware (
    hw_tag character varying(200) NOT NULL,
    purchase_date date,
    manufacturer character varying(100),
    cores integer,
    ram integer,
    disk character varying(100),
    site_id character varying(3),
    id integer NOT NULL,
    rack_id character varying(20),
    cost integer,
    kvm_switch character varying(20),
    kvm_port smallint,
    power_port smallint,
    power_switch character varying(20),
    model character varying(200),
    cpu_sockets smallint,
    cpu_speed character varying(20),
    rma boolean NOT NULL
);


ALTER TABLE public.hardware OWNER TO mothership;

--
-- Name: hardware_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE hardware_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.hardware_id_seq OWNER TO mothership;

--
-- Name: hardware_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE hardware_id_seq OWNED BY hardware.id;


--
-- Name: kv_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE kv_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.kv_id_seq OWNER TO mothership;

--
-- Name: kv; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE kv (
    key character varying(100) NOT NULL,
    value character varying(200),
    hostname character varying(200),
    site_id character varying(3),
    realm character varying(10),
    id integer DEFAULT nextval('kv_id_seq'::regclass) NOT NULL
);


ALTER TABLE public.kv OWNER TO mothership;

--
-- Name: network; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE network (
    mac character varying(17),
    site_id character varying(3),
    realm character varying(10),
    vlan integer,
    id integer NOT NULL,
    netmask character varying(15),
    server_id integer,
    interface character varying(15),
    switch character varying(30),
    switch_port character varying(50),
    ip inet,
    bond_options character varying(300),
    hw_tag character varying(200),
    static_route inet,
    public_ip inet
);


ALTER TABLE public.network OWNER TO mothership;

--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.network_id_seq OWNER TO mothership;

--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE network_id_seq OWNED BY network.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tags (
    name character varying(50),
    start_port integer,
    stop_port integer,
    id integer NOT NULL,
    security_level smallint
);


ALTER TABLE public.tags OWNER TO mothership;

--
-- Name: tags_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.tags_id_seq OWNER TO mothership;

--
-- Name: tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tags_id_seq OWNED BY tags.id;


--
-- Name: server_graveyard; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE server_graveyard (
    hostname character varying(200),
    site_id character varying(3),
    realm character varying(10),
    tag character varying(20),
    tag_index smallint,
    cores smallint,
    ram integer,
    disk integer,
    hw_tag character varying(200),
    os character varying(15),
    cobbler_profile character varying(50),
    comment character varying(1000),
    id integer NOT NULL,
    provision_date date,
    deprovision_date date,
    virtual boolean,
    security_level smallint,
    cost integer,
    zabbix_template character varying(300)
);


ALTER TABLE public.server_graveyard OWNER TO mothership;

--
-- Name: server_graveyard_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE server_graveyard_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.server_graveyard_id_seq OWNER TO mothership;

--
-- Name: server_graveyard_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE server_graveyard_id_seq OWNED BY server_graveyard.id;


--
-- Name: servers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE servers (
    hostname character varying(200),
    site_id character varying(3),
    realm character varying(10),
    tag character varying(20),
    tag_index smallint,
    cores smallint,
    ram integer,
    disk integer,
    hw_tag character varying(200),
    os character varying(15),
    cobbler_profile character varying(50),
    comment character varying(1000),
    id integer NOT NULL,
    virtual boolean,
    provision_date date,
    security_level smallint,
    cost integer,
    active boolean,
    zabbix_template character varying(300)
);


ALTER TABLE public.servers OWNER TO mothership;

--
-- Name: servers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE servers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.servers_id_seq OWNER TO mothership;

--
-- Name: servers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE servers_id_seq OWNED BY servers.id;


--
-- Name: system_services; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE system_services (
    name character varying(200),
    ip inet,
    server_id integer
);


ALTER TABLE public.system_services OWNER TO mothership;

--
-- Name: user_group_mapping; Type: TABLE; Schema: public; Owner: mothership; Tablespace: 
--

CREATE TABLE user_group_mapping (
    groups_id integer,
    users_id integer,
    id integer NOT NULL
);


ALTER TABLE public.user_group_mapping OWNER TO mothership;

--
-- Name: user_group_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: mothership
--

CREATE SEQUENCE user_group_mapping_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.user_group_mapping_id_seq OWNER TO mothership;

--
-- Name: user_group_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mothership
--

ALTER SEQUENCE user_group_mapping_id_seq OWNED BY user_group_mapping.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: mothership; Tablespace: 
--

CREATE TABLE users (
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    ssh_public_key character varying(4096),
    username character varying(64) NOT NULL,
    site_id character varying(3) NOT NULL,
    realm character varying(10) NOT NULL,
    uid integer NOT NULL,
    id integer NOT NULL,
    type character varying(15),
    hdir character varying(100),
    shell character varying(100),
    active boolean DEFAULT true,
    email character varying(100)
);


ALTER TABLE public.users OWNER TO mothership;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: mothership
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO mothership;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mothership
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: xen_pools; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE xen_pools (
    server_id integer NOT NULL,
    realm character varying(10),
    pool_id smallint
);


ALTER TABLE public.xen_pools OWNER TO mothership;

--
-- Name: zeus_cluster; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE zeus_cluster (
    cluster_name character varying(50),
    vhost character varying(300),
    ip inet,
    public_ip inet,
    id integer NOT NULL,
    port integer,
    tg_name character varying(200)
);


ALTER TABLE public.zeus_cluster OWNER TO mothership;

--
-- Name: zeus_cluster_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE zeus_cluster_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.zeus_cluster_id_seq OWNER TO mothership;

--
-- Name: zeus_cluster_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE zeus_cluster_id_seq OWNED BY zeus_cluster.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE application_instances ALTER COLUMN id SET DEFAULT nextval('application_instances_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE dns_addendum ALTER COLUMN id SET DEFAULT nextval('dns_addendum_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: mothership
--

ALTER TABLE groups ALTER COLUMN id SET DEFAULT nextval('groups_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE hardware ALTER COLUMN id SET DEFAULT nextval('hardware_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE tags ALTER COLUMN id SET DEFAULT nextval('tags_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE server_graveyard ALTER COLUMN id SET DEFAULT nextval('server_graveyard_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE servers ALTER COLUMN id SET DEFAULT nextval('servers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: mothership
--

ALTER TABLE user_group_mapping ALTER COLUMN id SET DEFAULT nextval('user_group_mapping_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: mothership
--

ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE zeus_cluster ALTER COLUMN id SET DEFAULT nextval('zeus_cluster_id_seq'::regclass);


--
-- Name: application_instances_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY application_instances
    ADD CONSTRAINT application_instances_pkey PRIMARY KEY (id);


--
-- Name: dns_addendum_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY dns_addendum
    ADD CONSTRAINT dns_addendum_pkey PRIMARY KEY (id);


--
-- Name: group_realm_site_id; Type: CONSTRAINT; Schema: public; Owner: mothership; Tablespace: 
--

ALTER TABLE ONLY groups
    ADD CONSTRAINT group_realm_site_id PRIMARY KEY (groupname, realm, site_id);


--
-- Name: groups_id_key; Type: CONSTRAINT; Schema: public; Owner: mothership; Tablespace: 
--

ALTER TABLE ONLY groups
    ADD CONSTRAINT groups_id_key UNIQUE (id);


--
-- Name: hardware_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY hardware
    ADD CONSTRAINT hardware_pkey PRIMARY KEY (hw_tag);


--
-- Name: kv_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY kv
    ADD CONSTRAINT kv_id_key UNIQUE (id);


--
-- Name: kv_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY kv
    ADD CONSTRAINT kv_pkey PRIMARY KEY (id);


--
-- Name: network_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: server_graveyard_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY server_graveyard
    ADD CONSTRAINT server_graveyard_pkey PRIMARY KEY (id);


--
-- Name: servers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_pkey PRIMARY KEY (id);


--
-- Name: user_group_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: mothership; Tablespace: 
--

ALTER TABLE ONLY user_group_mapping
    ADD CONSTRAINT user_group_mapping_pkey PRIMARY KEY (id);


--
-- Name: user_realm_site_id; Type: CONSTRAINT; Schema: public; Owner: mothership; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT user_realm_site_id PRIMARY KEY (username, realm, site_id);


--
-- Name: users_id_key; Type: CONSTRAINT; Schema: public; Owner: mothership; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_id_key UNIQUE (id);


--
-- Name: xen_pools_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY xen_pools
    ADD CONSTRAINT xen_pools_pkey PRIMARY KEY (server_id);


--
-- Name: zeus_cluster_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY zeus_cluster
    ADD CONSTRAINT zeus_cluster_pkey PRIMARY KEY (id);


--
-- Name: system_services_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY system_services
    ADD CONSTRAINT system_services_server_id_fkey FOREIGN KEY (server_id) REFERENCES servers(id);


--
-- Name: user_group_mapping_groups_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mothership
--

ALTER TABLE ONLY user_group_mapping
    ADD CONSTRAINT user_group_mapping_groups_id_fkey FOREIGN KEY (groups_id) REFERENCES groups(id);


--
-- Name: user_group_mapping_users_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mothership
--

ALTER TABLE ONLY user_group_mapping
    ADD CONSTRAINT user_group_mapping_users_id_fkey FOREIGN KEY (users_id) REFERENCES users(id);


--
-- Name: xen_pools_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY xen_pools
    ADD CONSTRAINT xen_pools_server_id_fkey FOREIGN KEY (server_id) REFERENCES servers(id);


--
-- PostgreSQL database dump complete
--

