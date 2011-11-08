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

