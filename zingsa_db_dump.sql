--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Drop databases (except postgres and template1)
--

DROP DATABASE template_postgis;
DROP DATABASE zingsa_collect;




--
-- Drop roles
--

DROP ROLE postgres;
DROP ROLE zingsa_user;


--
-- Roles
--

CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:KyDUEx+/FM1F20HgmMe5mA==$OI7++WAJD9xot+0xktNvJilAeToCxNcDJbhAoJYmE0s=:7r9Z5o40Bmd4IB8N+bVCHk5+Gt4jou6zpaYIeTEP+XA=';
CREATE ROLE zingsa_user;
ALTER ROLE zingsa_user WITH NOSUPERUSER INHERIT NOCREATEROLE CREATEDB LOGIN NOREPLICATION NOBYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:IicT2VKPqeXHg+j76RrJSg==$p+1CgUYIBHBLKRY4vfW98GIez3c5kMSHLMLOHdVGGQo=:gjoAbfBkCKAMKpMgVxvRULsborTFIY9FYM0TmJ2yo98=';

--
-- User Configurations
--








--
-- Databases
--

--
-- Database "template1" dump
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

UPDATE pg_catalog.pg_database SET datistemplate = false WHERE datname = 'template1';
DROP DATABASE template1;
--
-- Name: template1; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE template1 WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE template1 OWNER TO postgres;

\connect template1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE template1; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE template1 IS 'default template for new databases';


--
-- Name: template1; Type: DATABASE PROPERTIES; Schema: -; Owner: postgres
--

ALTER DATABASE template1 IS_TEMPLATE = true;


\connect template1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE template1; Type: ACL; Schema: -; Owner: postgres
--

REVOKE CONNECT,TEMPORARY ON DATABASE template1 FROM PUBLIC;
GRANT CONNECT ON DATABASE template1 TO PUBLIC;


--
-- PostgreSQL database dump complete
--

--
-- Database "postgres" dump
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE postgres;
--
-- Name: postgres; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE postgres WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE postgres OWNER TO postgres;

\connect postgres

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: postgres; Type: DATABASE PROPERTIES; Schema: -; Owner: postgres
--

ALTER DATABASE postgres SET search_path TO '$user', 'public', 'topology', 'tiger';


\connect postgres

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO postgres;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO postgres;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: postgres
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

--
-- Database "template_postgis" dump
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: template_postgis; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE template_postgis WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE template_postgis OWNER TO postgres;

\connect template_postgis

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: template_postgis; Type: DATABASE PROPERTIES; Schema: -; Owner: postgres
--

ALTER DATABASE template_postgis IS_TEMPLATE = true;
ALTER DATABASE template_postgis SET search_path TO '$user', 'public', 'topology', 'tiger';


\connect template_postgis

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO postgres;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO postgres;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: postgres
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: postgres
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

--
-- Database "zingsa_collect" dump
--

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg110+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg110+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: zingsa_collect; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE zingsa_collect WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.utf8';


ALTER DATABASE zingsa_collect OWNER TO postgres;

\connect zingsa_collect

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: zingsa_collect; Type: DATABASE PROPERTIES; Schema: -; Owner: postgres
--

ALTER DATABASE zingsa_collect SET search_path TO '$user', 'public', 'topology';


\connect zingsa_collect

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts_user (
    id bigint NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.accounts_user OWNER TO postgres;

--
-- Name: accounts_user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts_user_groups (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.accounts_user_groups OWNER TO postgres;

--
-- Name: accounts_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.accounts_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: accounts_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.accounts_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: accounts_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts_user_user_permissions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.accounts_user_user_permissions OWNER TO postgres;

--
-- Name: accounts_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.accounts_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.accounts_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auditlog_logentry; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auditlog_logentry (
    id integer NOT NULL,
    object_pk character varying(255) NOT NULL,
    object_id bigint,
    object_repr text NOT NULL,
    action smallint NOT NULL,
    changes text NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    actor_id bigint,
    content_type_id integer NOT NULL,
    remote_addr inet,
    additional_data jsonb,
    serialized_data jsonb,
    CONSTRAINT auditlog_logentry_action_check CHECK ((action >= 0))
);


ALTER TABLE public.auditlog_logentry OWNER TO postgres;

--
-- Name: auditlog_logentry_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auditlog_logentry ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auditlog_logentry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_agricultural_field_validation_survey_v1_aaeb9c7b (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name character varying(255),
    farmer character varying(255),
    photos text,
    croptype character varying(255),
    pesttype text,
    cropstage character varying(255),
    fieldcode character varying(255),
    irrigated character varying(255),
    signature text,
    pestdamage character varying(255),
    voicenotes text,
    damagenotes text,
    affectedarea integer,
    pestseverity character varying(255),
    fieldboundary public.geometry(Polygon,4326),
    irrigationtype text
);


ALTER TABLE public.collect_agricultural_field_validation_survey_v1_aaeb9c7b OWNER TO postgres;

--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq OWNER TO postgres;

--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq OWNED BY public.collect_agricultural_field_validation_survey_v1_aaeb9c7b.id;


--
-- Name: collect_community_census_data_collection_v1_72f41e4f; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_community_census_data_collection_v1_72f41e4f (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    notes text,
    headname character varying(255),
    housephoto text,
    householdid character varying(255),
    malemembers integer,
    watersource text,
    dwellingtype character varying(255),
    incomesource text,
    roofmaterial character varying(255),
    femalemembers integer,
    livestocktype text,
    childrenunder5 integer,
    lightingsource text,
    livestockowned character varying(255),
    toiletfacility character varying(255),
    otherwatersource character varying(255),
    electricityaccess character varying(255),
    electricitysource character varying(255),
    householdlocation public.geometry(Point,4326),
    otherincomesource character varying(255),
    opendefecationarea character varying(255)
);


ALTER TABLE public.collect_community_census_data_collection_v1_72f41e4f OWNER TO postgres;

--
-- Name: collect_community_census_data_collection_v1_72f41e4f_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_community_census_data_collection_v1_72f41e4f_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_community_census_data_collection_v1_72f41e4f_id_seq OWNER TO postgres;

--
-- Name: collect_community_census_data_collection_v1_72f41e4f_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_community_census_data_collection_v1_72f41e4f_id_seq OWNED BY public.collect_community_census_data_collection_v1_72f41e4f.id;


--
-- Name: collect_form; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_form (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    description text,
    mode character varying(50) NOT NULL,
    geometry_type character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    submission_table_name character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by_id bigint NOT NULL,
    project_id uuid NOT NULL,
    current_version_id uuid
);


ALTER TABLE public.collect_form OWNER TO postgres;

--
-- Name: collect_form_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_form_version (
    id uuid NOT NULL,
    version_number integer NOT NULL,
    version_label character varying(100) NOT NULL,
    schema jsonb NOT NULL,
    checksum character varying(64) NOT NULL,
    is_published boolean NOT NULL,
    physical_table_name character varying(255),
    column_mapping jsonb NOT NULL,
    published_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    created_by_id bigint NOT NULL,
    form_id uuid NOT NULL
);


ALTER TABLE public.collect_form_version OWNER TO postgres;

--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    geom public.geometry(Point,4326),
    pitdepth integer,
    pitstatus character varying(255),
    sitephotos text,
    watercolor character varying(255),
    mineraltype character varying(255),
    pitdiameter integer,
    waterfilled character varying(255),
    inspectiondate date,
    hazardsobserved text,
    inspectionnotes text,
    childrenobserved character varying(255),
    estimatedworkers integer,
    equipmentobserved text,
    recommendedaction text,
    siteaccessibility character varying(255),
    environmentaldamage text,
    rehabilitationneeded character varying(255)
);


ALTER TABLE public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 OWNER TO postgres;

--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq OWNER TO postgres;

--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq OWNED BY public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9.id;


--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e033286; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    audit_date date,
    audit_summary text,
    junction_type character varying(255),
    audit_time_period character varying(255),
    intersection_name character varying(255),
    conflict_observations text,
    inspector_audio_notes text,
    intersection_location public.geometry(Point,4326),
    signal_cycle_observed integer,
    count_duration_minutes integer,
    cyclist_volume_per_hour integer,
    vehicle_volume_per_hour integer,
    traffic_light_functional text,
    heavy_vehicles_percentage numeric,
    pedestrian_volume_per_hour integer,
    pedestrian_crossings_available text
);


ALTER TABLE public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 OWNER TO postgres;

--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq OWNER TO postgres;

--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq OWNED BY public.collect_intersection_traffic_pedestrian_audit_v1_6e033286.id;


--
-- Name: collect_organization; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_organization (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.collect_organization OWNER TO postgres;

--
-- Name: collect_organization_member; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_organization_member (
    id uuid NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    organization_id uuid NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.collect_organization_member OWNER TO postgres;

--
-- Name: collect_project; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_project (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    description text,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    organization_id uuid,
    owner_id bigint NOT NULL
);


ALTER TABLE public.collect_project OWNER TO postgres;

--
-- Name: collect_project_member; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_project_member (
    id uuid NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    project_id uuid NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.collect_project_member OWNER TO postgres;

--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57abe1a1; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    stop_id character varying(255),
    stop_name character varying(255),
    stop_photo text,
    has_shelter text,
    transit_mode character varying(255),
    routes_served character varying(255),
    safety_rating integer,
    stop_location public.geometry(Point,4326),
    general_comments character varying(255),
    real_time_display text,
    seating_available text,
    shelter_condition character varying(255),
    lighting_functional text,
    wheelchair_accessible text
);


ALTER TABLE public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 OWNER TO postgres;

--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq OWNER TO postgres;

--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq OWNED BY public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1.id;


--
-- Name: collect_road_network_survey_v1_5bea3d58; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_road_network_survey_v1_5bea3d58 (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    geom public.geometry(LineString,4326),
    roadname character varying(255),
    roadtype character varying(255),
    roadwidth integer,
    roadphotos text,
    surveydate date,
    surfacetype character varying(255),
    accessibility character varying(255),
    roadcondition character varying(255),
    trafficvolume character varying(255),
    conditionissues text,
    inspectionnotes text,
    digitalsignature text,
    maintenancerequired text
);


ALTER TABLE public.collect_road_network_survey_v1_5bea3d58 OWNER TO postgres;

--
-- Name: collect_road_network_survey_v1_5bea3d58_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_road_network_survey_v1_5bea3d58_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_road_network_survey_v1_5bea3d58_id_seq OWNER TO postgres;

--
-- Name: collect_road_network_survey_v1_5bea3d58_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_road_network_survey_v1_5bea3d58_id_seq OWNED BY public.collect_road_network_survey_v1_5bea3d58.id;


--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef056f; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_road_surface_quality_defect_assessment_v1_2cef056f (
    id bigint NOT NULL,
    submission_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    submitted_by_id integer,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    defect_photo text,
    pavement_type character varying(255),
    chainage_end_km numeric,
    defect_severity character varying(255),
    road_segment_id character varying(255),
    assessed_segment public.geometry(LineString,4326),
    segment_length_m integer,
    carriageway_lanes integer,
    chainage_start_km numeric,
    inspector_remarks text,
    drainage_condition character varying(255),
    highway_designation character varying(255),
    maintenance_urgency character varying(255),
    primary_defect_type character varying(255),
    defect_extent_percent integer,
    surface_condition_index integer
);


ALTER TABLE public.collect_road_surface_quality_defect_assessment_v1_2cef056f OWNER TO postgres;

--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq OWNER TO postgres;

--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq OWNED BY public.collect_road_surface_quality_defect_assessment_v1_2cef056f.id;


--
-- Name: collect_submission_index; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_submission_index (
    id uuid NOT NULL,
    device_id character varying(255) NOT NULL,
    client_submission_id character varying(255) NOT NULL,
    physical_table_name character varying(255) NOT NULL,
    physical_row_id integer NOT NULL,
    sync_status character varying(50) NOT NULL,
    synced_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    form_id uuid NOT NULL,
    form_version_id uuid NOT NULL,
    project_id uuid NOT NULL,
    submitted_by_id bigint
);


ALTER TABLE public.collect_submission_index OWNER TO postgres;

--
-- Name: collect_submission_media; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_submission_media (
    id uuid NOT NULL,
    field_id character varying(255) NOT NULL,
    file character varying(100),
    file_url character varying(1000),
    file_type character varying(50) NOT NULL,
    original_name character varying(255) NOT NULL,
    mime_type character varying(100) NOT NULL,
    size integer NOT NULL,
    checksum character varying(64),
    created_at timestamp with time zone NOT NULL,
    submission_index_id uuid NOT NULL
);


ALTER TABLE public.collect_submission_media OWNER TO postgres;

--
-- Name: collect_sync_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.collect_sync_log (
    id uuid NOT NULL,
    device_id character varying(255) NOT NULL,
    total_received integer NOT NULL,
    total_success integer NOT NULL,
    total_failed integer NOT NULL,
    conflict_count integer NOT NULL,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone NOT NULL,
    log jsonb,
    form_id uuid,
    project_id uuid,
    user_id bigint
);


ALTER TABLE public.collect_sync_log OWNER TO postgres;

--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id bigint NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_clockedschedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_clockedschedule (
    id integer NOT NULL,
    clocked_time timestamp with time zone NOT NULL
);


ALTER TABLE public.django_celery_beat_clockedschedule OWNER TO postgres;

--
-- Name: django_celery_beat_clockedschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_celery_beat_clockedschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_clockedschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_crontabschedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_crontabschedule (
    id integer NOT NULL,
    minute character varying(240) NOT NULL,
    hour character varying(96) NOT NULL,
    day_of_week character varying(64) NOT NULL,
    day_of_month character varying(124) NOT NULL,
    month_of_year character varying(64) NOT NULL,
    timezone character varying(63) NOT NULL
);


ALTER TABLE public.django_celery_beat_crontabschedule OWNER TO postgres;

--
-- Name: django_celery_beat_crontabschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_celery_beat_crontabschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_crontabschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_intervalschedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_intervalschedule (
    id integer NOT NULL,
    every integer NOT NULL,
    period character varying(24) NOT NULL
);


ALTER TABLE public.django_celery_beat_intervalschedule OWNER TO postgres;

--
-- Name: django_celery_beat_intervalschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_celery_beat_intervalschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_intervalschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_periodictask; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_periodictask (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    task character varying(200) NOT NULL,
    args text NOT NULL,
    kwargs text NOT NULL,
    queue character varying(200),
    exchange character varying(200),
    routing_key character varying(200),
    expires timestamp with time zone,
    enabled boolean NOT NULL,
    last_run_at timestamp with time zone,
    total_run_count integer NOT NULL,
    date_changed timestamp with time zone NOT NULL,
    description text NOT NULL,
    crontab_id integer,
    interval_id integer,
    solar_id integer,
    one_off boolean NOT NULL,
    start_time timestamp with time zone,
    priority integer,
    headers text NOT NULL,
    clocked_id integer,
    expire_seconds integer,
    CONSTRAINT django_celery_beat_periodictask_expire_seconds_check CHECK ((expire_seconds >= 0)),
    CONSTRAINT django_celery_beat_periodictask_priority_check CHECK ((priority >= 0)),
    CONSTRAINT django_celery_beat_periodictask_total_run_count_check CHECK ((total_run_count >= 0))
);


ALTER TABLE public.django_celery_beat_periodictask OWNER TO postgres;

--
-- Name: django_celery_beat_periodictask_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_celery_beat_periodictask ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_periodictask_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_celery_beat_periodictasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_periodictasks (
    ident smallint NOT NULL,
    last_update timestamp with time zone NOT NULL
);


ALTER TABLE public.django_celery_beat_periodictasks OWNER TO postgres;

--
-- Name: django_celery_beat_solarschedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_celery_beat_solarschedule (
    id integer NOT NULL,
    event character varying(24) NOT NULL,
    latitude numeric(9,6) NOT NULL,
    longitude numeric(9,6) NOT NULL
);


ALTER TABLE public.django_celery_beat_solarschedule OWNER TO postgres;

--
-- Name: django_celery_beat_solarschedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_celery_beat_solarschedule ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_celery_beat_solarschedule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: forms_field_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forms_field_type (
    id bigint NOT NULL,
    name character varying(50) NOT NULL,
    label character varying(100) NOT NULL,
    description text NOT NULL,
    category character varying(50) NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.forms_field_type OWNER TO postgres;

--
-- Name: forms_field_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.forms_field_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.forms_field_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: mediafiles_mediafile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mediafiles_mediafile (
    id uuid NOT NULL,
    file character varying(100) NOT NULL,
    original_name character varying(255) NOT NULL,
    file_type character varying(100) NOT NULL,
    file_size bigint NOT NULL,
    created_at timestamp with time zone NOT NULL,
    uploaded_by_id bigint
);


ALTER TABLE public.mediafiles_mediafile OWNER TO postgres;

--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_agricultural_field_validation_survey_v1_aaeb9c7b ALTER COLUMN id SET DEFAULT nextval('public.collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq'::regclass);


--
-- Name: collect_community_census_data_collection_v1_72f41e4f id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_community_census_data_collection_v1_72f41e4f ALTER COLUMN id SET DEFAULT nextval('public.collect_community_census_data_collection_v1_72f41e4f_id_seq'::regclass);


--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 ALTER COLUMN id SET DEFAULT nextval('public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq'::regclass);


--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e033286 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 ALTER COLUMN id SET DEFAULT nextval('public.collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq'::regclass);


--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 ALTER COLUMN id SET DEFAULT nextval('public.collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq'::regclass);


--
-- Name: collect_road_network_survey_v1_5bea3d58 id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_road_network_survey_v1_5bea3d58 ALTER COLUMN id SET DEFAULT nextval('public.collect_road_network_survey_v1_5bea3d58_id_seq'::regclass);


--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef056f id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_road_surface_quality_defect_assessment_v1_2cef056f ALTER COLUMN id SET DEFAULT nextval('public.collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq'::regclass);


--
-- Data for Name: accounts_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1	pbkdf2_sha256$720000$rSQTO64I2QMamzmU61i2i6$YM3bg32hznLvpka+K9ossV+hzHXd8Nh9nwjVj0oV3OE=	\N	f	zingsa_admin			admin@zingsa.test	f	t	2026-05-27 22:05:28.435863+00
\.


--
-- Data for Name: accounts_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: accounts_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auditlog_logentry; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auditlog_logentry (id, object_pk, object_id, object_repr, action, changes, "timestamp", actor_id, content_type_id, remote_addr, additional_data, serialized_data) FROM stdin;
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add crontab	6	add_crontabschedule
22	Can change crontab	6	change_crontabschedule
23	Can delete crontab	6	delete_crontabschedule
24	Can view crontab	6	view_crontabschedule
25	Can add interval	7	add_intervalschedule
26	Can change interval	7	change_intervalschedule
27	Can delete interval	7	delete_intervalschedule
28	Can view interval	7	view_intervalschedule
29	Can add periodic task	8	add_periodictask
30	Can change periodic task	8	change_periodictask
31	Can delete periodic task	8	delete_periodictask
32	Can view periodic task	8	view_periodictask
33	Can add periodic tasks	9	add_periodictasks
34	Can change periodic tasks	9	change_periodictasks
35	Can delete periodic tasks	9	delete_periodictasks
36	Can view periodic tasks	9	view_periodictasks
37	Can add solar event	10	add_solarschedule
38	Can change solar event	10	change_solarschedule
39	Can delete solar event	10	delete_solarschedule
40	Can view solar event	10	view_solarschedule
41	Can add clocked	11	add_clockedschedule
42	Can change clocked	11	change_clockedschedule
43	Can delete clocked	11	delete_clockedschedule
44	Can view clocked	11	view_clockedschedule
45	Can add log entry	12	add_logentry
46	Can change log entry	12	change_logentry
47	Can delete log entry	12	delete_logentry
48	Can view log entry	12	view_logentry
49	Can add user	13	add_user
50	Can change user	13	change_user
51	Can delete user	13	delete_user
52	Can view user	13	view_user
53	Can add organization	14	add_organization
54	Can change organization	14	change_organization
55	Can delete organization	14	delete_organization
56	Can view organization	14	view_organization
57	Can add project	15	add_project
58	Can change project	15	change_project
59	Can delete project	15	delete_project
60	Can view project	15	view_project
61	Can add form	16	add_form
62	Can change form	16	change_form
63	Can delete form	16	delete_form
64	Can view form	16	view_form
65	Can add form version	17	add_formversion
66	Can change form version	17	change_formversion
67	Can delete form version	17	delete_formversion
68	Can view form version	17	view_formversion
69	Can add submission index	18	add_submissionindex
70	Can change submission index	18	change_submissionindex
71	Can delete submission index	18	delete_submissionindex
72	Can view submission index	18	view_submissionindex
73	Can add submission media	19	add_submissionmedia
74	Can change submission media	19	change_submissionmedia
75	Can delete submission media	19	delete_submissionmedia
76	Can view submission media	19	view_submissionmedia
77	Can add sync log	20	add_synclog
78	Can change sync log	20	change_synclog
79	Can delete sync log	20	delete_synclog
80	Can view sync log	20	view_synclog
81	Can add organization member	21	add_organizationmember
82	Can change organization member	21	change_organizationmember
83	Can delete organization member	21	delete_organizationmember
84	Can view organization member	21	view_organizationmember
85	Can add project member	22	add_projectmember
86	Can change project member	22	change_projectmember
87	Can delete project member	22	delete_projectmember
88	Can view project member	22	view_projectmember
89	Can add Form Field Type	23	add_formfieldtype
90	Can change Form Field Type	23	change_formfieldtype
91	Can delete Form Field Type	23	delete_formfieldtype
92	Can view Form Field Type	23	view_formfieldtype
93	Can add media file	24	add_mediafile
94	Can change media file	24	change_mediafile
95	Can delete media file	24	delete_mediafile
96	Can view media file	24	view_mediafile
\.


--
-- Data for Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_agricultural_field_validation_survey_v1_aaeb9c7b (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, name, farmer, photos, croptype, pesttype, cropstage, fieldcode, irrigated, signature, pestdamage, voicenotes, damagenotes, affectedarea, pestseverity, fieldboundary, irrigationtype) FROM stdin;
\.


--
-- Data for Name: collect_community_census_data_collection_v1_72f41e4f; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_community_census_data_collection_v1_72f41e4f (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, notes, headname, housephoto, householdid, malemembers, watersource, dwellingtype, incomesource, roofmaterial, femalemembers, livestocktype, childrenunder5, lightingsource, livestockowned, toiletfacility, otherwatersource, electricityaccess, electricitysource, householdlocation, otherincomesource, opendefecationarea) FROM stdin;
\.


--
-- Data for Name: collect_form; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_form (id, title, slug, description, mode, geometry_type, status, submission_table_name, created_at, updated_at, created_by_id, project_id, current_version_id) FROM stdin;
72f41e4f-86e6-49bc-b251-276a1f82c30c	Community Census Data Collection	community-census-data-collection	Household and demographic data collection for community planning, infrastructure assessment, and development monitoring.	form_first	point	published	collect_community_census_data_collection_v1_72f41e4f	2026-05-27 22:08:51.851947+00	2026-05-27 22:08:52.32248+00	1	f7c0b8a5-d266-4da7-b077-75ab730cbf90	e783e3cd-71b5-4ed0-bb0f-6480eaf30e61
aaeb9c7b-90a1-489e-985f-274a75882659	Agricultural Field Validation Survey	agricultural-field-validation-survey	GIS field survey for mapping agricultural plots, validating crop types and assessing field conditions.	map_first	polygon	published	collect_agricultural_field_validation_survey_v1_aaeb9c7b	2026-05-27 22:08:52.388212+00	2026-05-27 22:08:52.552241+00	1	f7c0b8a5-d266-4da7-b077-75ab730cbf90	017c72f2-0ba0-4f8b-ae1b-967eb2f7477e
5bea3d58-b361-4d2a-95fa-55198832d4bf	Road Network Survey	road-network-survey	GIS field survey for mapping and assessing roads, access routes, and community pathways for maintenance, accessibility, and transport planning.	map_first	line	published	collect_road_network_survey_v1_5bea3d58	2026-05-27 22:08:52.664598+00	2026-05-27 22:08:52.831927+00	1	f7c0b8a5-d266-4da7-b077-75ab730cbf90	6738abc4-1ab5-430c-a7a0-3e1478649bf9
db3c56c9-801e-4153-a3fa-d09d1a6593f4	Illegal Mine Pit Inspection Survey	illegal-mine-pit-inspection-survey	GIS field survey for mapping and assessing illegal mining pits and associated environmental hazards.	map_first	point	published	collect_illegal_mine_pit_inspection_survey_v1_db3c56c9	2026-05-27 22:11:13.301851+00	2026-05-27 22:11:13.490733+00	1	0b3f4cd5-3632-4377-a117-7bc333935b66	b32d8a35-8ec1-4cce-8ad3-d062c12fb569
2cef056f-cbb5-4411-b4bf-7d7d5af0facb	Road Surface Quality & Defect Assessment	road-surface-quality-defect-assessment	Field assessment of paved and unpaved road segments for national highway maintenance planning. Captures pavement inventory, surface condition index (SCI), defect taxonomy, photographic evidence, and maintenance prioritisation along the surveyed alignment.	map_first	line	published	collect_road_surface_quality_defect_assessment_v1_2cef056f	2026-05-27 22:14:14.445975+00	2026-05-27 22:14:14.674697+00	1	b4a49c48-8079-4cb2-859a-b41a953903f3	1179d09a-ec6f-4534-85f0-2f924175d339
6e033286-bcb8-474d-8c84-c7bec56e53a0	Intersection Traffic & Pedestrian Audit	intersection-traffic-pedestrian-audit	Structured intersection audit for national transport corridor studies. Records peak-period vehicle and pedestrian volumes, heavy vehicle mix, crossing facilities, signal operations, and qualitative inspector notes at signalised and unsignalised junctions.	map_first	point	published	collect_intersection_traffic_pedestrian_audit_v1_6e033286	2026-05-27 22:14:14.741499+00	2026-05-27 22:14:14.909889+00	1	b4a49c48-8079-4cb2-859a-b41a953903f3	c31c996d-2e71-479a-b66d-f3675e82d55b
57abe1a1-a564-4576-bdf8-8a3c964d350d	Public Transit Stop Infrastructure Audit	public-transit-stop-infrastructure-audit	Infrastructure condition survey for public transport stops along national and urban corridors. Documents shelter, accessibility, lighting, signage, and passenger amenity standards for bus, BRT, and light-rail interfaces.	form_first	point	published	collect_public_transit_stop_infrastructure_audit_v1_57abe1a1	2026-05-27 22:14:14.981745+00	2026-05-27 22:14:15.130797+00	1	b4a49c48-8079-4cb2-859a-b41a953903f3	dd297970-956d-47be-b42f-4d9bf4c4f97d
\.


--
-- Data for Name: collect_form_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_form_version (id, version_number, version_label, schema, checksum, is_published, physical_table_name, column_mapping, published_at, created_at, created_by_id, form_id) FROM stdin;
e783e3cd-71b5-4ed0-bb0f-6480eaf30e61	1	1.0	{"id": "census_data_collection", "mode": "form_first", "title": "Community Census Data Collection", "formId": "community_census_form", "version": "1.0", "category": "demographics", "createdBy": {"name": "ZINGSA", "email": "info@zingsa.org"}, "projectId": "ZINGSA-COMMUNITY-MAPPING-001", "questions": [{"id": "householdLocation", "hint": "Capture GPS location of the household", "type": "location", "label": "Household Location", "required": true}, {"id": "householdId", "hint": "Enter unique household identifier", "type": "text", "label": "Household ID", "required": true, "maxLength": 20, "minLength": 3}, {"id": "headName", "hint": "Enter the full name of the household head", "type": "text", "label": "Head of Household Name", "required": true, "maxLength": 100, "minLength": 3}, {"id": "maleMembers", "max": 30, "min": 0, "hint": "Enter total number of males in the household", "type": "number", "label": "Male Members", "required": true}, {"id": "femaleMembers", "max": 30, "min": 0, "hint": "Enter total number of females in the household", "type": "number", "label": "Female Members", "required": true}, {"id": "childrenUnder5", "max": 20, "min": 0, "hint": "Enter number of children younger than five years", "type": "number", "label": "Children Under 5 Years", "required": true}, {"id": "dwellingType", "hint": "Select the type of household dwelling", "type": "radio", "label": "Dwelling Type", "options": [{"label": "House", "value": "house"}, {"label": "Traditional Hut", "value": "hut"}, {"label": "Apartment", "value": "apartment"}, {"label": "Temporary Shelter", "value": "temporary"}], "required": true}, {"id": "roofMaterial", "hint": "Select the primary roofing material", "type": "radio", "label": "Roof Material", "options": [{"label": "Iron Sheets", "value": "iron"}, {"label": "Thatch", "value": "thatch"}, {"label": "Tiles", "value": "tiles"}, {"label": "Asbestos", "value": "asbestos"}], "required": true}, {"id": "waterSource", "hint": "Select the household’s main source of water", "type": "checkbox", "label": "Main Water Source", "options": [{"label": "Tap Water", "value": "tap"}, {"label": "Borehole", "value": "borehole"}, {"label": "Well", "value": "well"}, {"label": "River", "value": "river"}, {"label": "Other", "value": "other"}], "required": true}, {"id": "otherWaterSource", "hint": "Specify the water source used", "type": "text", "label": "Specify Water Source", "required": true, "condition": {"field": "waterSource", "value": "other", "operator": "equals"}}, {"id": "electricityAccess", "hint": "Does the household have access to electricity?", "type": "radio", "label": "Electricity Access", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "electricitySource", "hint": "Select source of electricity", "type": "radio", "label": "Electricity Source", "options": [{"label": "National Grid", "value": "grid"}, {"label": "Solar", "value": "solar"}, {"label": "Generator", "value": "generator"}], "required": true, "condition": {"field": "electricityAccess", "value": "yes", "operator": "equals"}}, {"id": "lightingSource", "hint": "Select lighting sources used when electricity is unavailable", "type": "checkbox", "label": "Alternative Lighting Source", "options": [{"label": "Candles", "value": "candles"}, {"label": "Paraffin Lamp", "value": "paraffin"}, {"label": "Solar Lamp", "value": "solar_lamp"}, {"label": "Firewood", "value": "firewood"}], "required": false, "condition": {"field": "electricityAccess", "value": "no", "operator": "equals"}}, {"id": "toiletFacility", "hint": "Select the main sanitation facility used", "type": "radio", "label": "Toilet Facility", "options": [{"label": "Flush Toilet", "value": "flush"}, {"label": "Pit Latrine", "value": "pit"}, {"label": "No Facility", "value": "none"}], "required": true}, {"id": "openDefecationArea", "hint": "Describe the area commonly used", "type": "text", "label": "Open Defecation Area", "required": true, "condition": {"field": "toiletFacility", "value": "none", "operator": "equals"}}, {"id": "incomeSource", "hint": "Select all applicable household income sources", "type": "checkbox", "label": "Main Sources of Income", "options": [{"label": "Farming", "value": "farming"}, {"label": "Employment", "value": "employment"}, {"label": "Business", "value": "business"}, {"label": "Livestock", "value": "livestock"}, {"label": "Other", "value": "other"}], "required": true}, {"id": "otherIncomeSource", "hint": "Specify additional source of income", "type": "text", "label": "Specify Income Source", "required": true, "condition": {"field": "incomeSource", "value": "other", "operator": "contains"}}, {"id": "livestockOwned", "hint": "Does the household own livestock?", "type": "radio", "label": "Own Livestock", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "livestockType", "hint": "Select livestock owned", "type": "checkbox", "label": "Livestock Type", "options": [{"label": "Cattle", "value": "cattle"}, {"label": "Goats", "value": "goats"}, {"label": "Sheep", "value": "sheep"}, {"label": "Chickens", "value": "chickens"}], "required": false, "condition": {"field": "livestockOwned", "value": "yes", "operator": "equals"}}, {"id": "housePhoto", "hint": "Take a photo showing the household structure", "type": "image", "label": "Household Photo", "maxFiles": 3, "required": false}, {"id": "notes", "hint": "Record additional observations about the household", "type": "textarea", "label": "Additional Notes", "required": false, "maxLength": 500, "minLength": 10}], "createdDate": "2026-05-27T10:30:00Z", "description": "Household and demographic data collection for community planning, infrastructure assessment, and development monitoring.", "geometryType": "point"}	ab955927857f729f20a9befc52beee1c947c131f2f976914b5af62999f237fab	t	collect_community_census_data_collection_v1_72f41e4f	{"notes": "notes", "headName": "headname", "housePhoto": "housephoto", "householdId": "householdid", "maleMembers": "malemembers", "waterSource": "watersource", "dwellingType": "dwellingtype", "incomeSource": "incomesource", "roofMaterial": "roofmaterial", "femaleMembers": "femalemembers", "livestockType": "livestocktype", "childrenUnder5": "childrenunder5", "lightingSource": "lightingsource", "livestockOwned": "livestockowned", "toiletFacility": "toiletfacility", "otherWaterSource": "otherwatersource", "electricityAccess": "electricityaccess", "electricitySource": "electricitysource", "householdLocation": "householdlocation", "otherIncomeSource": "otherincomesource", "openDefecationArea": "opendefecationarea"}	2026-05-27 22:08:51.946889+00	2026-05-27 22:08:51.863023+00	1	72f41e4f-86e6-49bc-b251-276a1f82c30c
017c72f2-0ba0-4f8b-ae1b-967eb2f7477e	1	1.0	{"id": "crop_field_survey_001", "mode": "map_first", "title": "Agricultural Field Validation Survey", "formId": "crop_field_survey_001", "version": "1.0", "category": "agriculture", "createdBy": {"name": "ZINGSA", "email": "info@zingsa.org"}, "projectId": "ZINGSA-COMMUNITY-MAPPING-001", "questions": [{"id": "name", "hint": "Enter name of farm", "type": "text", "label": "Farm Name"}, {"id": "farmer", "hint": "Enter farmer name", "type": "text", "label": "Farmer Name"}, {"id": "fieldBoundary", "hint": "Map the agricultural field boundary by walking around the field or drawing on map.", "type": "polygon", "label": "Field Boundary", "required": true}, {"id": "fieldCode", "hint": "Enter unique field identifier (example: FLD-001).", "type": "text", "label": "Field ID", "required": true, "maxLength": 20, "minLength": 3}, {"id": "cropType", "hint": "Select dominant crop cultivated in this field.", "type": "radio", "label": "Primary Crop", "options": [{"label": "Maize", "value": "maize"}, {"label": "Wheat", "value": "wheat"}, {"label": "Soybean", "value": "soybean"}, {"label": "Cotton", "value": "cotton"}, {"label": "Tobacco", "value": "tobacco"}, {"label": "Mixed Crops", "value": "mixed"}], "required": true}, {"id": "cropStage", "hint": "Select current crop development stage.", "type": "radio", "label": "Crop Growth Stage", "options": [{"label": "Land Preparation", "value": "land_preparation"}, {"label": "Planting", "value": "planting"}, {"label": "Vegetative", "value": "vegetative"}, {"label": "Flowering", "value": "flowering"}, {"label": "Maturity", "value": "maturity"}, {"label": "Harvested", "value": "harvested"}], "required": true}, {"id": "irrigated", "hint": "Does the field have irrigation support?", "type": "radio", "label": "Irrigation Available", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "irrigationType", "hint": "Select irrigation methods used in this field.", "type": "checkbox", "label": "Irrigation Type", "options": [{"label": "Drip Irrigation", "value": "drip"}, {"label": "Sprinkler", "value": "sprinkler"}, {"label": "Flood Irrigation", "value": "flood"}, {"label": "Furrow Irrigation", "value": "furrow"}, {"label": "Other", "value": "other"}], "required": false, "condition": {"field": "irrigated", "value": "yes", "operator": "equals"}, "maxSelections": 4, "minSelections": 1}, {"id": "pestDamage", "hint": "Is there visible pest or disease damage?", "type": "radio", "label": "Pest Damage Observed", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "pestType", "hint": "Select observed pests or crop threats.", "type": "checkbox", "label": "Pest Type", "options": [{"label": "Armyworm", "value": "armyworm"}, {"label": "Aphids", "value": "aphids"}, {"label": "Locust", "value": "locust"}, {"label": "Stem Borer", "value": "stem_borer"}, {"label": "Fungal Disease", "value": "fungal"}, {"label": "Other", "value": "other"}], "required": false, "condition": {"field": "pestDamage", "value": "yes", "operator": "equals"}, "maxSelections": 5, "minSelections": 1}, {"id": "pestSeverity", "hint": "Estimate crop damage severity.", "type": "radio", "label": "Pest Severity", "options": [{"label": "Low", "value": "low"}, {"label": "Moderate", "value": "moderate"}, {"label": "High", "value": "high"}, {"label": "Severe", "value": "severe"}], "required": false, "condition": {"field": "pestDamage", "value": "yes", "operator": "equals"}}, {"id": "affectedArea", "max": 100, "min": 1, "hint": "Estimate percentage of field affected.", "type": "number", "label": "Affected Area (%)", "required": false, "condition": {"field": "pestDamage", "value": "yes", "operator": "equals"}}, {"id": "damageNotes", "hint": "Describe observed pest impacts.", "type": "textarea", "label": "Damage Notes", "required": false, "condition": {"field": "pestDamage", "value": "yes", "operator": "equals"}}, {"id": "photos", "hint": "Capture crop and field overview photos.", "type": "image", "label": "Field Photos", "maxFiles": 5}, {"id": "voiceNotes", "hint": "Record field observations.", "type": "voice", "label": "Voice Notes"}, {"id": "signature", "hint": "Sign to confirm field validation.", "type": "signature", "label": "Survey Signature", "required": true}], "createdDate": "2026-05-27T12:00:00Z", "description": "GIS field survey for mapping agricultural plots, validating crop types and assessing field conditions.", "geometryType": "polygon"}	14447b6652e2a2227e1463743a4118434bd607e15f16c65b9e733d2ee85b7295	t	collect_agricultural_field_validation_survey_v1_aaeb9c7b	{"name": "name", "farmer": "farmer", "photos": "photos", "cropType": "croptype", "pestType": "pesttype", "cropStage": "cropstage", "fieldCode": "fieldcode", "irrigated": "irrigated", "signature": "signature", "pestDamage": "pestdamage", "voiceNotes": "voicenotes", "damageNotes": "damagenotes", "affectedArea": "affectedarea", "pestSeverity": "pestseverity", "fieldBoundary": "fieldboundary", "irrigationType": "irrigationtype"}	2026-05-27 22:08:52.465818+00	2026-05-27 22:08:52.390423+00	1	aaeb9c7b-90a1-489e-985f-274a75882659
6738abc4-1ab5-430c-a7a0-3e1478649bf9	1	1.0	{"id": "road_network_survey_001", "mode": "map_first", "title": "Road Network Survey", "formId": "road_network_survey_001", "version": "1.0", "category": "infrastructure", "createdBy": {"name": "ZINGSA", "email": "info@zingsa.org"}, "projectId": "ZINGSA-COMMUNITY-MAPPING-001", "questions": [{"id": "roadName", "hint": "Enter the official or commonly known road/path name.", "type": "text", "label": "Road/Path Name", "required": true, "maxLength": 100, "minLength": 2}, {"id": "roadType", "hint": "Select the classification of the road or path.", "type": "radio", "label": "Road Type", "options": [{"label": "Service Road", "value": "service"}, {"label": "Access Road", "value": "access"}, {"label": "Bicycle Path", "value": "bicycle"}, {"label": "Pedestrian Path", "value": "pedestrian"}, {"label": "Emergency Route", "value": "emergency"}, {"label": "Highway", "value": "highway"}, {"label": "Residential Road", "value": "residential"}, {"label": "Other", "value": "other"}], "required": true}, {"id": "surfaceType", "hint": "Select the dominant road surface material.", "type": "radio", "label": "Surface Type", "options": [{"label": "Asphalt", "value": "asphalt"}, {"label": "Gravel", "value": "gravel"}, {"label": "Dirt", "value": "dirt"}, {"label": "Concrete", "value": "concrete"}, {"label": "Rocky", "value": "rocky"}, {"label": "Mixed Surface", "value": "mixed"}, {"label": "Other", "value": "other"}], "required": true}, {"id": "roadWidth", "max": 100, "min": 1, "hint": "Estimate average width of the road in meters.", "type": "number", "label": "Average Road Width (m)", "required": false}, {"id": "roadCondition", "hint": "Assess the overall condition of the road.", "type": "radio", "label": "Road Condition", "options": [{"label": "Excellent", "value": "excellent"}, {"label": "Good", "value": "good"}, {"label": "Fair", "value": "fair"}, {"label": "Poor", "value": "poor"}, {"label": "Impassable", "value": "impassable"}], "required": true}, {"id": "conditionIssues", "hint": "Select observed road defects or issues.", "type": "checkbox", "label": "Observed Road Issues", "options": [{"label": "Potholes", "value": "potholes"}, {"label": "Erosion", "value": "erosion"}, {"label": "Drainage Failure", "value": "drainage_failure"}, {"label": "Surface Cracking", "value": "cracking"}, {"label": "Vegetation Overgrowth", "value": "overgrown"}, {"label": "Flooding", "value": "flooding"}, {"label": "Bridge Damage", "value": "bridge_damage"}, {"label": "Other", "value": "other"}], "required": false, "maxSelections": 8, "minSelections": 1}, {"id": "trafficVolume", "hint": "Estimate average traffic usage.", "type": "radio", "label": "Traffic Volume", "options": [{"label": "Low", "value": "low"}, {"label": "Moderate", "value": "moderate"}, {"label": "High", "value": "high"}, {"label": "Very High", "value": "very_high"}], "required": false}, {"id": "accessibility", "hint": "Assess ease of access along the road.", "type": "radio", "label": "Accessibility", "options": [{"label": "Easy Access", "value": "easy"}, {"label": "Moderate Access", "value": "moderate"}, {"label": "Difficult Access", "value": "difficult"}, {"label": "Restricted Access", "value": "restricted"}], "required": true}, {"id": "maintenanceRequired", "hint": "Select required maintenance interventions.", "type": "checkbox", "label": "Maintenance Required", "options": [{"label": "Road Grading", "value": "grading"}, {"label": "Drainage Repair", "value": "drainage"}, {"label": "Resurfacing", "value": "resurfacing"}, {"label": "Bridge Repair", "value": "bridge_repair"}, {"label": "Vegetation Clearing", "value": "vegetation_clearing"}, {"label": "Road Signage", "value": "signage"}], "required": false, "maxSelections": 6, "minSelections": 1}, {"id": "roadPhotos", "hint": "Capture photos showing road condition and features.", "type": "image", "label": "Road Photos", "maxFiles": 8, "required": false}, {"id": "inspectionNotes", "hint": "Enter additional observations or recommendations.", "type": "textarea", "label": "Inspection Notes", "required": false, "maxLength": 2000, "minLength": 10}, {"id": "surveyDate", "hint": "Select survey date.", "type": "date", "label": "Survey Date", "required": true}, {"id": "digitalSignature", "hint": "Sign to confirm survey completion and accuracy.", "type": "signature", "label": "Digital Signature", "required": true}, {"id": "geom", "type": "line", "label": "Geometry Feature", "required": false}], "createdDate": "2026-05-27T10:00:00Z", "description": "GIS field survey for mapping and assessing roads, access routes, and community pathways for maintenance, accessibility, and transport planning.", "geometryType": "line"}	385d130006152e2387302e7a39def2f81ab0af9b7ec0ec8a603488dba9ba0a82	t	collect_road_network_survey_v1_5bea3d58	{"geom": "geom", "roadName": "roadname", "roadType": "roadtype", "roadWidth": "roadwidth", "roadPhotos": "roadphotos", "surveyDate": "surveydate", "surfaceType": "surfacetype", "accessibility": "accessibility", "roadCondition": "roadcondition", "trafficVolume": "trafficvolume", "conditionIssues": "conditionissues", "inspectionNotes": "inspectionnotes", "digitalSignature": "digitalsignature", "maintenanceRequired": "maintenancerequired"}	2026-05-27 22:08:52.739343+00	2026-05-27 22:08:52.667994+00	1	5bea3d58-b361-4d2a-95fa-55198832d4bf
b32d8a35-8ec1-4cce-8ad3-d062c12fb569	1	1.0	{"id": "illegal_mine_pits_001", "mode": "map_first", "title": "Illegal Mine Pit Inspection Survey", "formId": "illegal_mine_pits_001", "version": "1.0", "category": "environment", "createdBy": {"name": "ZINGSA", "email": "info@zingsa.org"}, "projectId": "ZINGSA-COMMUNITY-MAPPING-001", "questions": [{"id": "mineralType", "hint": "Select the primary mineral associated with this mine pit.", "type": "radio", "label": "Mineral Being Extracted", "options": [{"label": "Gold", "value": "gold"}, {"label": "Diamond", "value": "diamond"}, {"label": "Chrome", "value": "chrome"}, {"label": "Coal", "value": "coal"}, {"label": "Lithium", "value": "lithium"}, {"label": "Other", "value": "other"}], "required": true}, {"id": "pitStatus", "hint": "Select the operational status of the mine pit.", "type": "radio", "label": "Mine Pit Status", "options": [{"label": "Active", "value": "active"}, {"label": "Abandoned", "value": "abandoned"}, {"label": "Partially Active", "value": "partially_active"}, {"label": "Rehabilitated", "value": "rehabilitated"}], "required": true}, {"id": "pitDepth", "max": 500, "min": 1, "hint": "Estimate the depth of the mine pit in meters.", "type": "number", "label": "Estimated Pit Depth (m)", "required": true}, {"id": "pitDiameter", "max": 1000, "min": 1, "hint": "Estimate the width or diameter of the mine pit.", "type": "number", "label": "Estimated Pit Diameter (m)", "required": true}, {"id": "waterFilled", "hint": "Is the pit filled with water?", "type": "radio", "label": "Water Filled", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "waterColor", "hint": "Select observed water color.", "type": "radio", "label": "Water Color", "options": [{"label": "Clear", "value": "clear"}, {"label": "Brown", "value": "brown"}, {"label": "Green", "value": "green"}, {"label": "Black", "value": "black"}, {"label": "Other", "value": "other"}], "required": false, "condition": {"field": "waterFilled", "value": "yes", "operator": "equals"}}, {"id": "hazardsObserved", "hint": "Select all hazards observed at the site.", "type": "checkbox", "label": "Hazards Observed", "options": [{"label": "Open Pit", "value": "open_pit"}, {"label": "Unstable Pit Walls", "value": "unstable_walls"}, {"label": "Water Contamination", "value": "water_contamination"}, {"label": "Chemical Exposure", "value": "chemical_exposure"}, {"label": "Accessible to Children", "value": "child_access"}, {"label": "Livestock Risk", "value": "livestock_risk"}, {"label": "Other", "value": "other"}], "required": false, "maxSelections": 6, "minSelections": 1}, {"id": "environmentalDamage", "hint": "Select observed environmental impacts.", "type": "checkbox", "label": "Environmental Damage", "options": [{"label": "Deforestation", "value": "deforestation"}, {"label": "Soil Erosion", "value": "soil_erosion"}, {"label": "River Siltation", "value": "river_siltation"}, {"label": "Water Pollution", "value": "water_pollution"}, {"label": "Land Degradation", "value": "land_degradation"}], "required": false, "maxSelections": 5, "minSelections": 1}, {"id": "equipmentObserved", "hint": "Select equipment observed at the site.", "type": "checkbox", "label": "Mining Equipment Observed", "options": [{"label": "Excavator", "value": "excavator"}, {"label": "Water Pump", "value": "water_pump"}, {"label": "Crusher", "value": "crusher"}, {"label": "Generator", "value": "generator"}, {"label": "Sluice Box", "value": "sluice_box"}, {"label": "Manual Tools", "value": "manual_tools"}], "required": false, "maxSelections": 6, "minSelections": 1}, {"id": "estimatedWorkers", "max": 500, "min": 1, "hint": "Estimate the number of people working at the site.", "type": "number", "label": "Estimated Number of Workers", "required": false}, {"id": "childrenObserved", "hint": "Were children observed working or present at the site?", "type": "radio", "label": "Children Observed at Site", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "siteAccessibility", "hint": "Assess how accessible the site is.", "type": "radio", "label": "Site Accessibility", "options": [{"label": "Easy Access", "value": "easy"}, {"label": "Moderate Access", "value": "moderate"}, {"label": "Difficult Access", "value": "difficult"}, {"label": "Restricted Access", "value": "restricted"}], "required": true}, {"id": "rehabilitationNeeded", "hint": "Does this site require environmental rehabilitation?", "type": "radio", "label": "Rehabilitation Required", "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}], "required": true}, {"id": "recommendedAction", "hint": "Select recommended interventions.", "type": "checkbox", "label": "Recommended Actions", "options": [{"label": "Site Closure", "value": "site_closure"}, {"label": "Fencing", "value": "fencing"}, {"label": "Backfilling", "value": "backfilling"}, {"label": "Law Enforcement Action", "value": "law_enforcement"}, {"label": "Community Awareness", "value": "community_awareness"}, {"label": "Water Quality Testing", "value": "water_testing"}], "required": false, "maxSelections": 6, "minSelections": 1}, {"id": "sitePhotos", "hint": "Capture photos of the mine pit and surrounding environment.", "type": "image", "label": "Mine Pit Photos", "maxFiles": 8, "required": false}, {"id": "inspectionNotes", "hint": "Enter additional observations or comments.", "type": "textarea", "label": "Inspection Notes", "required": false, "maxLength": 2000, "minLength": 10}, {"id": "inspectionDate", "hint": "Select inspection date.", "type": "date", "label": "Inspection Date", "required": true}, {"id": "geom", "type": "point", "label": "Geometry Feature", "required": false}], "createdDate": "2026-05-27T12:00:00Z", "description": "GIS field survey for mapping and assessing illegal mining pits and associated environmental hazards.", "geometryType": "point"}	8fac5e63b595bff189ae5e125487b1c080c0b889a52055f2db2c17ac8e929a0c	t	collect_illegal_mine_pit_inspection_survey_v1_db3c56c9	{"geom": "geom", "pitDepth": "pitdepth", "pitStatus": "pitstatus", "sitePhotos": "sitephotos", "waterColor": "watercolor", "mineralType": "mineraltype", "pitDiameter": "pitdiameter", "waterFilled": "waterfilled", "inspectionDate": "inspectiondate", "hazardsObserved": "hazardsobserved", "inspectionNotes": "inspectionnotes", "childrenObserved": "childrenobserved", "estimatedWorkers": "estimatedworkers", "equipmentObserved": "equipmentobserved", "recommendedAction": "recommendedaction", "siteAccessibility": "siteaccessibility", "environmentalDamage": "environmentaldamage", "rehabilitationNeeded": "rehabilitationneeded"}	2026-05-27 22:11:13.378588+00	2026-05-27 22:11:13.308006+00	1	db3c56c9-801e-4153-a3fa-d09d1a6593f4
1179d09a-ec6f-4534-85f0-2f924175d339	1	1.0	{"id": "transport_road_surface_quality_v1", "mode": "map_first", "title": "Road Surface Quality & Defect Assessment", "formId": "transport_road_surface_quality_v1", "version": "1.0", "category": "transport", "createdBy": {"name": "ZINGSA Transport Division", "email": "transport@zingsa.org"}, "projectId": "PROJ-C104EF", "questions": [{"id": "assessed_segment", "hint": "Trace the centreline of the road segment being assessed, from chainage start to end.", "type": "line", "label": "Assessed Road Segment", "required": true}, {"id": "road_segment_id", "hint": "Official segment identifier from the highway asset register (e.g. A4-KM12.4-NB).", "type": "text", "label": "Road Segment ID", "required": true, "maxLength": 64, "minLength": 3, "placeholder": "e.g. A4-KM12.4-NB"}, {"id": "highway_designation", "hint": "National route number or local road name.", "type": "text", "label": "Highway / Route Designation", "required": true, "maxLength": 120, "placeholder": "e.g. A4 Harare–Mutare Highway"}, {"id": "chainage_start_km", "max": 9999, "min": 0, "hint": "Kilometre post at the start of the assessed segment.", "type": "number", "label": "Chainage Start (km)", "required": true, "numericType": "decimal"}, {"id": "chainage_end_km", "max": 9999, "min": 0, "hint": "Kilometre post at the end of the assessed segment.", "type": "number", "label": "Chainage End (km)", "required": true, "numericType": "decimal"}, {"id": "segment_length_m", "max": 50000, "min": 1, "hint": "Measured or GIS-derived length of the assessed segment.", "type": "number", "label": "Segment Length (m)", "required": false, "numericType": "integer"}, {"id": "pavement_type", "hint": "Dominant structural pavement layer at the surface.", "type": "dropdown", "label": "Pavement Type", "options": [{"label": "Asphalt", "value": "asphalt"}, {"label": "Concrete", "value": "concrete"}, {"label": "Gravel", "value": "gravel"}, {"label": "Unpaved", "value": "unpaved"}], "required": true}, {"id": "carriageway_lanes", "max": 8, "min": 1, "hint": "Total lanes in the assessed direction(s) of travel.", "type": "number", "label": "Number of Lanes", "required": false, "numericType": "integer"}, {"id": "surface_condition_index", "max": 10, "min": 1, "hint": "1 = failed pavement, 10 = excellent. Use national SCI guidance.", "type": "number", "label": "Surface Condition Index (1–10)", "required": true, "numericType": "integer"}, {"id": "primary_defect_type", "hint": "Most severe or extensive defect observed along the segment.", "type": "dropdown", "label": "Primary Defect Type", "options": [{"label": "Potholes", "value": "potholes"}, {"label": "Cracking", "value": "cracking"}, {"label": "Rutting", "value": "rutting"}, {"label": "None", "value": "none"}], "required": true}, {"id": "defect_severity", "hint": "Severity rating for the primary defect type.", "type": "dropdown", "label": "Defect Severity", "options": [{"label": "Minor — cosmetic / early stage", "value": "minor"}, {"label": "Moderate — functional impact emerging", "value": "moderate"}, {"label": "Severe — safety or structural concern", "value": "severe"}, {"label": "Critical — immediate intervention required", "value": "critical"}], "required": true}, {"id": "defect_extent_percent", "max": 100, "min": 0, "hint": "Approximate percentage of segment length affected by the primary defect.", "type": "number", "label": "Defect Extent (% of segment)", "required": false, "numericType": "integer"}, {"id": "defect_photo", "hint": "Capture clear photos of the worst defect location; include scale reference where possible.", "type": "image", "label": "Defect Photograph", "required": true, "maxPhotos": 3}, {"id": "drainage_condition", "type": "dropdown", "label": "Side Drain / Shoulder Drainage", "options": [{"label": "Adequate", "value": "adequate"}, {"label": "Partially Blocked", "value": "partially_blocked"}, {"label": "Blocked", "value": "blocked"}, {"label": "Not Present", "value": "not_present"}], "required": false}, {"id": "maintenance_urgency", "hint": "Recommended response timeframe for maintenance programming.", "type": "dropdown", "label": "Maintenance Urgency", "options": [{"label": "Low — routine cycle", "value": "low"}, {"label": "Medium — schedule within 12 months", "value": "medium"}, {"label": "High — schedule within 90 days", "value": "high"}, {"label": "Critical — emergency works", "value": "critical"}], "required": true}, {"id": "inspector_remarks", "type": "textarea", "label": "Inspector Remarks", "required": false, "maxLength": 2000, "minLength": 0, "placeholder": "Additional observations, detour recommendations, or coordination notes."}], "createdDate": "2026-05-27T22:14:14Z", "description": "Field assessment of paved and unpaved road segments for national highway maintenance planning. Captures pavement inventory, surface condition index (SCI), defect taxonomy, photographic evidence, and maintenance prioritisation along the surveyed alignment.", "geometryType": "line"}	0a4f5c8b83e918c08037db6520832c7ab806fd50288d47e680c6656a57b8ba32	t	collect_road_surface_quality_defect_assessment_v1_2cef056f	{"defect_photo": "defect_photo", "pavement_type": "pavement_type", "chainage_end_km": "chainage_end_km", "defect_severity": "defect_severity", "road_segment_id": "road_segment_id", "assessed_segment": "assessed_segment", "segment_length_m": "segment_length_m", "carriageway_lanes": "carriageway_lanes", "chainage_start_km": "chainage_start_km", "inspector_remarks": "inspector_remarks", "drainage_condition": "drainage_condition", "highway_designation": "highway_designation", "maintenance_urgency": "maintenance_urgency", "primary_defect_type": "primary_defect_type", "defect_extent_percent": "defect_extent_percent", "surface_condition_index": "surface_condition_index"}	2026-05-27 22:14:14.548921+00	2026-05-27 22:14:14.451752+00	1	2cef056f-cbb5-4411-b4bf-7d7d5af0facb
c31c996d-2e71-479a-b66d-f3675e82d55b	1	1.0	{"id": "transport_intersection_traffic_v1", "mode": "map_first", "title": "Intersection Traffic & Pedestrian Audit", "formId": "transport_intersection_traffic_v1", "version": "1.0", "category": "transport", "createdBy": {"name": "ZINGSA Transport Division", "email": "transport@zingsa.org"}, "projectId": "PROJ-C104EF", "questions": [{"id": "intersection_location", "hint": "Stand at the approximate centre of the junction and capture the point.", "type": "location", "label": "Intersection GPS Location", "required": true}, {"id": "intersection_name", "hint": "Official or commonly used junction name.", "type": "text", "label": "Intersection Name", "required": true, "maxLength": 150, "minLength": 3, "placeholder": "e.g. Samora Machel & Leopold Takawira"}, {"id": "junction_type", "type": "dropdown", "label": "Junction Type", "options": [{"label": "Signalised", "value": "signalised"}, {"label": "Roundabout", "value": "roundabout"}, {"label": "Priority (give-way)", "value": "priority"}, {"label": "Uncontrolled", "value": "uncontrolled"}], "required": true}, {"id": "audit_date", "type": "date", "label": "Audit Date", "required": true}, {"id": "audit_time_period", "hint": "Peak period during which counts were conducted.", "type": "dropdown", "label": "Audit Time Period", "options": [{"label": "Morning Peak", "value": "morning_peak"}, {"label": "Midday", "value": "midday"}, {"label": "Evening Peak", "value": "evening_peak"}, {"label": "Night", "value": "night"}], "required": true}, {"id": "count_duration_minutes", "max": 180, "min": 15, "hint": "Standard count window (typically 60 or 120 minutes).", "type": "number", "label": "Count Duration (minutes)", "required": true, "numericType": "integer"}, {"id": "vehicle_volume_per_hour", "max": 50000, "min": 0, "hint": "Total all-direction vehicle flow extrapolated to hourly rate.", "type": "number", "label": "Vehicle Volume (vehicles/hour)", "required": true, "numericType": "integer"}, {"id": "heavy_vehicles_percentage", "max": 100, "min": 0, "hint": "Percentage of trucks, buses, and articulated vehicles in the count.", "type": "number", "label": "Heavy Vehicles (%)", "required": true, "numericType": "decimal"}, {"id": "pedestrian_crossings_available", "hint": "True if marked crossings, refuge islands, or signalised pedestrian stages exist.", "type": "boolean", "label": "Formal Pedestrian Crossings Available", "required": true}, {"id": "pedestrian_volume_per_hour", "max": 20000, "min": 0, "type": "number", "label": "Pedestrian Volume (pedestrians/hour)", "required": true, "numericType": "integer"}, {"id": "cyclist_volume_per_hour", "max": 5000, "min": 0, "type": "number", "label": "Cyclist Volume (cycles/hour)", "required": false, "numericType": "integer"}, {"id": "traffic_light_functional", "hint": "False if signals are flashing, off, or vandalised. N/A if unsignalised — select True.", "type": "boolean", "label": "Traffic Signals Functional", "required": true}, {"id": "signal_cycle_observed", "max": 300, "min": 30, "type": "number", "label": "Observed Signal Cycle Length (seconds)", "required": false, "numericType": "integer"}, {"id": "conflict_observations", "hint": "Select all conflict types witnessed during the count period.", "type": "checkbox", "label": "Observed Conflict Types", "options": [{"label": "Vehicle–Pedestrian", "value": "vehicle_pedestrian"}, {"label": "Vehicle–Vehicle", "value": "vehicle_vehicle"}, {"label": "Vehicle–Cyclist", "value": "vehicle_cyclist"}, {"label": "None Observed", "value": "none"}], "required": false}, {"id": "inspector_audio_notes", "hint": "Record operational observations, near-misses, or signal timing issues.", "type": "voice", "label": "Inspector Audio Notes", "required": false}, {"id": "audit_summary", "type": "textarea", "label": "Audit Summary", "required": false, "maxLength": 1500, "placeholder": "Capacity assessment, recommended improvements, and coordination requirements."}], "createdDate": "2026-05-27T22:14:14Z", "description": "Structured intersection audit for national transport corridor studies. Records peak-period vehicle and pedestrian volumes, heavy vehicle mix, crossing facilities, signal operations, and qualitative inspector notes at signalised and unsignalised junctions.", "geometryType": "point"}	d3f460f1561b3d739684839f85d2da44b243ed6f03969872bfde873676b3868f	t	collect_intersection_traffic_pedestrian_audit_v1_6e033286	{"audit_date": "audit_date", "audit_summary": "audit_summary", "junction_type": "junction_type", "audit_time_period": "audit_time_period", "intersection_name": "intersection_name", "conflict_observations": "conflict_observations", "inspector_audio_notes": "inspector_audio_notes", "intersection_location": "intersection_location", "signal_cycle_observed": "signal_cycle_observed", "count_duration_minutes": "count_duration_minutes", "cyclist_volume_per_hour": "cyclist_volume_per_hour", "vehicle_volume_per_hour": "vehicle_volume_per_hour", "traffic_light_functional": "traffic_light_functional", "heavy_vehicles_percentage": "heavy_vehicles_percentage", "pedestrian_volume_per_hour": "pedestrian_volume_per_hour", "pedestrian_crossings_available": "pedestrian_crossings_available"}	2026-05-27 22:14:14.820259+00	2026-05-27 22:14:14.744615+00	1	6e033286-bcb8-474d-8c84-c7bec56e53a0
dd297970-956d-47be-b42f-4d9bf4c4f97d	1	1.0	{"id": "transport_transit_stop_audit_v1", "mode": "form_first", "title": "Public Transit Stop Infrastructure Audit", "formId": "transport_transit_stop_audit_v1", "version": "1.0", "category": "transport", "createdBy": {"name": "ZINGSA Transport Division", "email": "transport@zingsa.org"}, "projectId": "PROJ-C104EF", "questions": [{"id": "stop_location", "hint": "Capture the stop pole or shelter centroid.", "type": "location", "label": "Transit Stop Location", "required": true}, {"id": "stop_id", "hint": "Operator or municipal asset register identifier.", "type": "text", "label": "Stop ID", "required": true, "maxLength": 64, "minLength": 2, "placeholder": "e.g. BRT-HRE-0142"}, {"id": "stop_name", "hint": "Passenger-facing stop name on signage.", "type": "text", "label": "Stop Name", "required": true, "maxLength": 120}, {"id": "transit_mode", "type": "dropdown", "label": "Transit Mode", "options": [{"label": "Bus", "value": "bus"}, {"label": "Light Rail", "value": "light_rail"}, {"label": "BRT", "value": "brt"}], "required": true}, {"id": "routes_served", "hint": "Comma-separated route numbers observed on signage or timetables.", "type": "text", "label": "Routes Served", "required": false, "maxLength": 200, "placeholder": "e.g. R1, R4, ZUPCO 42"}, {"id": "has_shelter", "type": "boolean", "label": "Passenger Shelter Present", "required": true}, {"id": "shelter_condition", "hint": "If no shelter, select Poor and note in comments.", "type": "dropdown", "label": "Shelter Condition", "options": [{"label": "Excellent", "value": "excellent"}, {"label": "Good", "value": "good"}, {"label": "Poor", "value": "poor"}, {"label": "Vandalized", "value": "vandalized"}], "required": true}, {"id": "seating_available", "type": "boolean", "label": "Seating Available", "required": false}, {"id": "wheelchair_accessible", "hint": "Level boarding, ramp, or compliant access path to boarding area.", "type": "boolean", "label": "Wheelchair Accessible", "required": true}, {"id": "lighting_functional", "hint": "Assess at dusk if possible; note if not observable during day audit.", "type": "boolean", "label": "Lighting Functional", "required": true}, {"id": "real_time_display", "type": "boolean", "label": "Real-Time Passenger Information Display", "required": false}, {"id": "safety_rating", "max": 5, "min": 1, "hint": "Inspector subjective safety score for waiting passengers.", "type": "number", "label": "Perceived Safety Rating (1–5)", "required": false, "numericType": "integer"}, {"id": "stop_photo", "hint": "Wide shot showing shelter, signage, and immediate road environment.", "type": "image", "label": "Stop Photograph", "required": true, "maxPhotos": 4}, {"id": "general_comments", "type": "text", "label": "General Comments", "required": false, "maxLength": 1000, "placeholder": "Maintenance backlog, vandalism, accessibility gaps, or operator coordination notes."}], "createdDate": "2026-05-27T22:14:14Z", "description": "Infrastructure condition survey for public transport stops along national and urban corridors. Documents shelter, accessibility, lighting, signage, and passenger amenity standards for bus, BRT, and light-rail interfaces.", "geometryType": "point"}	6877b700192c2c01a55b6e0cbcadf5d4959bd9a1929492289c2d38c35ef82727	t	collect_public_transit_stop_infrastructure_audit_v1_57abe1a1	{"stop_id": "stop_id", "stop_name": "stop_name", "stop_photo": "stop_photo", "has_shelter": "has_shelter", "transit_mode": "transit_mode", "routes_served": "routes_served", "safety_rating": "safety_rating", "stop_location": "stop_location", "general_comments": "general_comments", "real_time_display": "real_time_display", "seating_available": "seating_available", "shelter_condition": "shelter_condition", "lighting_functional": "lighting_functional", "wheelchair_accessible": "wheelchair_accessible"}	2026-05-27 22:14:15.053614+00	2026-05-27 22:14:14.9846+00	1	57abe1a1-a564-4576-bdf8-8a3c964d350d
\.


--
-- Data for Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, geom, pitdepth, pitstatus, sitephotos, watercolor, mineraltype, pitdiameter, waterfilled, inspectiondate, hazardsobserved, inspectionnotes, childrenobserved, estimatedworkers, equipmentobserved, recommendedaction, siteaccessibility, environmentaldamage, rehabilitationneeded) FROM stdin;
\.


--
-- Data for Name: collect_intersection_traffic_pedestrian_audit_v1_6e033286; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, audit_date, audit_summary, junction_type, audit_time_period, intersection_name, conflict_observations, inspector_audio_notes, intersection_location, signal_cycle_observed, count_duration_minutes, cyclist_volume_per_hour, vehicle_volume_per_hour, traffic_light_functional, heavy_vehicles_percentage, pedestrian_volume_per_hour, pedestrian_crossings_available) FROM stdin;
\.


--
-- Data for Name: collect_organization; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_organization (id, name, code, created_at, updated_at) FROM stdin;
a66c238f-1a3e-4290-a70c-9ea8e0315136	ZINGSA Seed Org	ORG-CB8FB2	2026-05-27 22:08:27.735466+00	2026-05-27 22:08:27.735494+00
d5afe950-2a21-4431-b870-7edeeed17e1a	ZINGSA Seed Org	ORG-7B6CE8	2026-05-27 22:08:51.676297+00	2026-05-27 22:08:51.676316+00
\.


--
-- Data for Name: collect_organization_member; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_organization_member (id, role, created_at, updated_at, organization_id, user_id) FROM stdin;
b525df49-8855-4b9a-bd3c-82d4f79a8e42	admin	2026-05-27 22:08:27.751152+00	2026-05-27 22:08:27.751172+00	a66c238f-1a3e-4290-a70c-9ea8e0315136	1
829db4cd-e588-4e3f-b7ee-4cd243d8b5fd	admin	2026-05-27 22:08:51.677536+00	2026-05-27 22:08:51.677549+00	d5afe950-2a21-4431-b870-7edeeed17e1a	1
\.


--
-- Data for Name: collect_project; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_project (id, name, code, description, status, created_at, updated_at, organization_id, owner_id) FROM stdin;
0b3f4cd5-3632-4377-a117-7bc333935b66	Master Forms Project	PROJ-573570	\N	active	2026-05-27 22:08:27.861769+00	2026-05-27 22:08:27.861788+00	a66c238f-1a3e-4290-a70c-9ea8e0315136	1
f7c0b8a5-d266-4da7-b077-75ab730cbf90	Master Forms Project	PROJ-B07A5B	\N	active	2026-05-27 22:08:51.746358+00	2026-05-27 22:08:51.746378+00	d5afe950-2a21-4431-b870-7edeeed17e1a	1
b4a49c48-8079-4cb2-859a-b41a953903f3	National Highway & Transport Survey	PROJ-C104EF	\N	active	2026-05-27 22:14:14.335829+00	2026-05-27 22:14:14.335951+00	d5afe950-2a21-4431-b870-7edeeed17e1a	1
\.


--
-- Data for Name: collect_project_member; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_project_member (id, role, created_at, updated_at, project_id, user_id) FROM stdin;
bc5ac3f9-e478-4b14-bc82-c919211d0af0	manager	2026-05-27 22:08:27.869048+00	2026-05-27 22:08:27.869076+00	0b3f4cd5-3632-4377-a117-7bc333935b66	1
ba3559e3-c97f-4e6b-a258-47898a4ec24b	manager	2026-05-27 22:08:51.748714+00	2026-05-27 22:08:51.748735+00	f7c0b8a5-d266-4da7-b077-75ab730cbf90	1
aa9a4ae1-ca44-4d7c-9c9b-6ca5557a1d9f	manager	2026-05-27 22:14:14.342712+00	2026-05-27 22:14:14.342735+00	b4a49c48-8079-4cb2-859a-b41a953903f3	1
\.


--
-- Data for Name: collect_public_transit_stop_infrastructure_audit_v1_57abe1a1; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, stop_id, stop_name, stop_photo, has_shelter, transit_mode, routes_served, safety_rating, stop_location, general_comments, real_time_display, seating_available, shelter_condition, lighting_functional, wheelchair_accessible) FROM stdin;
\.


--
-- Data for Name: collect_road_network_survey_v1_5bea3d58; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_road_network_survey_v1_5bea3d58 (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, geom, roadname, roadtype, roadwidth, roadphotos, surveydate, surfacetype, accessibility, roadcondition, trafficvolume, conditionissues, inspectionnotes, digitalsignature, maintenancerequired) FROM stdin;
\.


--
-- Data for Name: collect_road_surface_quality_defect_assessment_v1_2cef056f; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_road_surface_quality_defect_assessment_v1_2cef056f (id, submission_uuid, project_id, form_id, form_version_id, submitted_by_id, device_id, client_submission_id, sync_status, synced_at, created_at, updated_at, defect_photo, pavement_type, chainage_end_km, defect_severity, road_segment_id, assessed_segment, segment_length_m, carriageway_lanes, chainage_start_km, inspector_remarks, drainage_condition, highway_designation, maintenance_urgency, primary_defect_type, defect_extent_percent, surface_condition_index) FROM stdin;
\.


--
-- Data for Name: collect_submission_index; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_submission_index (id, device_id, client_submission_id, physical_table_name, physical_row_id, sync_status, synced_at, created_at, updated_at, form_id, form_version_id, project_id, submitted_by_id) FROM stdin;
\.


--
-- Data for Name: collect_submission_media; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_submission_media (id, field_id, file, file_url, file_type, original_name, mime_type, size, checksum, created_at, submission_index_id) FROM stdin;
\.


--
-- Data for Name: collect_sync_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.collect_sync_log (id, device_id, total_received, total_success, total_failed, conflict_count, started_at, finished_at, log, form_id, project_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_clockedschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_clockedschedule (id, clocked_time) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_crontabschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_crontabschedule (id, minute, hour, day_of_week, day_of_month, month_of_year, timezone) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_intervalschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_intervalschedule (id, every, period) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_periodictask; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_periodictask (id, name, task, args, kwargs, queue, exchange, routing_key, expires, enabled, last_run_at, total_run_count, date_changed, description, crontab_id, interval_id, solar_id, one_off, start_time, priority, headers, clocked_id, expire_seconds) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_periodictasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_periodictasks (ident, last_update) FROM stdin;
\.


--
-- Data for Name: django_celery_beat_solarschedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_celery_beat_solarschedule (id, event, latitude, longitude) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	django_celery_beat	crontabschedule
7	django_celery_beat	intervalschedule
8	django_celery_beat	periodictask
9	django_celery_beat	periodictasks
10	django_celery_beat	solarschedule
11	django_celery_beat	clockedschedule
12	auditlog	logentry
13	accounts	user
14	organizations	organization
15	projects	project
16	forms	form
17	forms	formversion
18	submissions	submissionindex
19	submissions	submissionmedia
20	sync	synclog
21	organizations	organizationmember
22	projects	projectmember
23	forms	formfieldtype
24	mediafiles	mediafile
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2026-05-27 12:18:47.578397+00
2	contenttypes	0002_remove_content_type_name	2026-05-27 12:18:47.626074+00
3	auth	0001_initial	2026-05-27 12:18:47.845665+00
4	auth	0002_alter_permission_name_max_length	2026-05-27 12:18:47.867364+00
5	auth	0003_alter_user_email_max_length	2026-05-27 12:18:47.883753+00
6	auth	0004_alter_user_username_opts	2026-05-27 12:18:47.906239+00
7	auth	0005_alter_user_last_login_null	2026-05-27 12:18:47.927566+00
8	auth	0006_require_contenttypes_0002	2026-05-27 12:18:47.94095+00
9	auth	0007_alter_validators_add_error_messages	2026-05-27 12:18:47.958769+00
10	auth	0008_alter_user_username_max_length	2026-05-27 12:18:47.978664+00
11	auth	0009_alter_user_last_name_max_length	2026-05-27 12:18:47.995522+00
12	auth	0010_alter_group_name_max_length	2026-05-27 12:18:48.019998+00
13	auth	0011_update_proxy_permissions	2026-05-27 12:18:48.045002+00
14	auth	0012_alter_user_first_name_max_length	2026-05-27 12:18:48.064579+00
15	accounts	0001_initial	2026-05-27 12:18:48.324209+00
16	admin	0001_initial	2026-05-27 12:18:48.394109+00
17	admin	0002_logentry_remove_auto_add	2026-05-27 12:18:48.411417+00
18	admin	0003_logentry_add_action_flag_choices	2026-05-27 12:18:48.435836+00
19	auditlog	0001_initial	2026-05-27 12:18:48.61997+00
20	auditlog	0002_auto_support_long_primary_keys	2026-05-27 12:18:48.782017+00
21	auditlog	0003_logentry_remote_addr	2026-05-27 12:18:48.83983+00
22	auditlog	0004_logentry_detailed_object_repr	2026-05-27 12:18:48.87763+00
23	auditlog	0005_logentry_additional_data_verbose_name	2026-05-27 12:18:48.902858+00
24	auditlog	0006_object_pk_index	2026-05-27 12:18:49.009793+00
25	auditlog	0007_object_pk_type	2026-05-27 12:18:49.036401+00
26	auditlog	0008_action_index	2026-05-27 12:18:49.083382+00
27	auditlog	0009_alter_logentry_additional_data	2026-05-27 12:18:49.107147+00
28	auditlog	0010_alter_logentry_timestamp	2026-05-27 12:18:49.147281+00
29	auditlog	0011_logentry_serialized_data	2026-05-27 12:18:49.178184+00
30	auditlog	0012_add_logentry_action_access	2026-05-27 12:18:49.199477+00
31	django_celery_beat	0001_initial	2026-05-27 12:18:49.377069+00
32	django_celery_beat	0002_auto_20161118_0346	2026-05-27 12:18:49.442634+00
33	django_celery_beat	0003_auto_20161209_0049	2026-05-27 12:18:49.477899+00
34	django_celery_beat	0004_auto_20170221_0000	2026-05-27 12:18:49.493955+00
35	django_celery_beat	0005_add_solarschedule_events_choices	2026-05-27 12:18:49.515559+00
36	django_celery_beat	0006_auto_20180322_0932	2026-05-27 12:18:49.646009+00
37	django_celery_beat	0007_auto_20180521_0826	2026-05-27 12:18:49.711311+00
38	django_celery_beat	0008_auto_20180914_1922	2026-05-27 12:18:49.802321+00
39	django_celery_beat	0006_auto_20180210_1226	2026-05-27 12:18:49.868165+00
40	django_celery_beat	0006_periodictask_priority	2026-05-27 12:18:49.917717+00
41	django_celery_beat	0009_periodictask_headers	2026-05-27 12:18:49.962943+00
42	django_celery_beat	0010_auto_20190429_0326	2026-05-27 12:18:50.4765+00
43	django_celery_beat	0011_auto_20190508_0153	2026-05-27 12:18:51.526826+00
44	django_celery_beat	0012_periodictask_expire_seconds	2026-05-27 12:18:51.673139+00
45	django_celery_beat	0013_auto_20200609_0727	2026-05-27 12:18:51.827228+00
46	django_celery_beat	0014_remove_clockedschedule_enabled	2026-05-27 12:18:51.969894+00
47	django_celery_beat	0015_edit_solarschedule_events_choices	2026-05-27 12:18:52.126527+00
48	django_celery_beat	0016_alter_crontabschedule_timezone	2026-05-27 12:18:52.294591+00
49	django_celery_beat	0017_alter_crontabschedule_month_of_year	2026-05-27 12:18:52.448436+00
50	django_celery_beat	0018_improve_crontab_helptext	2026-05-27 12:18:52.627172+00
51	organizations	0001_initial	2026-05-27 12:18:55.733171+00
52	projects	0001_initial	2026-05-27 12:18:56.613623+00
53	forms	0001_initial	2026-05-27 12:18:57.028064+00
54	sessions	0001_initial	2026-05-27 12:18:57.099716+00
55	submissions	0001_initial	2026-05-27 12:18:57.328787+00
56	sync	0001_initial	2026-05-27 12:18:57.468123+00
57	organizations	0002_organizationmember	2026-05-27 18:11:43.234886+00
58	projects	0002_projectmember	2026-05-27 18:11:43.433383+00
59	forms	0002_formfieldtype	2026-05-27 19:38:11.637723+00
60	mediafiles	0001_initial	2026-05-27 21:27:23.986797+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: forms_field_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.forms_field_type (id, name, label, description, category, is_active) FROM stdin;
1	text	Single-line text input		Basic	t
2	textarea	Multi-line text input		Basic	t
3	email	Email input		Basic	t
4	phone	Phone number input		Basic	t
5	url	URL input		Basic	t
6	number	Numeric input		Basic	t
7	date	Date picker		Date & Time	t
8	time	Time picker		Date & Time	t
9	radio	Single-choice selection		Selection	t
10	checkbox	Multiple-choice selection		Selection	t
11	dropdown	Dropdown selection		Selection	t
12	image	Image/photo capture		Media	t
13	video	Video capture		Media	t
14	voice	Voice recording		Media	t
15	audio	Audio recording		Media	t
16	signature	Signature capture		Media	t
17	file	Generic file upload		Media	t
18	location	GPS location capture		GIS	t
19	point	GPS point capture		GIS	t
20	line	GIS line capture		GIS	t
21	polygon	GIS polygon capture		GIS	t
22	barcode	Barcode scanner		Scanning	t
23	qr	QR scanner		Scanning	t
\.


--
-- Data for Name: mediafiles_mediafile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mediafiles_mediafile (id, file, original_name, file_type, file_size, created_at, uploaded_by_id) FROM stdin;
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Name: accounts_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_user_groups_id_seq', 1, false);


--
-- Name: accounts_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_user_id_seq', 1, true);


--
-- Name: accounts_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_user_user_permissions_id_seq', 1, false);


--
-- Name: auditlog_logentry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auditlog_logentry_id_seq', 1, false);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 96, true);


--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_agricultural_field_validation_survey_v1_aaeb9c7b_id_seq', 1, false);


--
-- Name: collect_community_census_data_collection_v1_72f41e4f_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_community_census_data_collection_v1_72f41e4f_id_seq', 1, false);


--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_id_seq', 1, false);


--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_intersection_traffic_pedestrian_audit_v1_6e03328_id_seq', 1, false);


--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_public_transit_stop_infrastructure_audit_v1_57ab_id_seq', 1, false);


--
-- Name: collect_road_network_survey_v1_5bea3d58_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_road_network_survey_v1_5bea3d58_id_seq', 1, false);


--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.collect_road_surface_quality_defect_assessment_v1_2cef05_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_celery_beat_clockedschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_celery_beat_clockedschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_crontabschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_celery_beat_crontabschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_intervalschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_celery_beat_intervalschedule_id_seq', 1, false);


--
-- Name: django_celery_beat_periodictask_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_celery_beat_periodictask_id_seq', 1, false);


--
-- Name: django_celery_beat_solarschedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_celery_beat_solarschedule_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 24, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 60, true);


--
-- Name: forms_field_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.forms_field_type_id_seq', 23, true);


--
-- Name: topology_id_seq; Type: SEQUENCE SET; Schema: topology; Owner: postgres
--

SELECT pg_catalog.setval('topology.topology_id_seq', 1, false);


--
-- Name: accounts_user_groups accounts_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_groups accounts_user_groups_user_id_group_id_59c0b32f_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_user_id_group_id_59c0b32f_uniq UNIQUE (user_id, group_id);


--
-- Name: accounts_user accounts_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user
    ADD CONSTRAINT accounts_user_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_user_permissions accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_permi_user_id_permission_id_2ab516c2_uniq UNIQUE (user_id, permission_id);


--
-- Name: accounts_user_user_permissions accounts_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: accounts_user accounts_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user
    ADD CONSTRAINT accounts_user_username_key UNIQUE (username);


--
-- Name: auditlog_logentry auditlog_logentry_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditlog_logentry
    ADD CONSTRAINT auditlog_logentry_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: collect_agricultural_field_validation_survey_v1_aaeb9c7b collect_agricultural_field_validation_survey_v1_aaeb9c7b_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_agricultural_field_validation_survey_v1_aaeb9c7b
    ADD CONSTRAINT collect_agricultural_field_validation_survey_v1_aaeb9c7b_pkey PRIMARY KEY (id);


--
-- Name: collect_community_census_data_collection_v1_72f41e4f collect_community_census_data_collection_v1_72f41e4f_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_community_census_data_collection_v1_72f41e4f
    ADD CONSTRAINT collect_community_census_data_collection_v1_72f41e4f_pkey PRIMARY KEY (id);


--
-- Name: collect_form collect_form_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form
    ADD CONSTRAINT collect_form_pkey PRIMARY KEY (id);


--
-- Name: collect_form collect_form_project_id_slug_b8442fa5_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form
    ADD CONSTRAINT collect_form_project_id_slug_b8442fa5_uniq UNIQUE (project_id, slug);


--
-- Name: collect_form_version collect_form_version_form_id_version_number_0a9dc385_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form_version
    ADD CONSTRAINT collect_form_version_form_id_version_number_0a9dc385_uniq UNIQUE (form_id, version_number);


--
-- Name: collect_form_version collect_form_version_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form_version
    ADD CONSTRAINT collect_form_version_pkey PRIMARY KEY (id);


--
-- Name: collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9
    ADD CONSTRAINT collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_pkey PRIMARY KEY (id);


--
-- Name: collect_intersection_traffic_pedestrian_audit_v1_6e033286 collect_intersection_traffic_pedestrian_audit_v1_6e033286_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_intersection_traffic_pedestrian_audit_v1_6e033286
    ADD CONSTRAINT collect_intersection_traffic_pedestrian_audit_v1_6e033286_pkey PRIMARY KEY (id);


--
-- Name: collect_organization collect_organization_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization
    ADD CONSTRAINT collect_organization_code_key UNIQUE (code);


--
-- Name: collect_organization_member collect_organization_mem_organization_id_user_id_149eb8cd_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization_member
    ADD CONSTRAINT collect_organization_mem_organization_id_user_id_149eb8cd_uniq UNIQUE (organization_id, user_id);


--
-- Name: collect_organization_member collect_organization_member_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization_member
    ADD CONSTRAINT collect_organization_member_pkey PRIMARY KEY (id);


--
-- Name: collect_organization collect_organization_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization
    ADD CONSTRAINT collect_organization_pkey PRIMARY KEY (id);


--
-- Name: collect_project collect_project_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project
    ADD CONSTRAINT collect_project_code_key UNIQUE (code);


--
-- Name: collect_project_member collect_project_member_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project_member
    ADD CONSTRAINT collect_project_member_pkey PRIMARY KEY (id);


--
-- Name: collect_project_member collect_project_member_project_id_user_id_b7205a8b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project_member
    ADD CONSTRAINT collect_project_member_project_id_user_id_b7205a8b_uniq UNIQUE (project_id, user_id);


--
-- Name: collect_project collect_project_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project
    ADD CONSTRAINT collect_project_pkey PRIMARY KEY (id);


--
-- Name: collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 collect_public_transit_stop_infrastructure_audit_v1_57abe1_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1
    ADD CONSTRAINT collect_public_transit_stop_infrastructure_audit_v1_57abe1_pkey PRIMARY KEY (id);


--
-- Name: collect_road_network_survey_v1_5bea3d58 collect_road_network_survey_v1_5bea3d58_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_road_network_survey_v1_5bea3d58
    ADD CONSTRAINT collect_road_network_survey_v1_5bea3d58_pkey PRIMARY KEY (id);


--
-- Name: collect_road_surface_quality_defect_assessment_v1_2cef056f collect_road_surface_quality_defect_assessment_v1_2cef056f_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_road_surface_quality_defect_assessment_v1_2cef056f
    ADD CONSTRAINT collect_road_surface_quality_defect_assessment_v1_2cef056f_pkey PRIMARY KEY (id);


--
-- Name: collect_submission_index collect_submission_index_device_id_client_submiss_ad778979_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_index_device_id_client_submiss_ad778979_uniq UNIQUE (device_id, client_submission_id, form_id);


--
-- Name: collect_submission_index collect_submission_index_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_index_pkey PRIMARY KEY (id);


--
-- Name: collect_submission_media collect_submission_media_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_media
    ADD CONSTRAINT collect_submission_media_pkey PRIMARY KEY (id);


--
-- Name: collect_sync_log collect_sync_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_sync_log
    ADD CONSTRAINT collect_sync_log_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_clockedschedule django_celery_beat_clockedschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_clockedschedule
    ADD CONSTRAINT django_celery_beat_clockedschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_crontabschedule django_celery_beat_crontabschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_crontabschedule
    ADD CONSTRAINT django_celery_beat_crontabschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_intervalschedule django_celery_beat_intervalschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_intervalschedule
    ADD CONSTRAINT django_celery_beat_intervalschedule_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_periodictask django_celery_beat_periodictask_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_periodictask_name_key UNIQUE (name);


--
-- Name: django_celery_beat_periodictask django_celery_beat_periodictask_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_periodictask_pkey PRIMARY KEY (id);


--
-- Name: django_celery_beat_periodictasks django_celery_beat_periodictasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictasks
    ADD CONSTRAINT django_celery_beat_periodictasks_pkey PRIMARY KEY (ident);


--
-- Name: django_celery_beat_solarschedule django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_solarschedule
    ADD CONSTRAINT django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq UNIQUE (event, latitude, longitude);


--
-- Name: django_celery_beat_solarschedule django_celery_beat_solarschedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_solarschedule
    ADD CONSTRAINT django_celery_beat_solarschedule_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: forms_field_type forms_field_type_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forms_field_type
    ADD CONSTRAINT forms_field_type_name_key UNIQUE (name);


--
-- Name: forms_field_type forms_field_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forms_field_type
    ADD CONSTRAINT forms_field_type_pkey PRIMARY KEY (id);


--
-- Name: mediafiles_mediafile mediafiles_mediafile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mediafiles_mediafile
    ADD CONSTRAINT mediafiles_mediafile_pkey PRIMARY KEY (id);


--
-- Name: accounts_user_groups_group_id_bd11a704; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX accounts_user_groups_group_id_bd11a704 ON public.accounts_user_groups USING btree (group_id);


--
-- Name: accounts_user_groups_user_id_52b62117; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX accounts_user_groups_user_id_52b62117 ON public.accounts_user_groups USING btree (user_id);


--
-- Name: accounts_user_user_permissions_permission_id_113bb443; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX accounts_user_user_permissions_permission_id_113bb443 ON public.accounts_user_user_permissions USING btree (permission_id);


--
-- Name: accounts_user_user_permissions_user_id_e4f0a161; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX accounts_user_user_permissions_user_id_e4f0a161 ON public.accounts_user_user_permissions USING btree (user_id);


--
-- Name: accounts_user_username_6088629e_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX accounts_user_username_6088629e_like ON public.accounts_user USING btree (username varchar_pattern_ops);


--
-- Name: auditlog_logentry_action_229afe39; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_action_229afe39 ON public.auditlog_logentry USING btree (action);


--
-- Name: auditlog_logentry_actor_id_959271d2; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_actor_id_959271d2 ON public.auditlog_logentry USING btree (actor_id);


--
-- Name: auditlog_logentry_content_type_id_75830218; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_content_type_id_75830218 ON public.auditlog_logentry USING btree (content_type_id);


--
-- Name: auditlog_logentry_object_id_09c2eee8; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_object_id_09c2eee8 ON public.auditlog_logentry USING btree (object_id);


--
-- Name: auditlog_logentry_object_pk_6e3219c0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_object_pk_6e3219c0 ON public.auditlog_logentry USING btree (object_pk);


--
-- Name: auditlog_logentry_object_pk_6e3219c0_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_object_pk_6e3219c0_like ON public.auditlog_logentry USING btree (object_pk varchar_pattern_ops);


--
-- Name: auditlog_logentry_timestamp_37867bb0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auditlog_logentry_timestamp_37867bb0 ON public.auditlog_logentry USING btree ("timestamp");


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: collect_form_created_by_id_34513344; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_created_by_id_34513344 ON public.collect_form USING btree (created_by_id);


--
-- Name: collect_form_current_version_id_8233fc87; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_current_version_id_8233fc87 ON public.collect_form USING btree (current_version_id);


--
-- Name: collect_form_project_id_f5edcbab; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_project_id_f5edcbab ON public.collect_form USING btree (project_id);


--
-- Name: collect_form_slug_cadc5dfb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_slug_cadc5dfb ON public.collect_form USING btree (slug);


--
-- Name: collect_form_slug_cadc5dfb_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_slug_cadc5dfb_like ON public.collect_form USING btree (slug varchar_pattern_ops);


--
-- Name: collect_form_version_created_by_id_e6dfeafd; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_version_created_by_id_e6dfeafd ON public.collect_form_version USING btree (created_by_id);


--
-- Name: collect_form_version_form_id_12349954; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_form_version_form_id_12349954 ON public.collect_form_version USING btree (form_id);


--
-- Name: collect_organization_code_89cd50c0_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_organization_code_89cd50c0_like ON public.collect_organization USING btree (code varchar_pattern_ops);


--
-- Name: collect_organization_member_organization_id_3d7d7b97; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_organization_member_organization_id_3d7d7b97 ON public.collect_organization_member USING btree (organization_id);


--
-- Name: collect_organization_member_user_id_44ce3d69; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_organization_member_user_id_44ce3d69 ON public.collect_organization_member USING btree (user_id);


--
-- Name: collect_project_code_c9b45d95_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_project_code_c9b45d95_like ON public.collect_project USING btree (code varchar_pattern_ops);


--
-- Name: collect_project_member_project_id_acb77baa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_project_member_project_id_acb77baa ON public.collect_project_member USING btree (project_id);


--
-- Name: collect_project_member_user_id_65a8e06b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_project_member_user_id_65a8e06b ON public.collect_project_member USING btree (user_id);


--
-- Name: collect_project_organization_id_d1ab8ff0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_project_organization_id_d1ab8ff0 ON public.collect_project USING btree (organization_id);


--
-- Name: collect_project_owner_id_0f8813dc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_project_owner_id_0f8813dc ON public.collect_project USING btree (owner_id);


--
-- Name: collect_submission_index_form_id_cb8a3e30; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_submission_index_form_id_cb8a3e30 ON public.collect_submission_index USING btree (form_id);


--
-- Name: collect_submission_index_form_version_id_bb027fb0; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_submission_index_form_version_id_bb027fb0 ON public.collect_submission_index USING btree (form_version_id);


--
-- Name: collect_submission_index_project_id_72230e98; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_submission_index_project_id_72230e98 ON public.collect_submission_index USING btree (project_id);


--
-- Name: collect_submission_index_submitted_by_id_bcc8f1fe; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_submission_index_submitted_by_id_bcc8f1fe ON public.collect_submission_index USING btree (submitted_by_id);


--
-- Name: collect_submission_media_submission_index_id_70aaa076; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_submission_media_submission_index_id_70aaa076 ON public.collect_submission_media USING btree (submission_index_id);


--
-- Name: collect_sync_log_form_id_3622bc00; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_sync_log_form_id_3622bc00 ON public.collect_sync_log USING btree (form_id);


--
-- Name: collect_sync_log_project_id_497eb44b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_sync_log_project_id_497eb44b ON public.collect_sync_log USING btree (project_id);


--
-- Name: collect_sync_log_user_id_5703d5cb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX collect_sync_log_user_id_5703d5cb ON public.collect_sync_log USING btree (user_id);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_celery_beat_periodictask_clocked_id_47a69f82; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_celery_beat_periodictask_clocked_id_47a69f82 ON public.django_celery_beat_periodictask USING btree (clocked_id);


--
-- Name: django_celery_beat_periodictask_crontab_id_d3cba168; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_celery_beat_periodictask_crontab_id_d3cba168 ON public.django_celery_beat_periodictask USING btree (crontab_id);


--
-- Name: django_celery_beat_periodictask_interval_id_a8ca27da; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_celery_beat_periodictask_interval_id_a8ca27da ON public.django_celery_beat_periodictask USING btree (interval_id);


--
-- Name: django_celery_beat_periodictask_name_265a36b7_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_celery_beat_periodictask_name_265a36b7_like ON public.django_celery_beat_periodictask USING btree (name varchar_pattern_ops);


--
-- Name: django_celery_beat_periodictask_solar_id_a87ce72c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_celery_beat_periodictask_solar_id_a87ce72c ON public.django_celery_beat_periodictask USING btree (solar_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: forms_field_type_name_e0122f60_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX forms_field_type_name_e0122f60_like ON public.forms_field_type USING btree (name varchar_pattern_ops);


--
-- Name: gist_collect_agricultural_field_validation_survey_v1_aaeb9c7b_f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_agricultural_field_validation_survey_v1_aaeb9c7b_f ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING gist (fieldboundary);


--
-- Name: gist_collect_community_census_data_collection_v1_72f41e4f_house; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_community_census_data_collection_v1_72f41e4f_house ON public.collect_community_census_data_collection_v1_72f41e4f USING gist (householdlocation);


--
-- Name: gist_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_geo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_geo ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING gist (geom);


--
-- Name: gist_collect_intersection_traffic_pedestrian_audit_v1_6e033286_; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_intersection_traffic_pedestrian_audit_v1_6e033286_ ON public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 USING gist (intersection_location);


--
-- Name: gist_collect_public_transit_stop_infrastructure_audit_v1_57abe1; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_public_transit_stop_infrastructure_audit_v1_57abe1 ON public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 USING gist (stop_location);


--
-- Name: gist_collect_road_network_survey_v1_5bea3d58_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_road_network_survey_v1_5bea3d58_geom ON public.collect_road_network_survey_v1_5bea3d58 USING gist (geom);


--
-- Name: gist_collect_road_surface_quality_defect_assessment_v1_2cef056f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX gist_collect_road_surface_quality_defect_assessment_v1_2cef056f ON public.collect_road_surface_quality_defect_assessment_v1_2cef056f USING gist (assessed_segment);


--
-- Name: idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_cl; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_cl ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING btree (client_submission_id);


--
-- Name: idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_fo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_fo ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING btree (form_id);


--
-- Name: idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_pr; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_pr ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING btree (project_id);


--
-- Name: idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_su; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_su ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING btree (submitted_by_id);


--
-- Name: idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_sy; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_agricultural_field_validation_survey_v1_aaeb9c7b_sy ON public.collect_agricultural_field_validation_survey_v1_aaeb9c7b USING btree (synced_at);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_client; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_client ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (client_submission_id);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_form_i; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_form_i ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (form_id);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_form_v; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_form_v ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (form_version_id);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_projec; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_projec ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (project_id);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_submit; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_submit ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (submitted_by_id);


--
-- Name: idx_collect_community_census_data_collection_v1_72f41e4f_synced; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_community_census_data_collection_v1_72f41e4f_synced ON public.collect_community_census_data_collection_v1_72f41e4f USING btree (synced_at);


--
-- Name: idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_clie; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_clie ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING btree (client_submission_id);


--
-- Name: idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_form; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_form ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING btree (form_id);


--
-- Name: idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_proj; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_proj ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING btree (project_id);


--
-- Name: idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_subm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_subm ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING btree (submitted_by_id);


--
-- Name: idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_sync; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_illegal_mine_pit_inspection_survey_v1_db3c56c9_sync ON public.collect_illegal_mine_pit_inspection_survey_v1_db3c56c9 USING btree (synced_at);


--
-- Name: idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_c ON public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 USING btree (client_submission_id);


--
-- Name: idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_f; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_f ON public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 USING btree (form_id);


--
-- Name: idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_p; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_p ON public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 USING btree (project_id);


--
-- Name: idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_s; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_intersection_traffic_pedestrian_audit_v1_6e033286_s ON public.collect_intersection_traffic_pedestrian_audit_v1_6e033286 USING btree (submitted_by_id);


--
-- Name: idx_collect_public_transit_stop_infrastructure_audit_v1_57abe1a; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_public_transit_stop_infrastructure_audit_v1_57abe1a ON public.collect_public_transit_stop_infrastructure_audit_v1_57abe1a1 USING btree (project_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_client_submission_i; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_client_submission_i ON public.collect_road_network_survey_v1_5bea3d58 USING btree (client_submission_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_form_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_form_id ON public.collect_road_network_survey_v1_5bea3d58 USING btree (form_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_form_version_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_form_version_id ON public.collect_road_network_survey_v1_5bea3d58 USING btree (form_version_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_project_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_project_id ON public.collect_road_network_survey_v1_5bea3d58 USING btree (project_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_submitted_by_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_submitted_by_id ON public.collect_road_network_survey_v1_5bea3d58 USING btree (submitted_by_id);


--
-- Name: idx_collect_road_network_survey_v1_5bea3d58_synced_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_network_survey_v1_5bea3d58_synced_at ON public.collect_road_network_survey_v1_5bea3d58 USING btree (synced_at);


--
-- Name: idx_collect_road_surface_quality_defect_assessment_v1_2cef056f_; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_collect_road_surface_quality_defect_assessment_v1_2cef056f_ ON public.collect_road_surface_quality_defect_assessment_v1_2cef056f USING btree (project_id);


--
-- Name: mediafiles_mediafile_uploaded_by_id_b1ea38ca; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX mediafiles_mediafile_uploaded_by_id_b1ea38ca ON public.mediafiles_mediafile USING btree (uploaded_by_id);


--
-- Name: accounts_user_groups accounts_user_groups_group_id_bd11a704_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_group_id_bd11a704_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_groups accounts_user_groups_user_id_52b62117_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_groups
    ADD CONSTRAINT accounts_user_groups_user_id_52b62117_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_user_permissions accounts_user_user_p_permission_id_113bb443_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_p_permission_id_113bb443_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: accounts_user_user_permissions accounts_user_user_p_user_id_e4f0a161_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts_user_user_permissions
    ADD CONSTRAINT accounts_user_user_p_user_id_e4f0a161_fk_accounts_ FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auditlog_logentry auditlog_logentry_actor_id_959271d2_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditlog_logentry
    ADD CONSTRAINT auditlog_logentry_actor_id_959271d2_fk_accounts_user_id FOREIGN KEY (actor_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auditlog_logentry auditlog_logentry_content_type_id_75830218_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auditlog_logentry
    ADD CONSTRAINT auditlog_logentry_content_type_id_75830218_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_form collect_form_created_by_id_34513344_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form
    ADD CONSTRAINT collect_form_created_by_id_34513344_fk_accounts_user_id FOREIGN KEY (created_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_form collect_form_current_version_id_8233fc87_fk_collect_f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form
    ADD CONSTRAINT collect_form_current_version_id_8233fc87_fk_collect_f FOREIGN KEY (current_version_id) REFERENCES public.collect_form_version(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_form collect_form_project_id_f5edcbab_fk_collect_project_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form
    ADD CONSTRAINT collect_form_project_id_f5edcbab_fk_collect_project_id FOREIGN KEY (project_id) REFERENCES public.collect_project(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_form_version collect_form_version_created_by_id_e6dfeafd_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form_version
    ADD CONSTRAINT collect_form_version_created_by_id_e6dfeafd_fk_accounts_user_id FOREIGN KEY (created_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_form_version collect_form_version_form_id_12349954_fk_collect_form_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_form_version
    ADD CONSTRAINT collect_form_version_form_id_12349954_fk_collect_form_id FOREIGN KEY (form_id) REFERENCES public.collect_form(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_organization_member collect_organization_organization_id_3d7d7b97_fk_collect_o; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization_member
    ADD CONSTRAINT collect_organization_organization_id_3d7d7b97_fk_collect_o FOREIGN KEY (organization_id) REFERENCES public.collect_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_organization_member collect_organization_user_id_44ce3d69_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_organization_member
    ADD CONSTRAINT collect_organization_user_id_44ce3d69_fk_accounts_ FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_project_member collect_project_memb_project_id_acb77baa_fk_collect_p; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project_member
    ADD CONSTRAINT collect_project_memb_project_id_acb77baa_fk_collect_p FOREIGN KEY (project_id) REFERENCES public.collect_project(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_project_member collect_project_member_user_id_65a8e06b_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project_member
    ADD CONSTRAINT collect_project_member_user_id_65a8e06b_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_project collect_project_organization_id_d1ab8ff0_fk_collect_o; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project
    ADD CONSTRAINT collect_project_organization_id_d1ab8ff0_fk_collect_o FOREIGN KEY (organization_id) REFERENCES public.collect_organization(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_project collect_project_owner_id_0f8813dc_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_project
    ADD CONSTRAINT collect_project_owner_id_0f8813dc_fk_accounts_user_id FOREIGN KEY (owner_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_submission_index collect_submission_i_form_version_id_bb027fb0_fk_collect_f; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_i_form_version_id_bb027fb0_fk_collect_f FOREIGN KEY (form_version_id) REFERENCES public.collect_form_version(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_submission_index collect_submission_i_project_id_72230e98_fk_collect_p; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_i_project_id_72230e98_fk_collect_p FOREIGN KEY (project_id) REFERENCES public.collect_project(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_submission_index collect_submission_i_submitted_by_id_bcc8f1fe_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_i_submitted_by_id_bcc8f1fe_fk_accounts_ FOREIGN KEY (submitted_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_submission_index collect_submission_index_form_id_cb8a3e30_fk_collect_form_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_index
    ADD CONSTRAINT collect_submission_index_form_id_cb8a3e30_fk_collect_form_id FOREIGN KEY (form_id) REFERENCES public.collect_form(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_submission_media collect_submission_m_submission_index_id_70aaa076_fk_collect_s; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_submission_media
    ADD CONSTRAINT collect_submission_m_submission_index_id_70aaa076_fk_collect_s FOREIGN KEY (submission_index_id) REFERENCES public.collect_submission_index(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_sync_log collect_sync_log_form_id_3622bc00_fk_collect_form_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_sync_log
    ADD CONSTRAINT collect_sync_log_form_id_3622bc00_fk_collect_form_id FOREIGN KEY (form_id) REFERENCES public.collect_form(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_sync_log collect_sync_log_project_id_497eb44b_fk_collect_project_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_sync_log
    ADD CONSTRAINT collect_sync_log_project_id_497eb44b_fk_collect_project_id FOREIGN KEY (project_id) REFERENCES public.collect_project(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: collect_sync_log collect_sync_log_user_id_5703d5cb_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.collect_sync_log
    ADD CONSTRAINT collect_sync_log_user_id_5703d5cb_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_accounts_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_clocked_id_47a69f82_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_clocked_id_47a69f82_fk_django_ce FOREIGN KEY (clocked_id) REFERENCES public.django_celery_beat_clockedschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_crontab_id_d3cba168_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_crontab_id_d3cba168_fk_django_ce FOREIGN KEY (crontab_id) REFERENCES public.django_celery_beat_crontabschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_interval_id_a8ca27da_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_interval_id_a8ca27da_fk_django_ce FOREIGN KEY (interval_id) REFERENCES public.django_celery_beat_intervalschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_celery_beat_periodictask django_celery_beat_p_solar_id_a87ce72c_fk_django_ce; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_celery_beat_periodictask
    ADD CONSTRAINT django_celery_beat_p_solar_id_a87ce72c_fk_django_ce FOREIGN KEY (solar_id) REFERENCES public.django_celery_beat_solarschedule(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: mediafiles_mediafile mediafiles_mediafile_uploaded_by_id_b1ea38ca_fk_accounts_; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mediafiles_mediafile
    ADD CONSTRAINT mediafiles_mediafile_uploaded_by_id_b1ea38ca_fk_accounts_ FOREIGN KEY (uploaded_by_id) REFERENCES public.accounts_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

--
-- PostgreSQL database cluster dump complete
--

