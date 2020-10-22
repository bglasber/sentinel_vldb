--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.16
-- Dumped by pg_dump version 9.5.16

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: benchmarkdatahook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.benchmarkdatahook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    benchmark_time double precision,
    overall_throughput double precision
);


ALTER TABLE public.benchmarkdatahook OWNER TO postgres;

--
-- Name: benchmarkdatahook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.benchmarkdatahook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.benchmarkdatahook_run_id_seq OWNER TO postgres;

--
-- Name: benchmarkdatahook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.benchmarkdatahook_run_id_seq OWNED BY public.benchmarkdatahook.run_id;


--
-- Name: benchmarkovertimehook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.benchmarkovertimehook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    "time" integer[],
    throughput double precision[],
    avg_lat double precision[],
    min_lat double precision[],
    lat_25 double precision[],
    lat_50 double precision[],
    lat_75 double precision[],
    lat_90 double precision[],
    lat_95 double precision[],
    lat_99 double precision[],
    max_lat double precision[],
    tput_scaled double precision[]
);


ALTER TABLE public.benchmarkovertimehook OWNER TO postgres;

--
-- Name: benchmarkovertimehook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.benchmarkovertimehook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.benchmarkovertimehook_run_id_seq OWNER TO postgres;

--
-- Name: benchmarkovertimehook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.benchmarkovertimehook_run_id_seq OWNED BY public.benchmarkovertimehook.run_id;


--
-- Name: distance_weights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.distance_weights (
    run_id integer NOT NULL,
    iteration_number integer NOT NULL,
    weights double precision[],
    error double precision,
    run_id_last_updated integer
);


ALTER TABLE public.distance_weights OWNER TO postgres;

--
-- Name: exp_iterations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exp_iterations (
    run_id integer NOT NULL,
    iteration_number integer NOT NULL
);


ALTER TABLE public.exp_iterations OWNER TO postgres;

--
-- Name: exp_iterations_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exp_iterations_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.exp_iterations_run_id_seq OWNER TO postgres;

--
-- Name: exp_iterations_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exp_iterations_run_id_seq OWNED BY public.exp_iterations.run_id;


--
-- Name: log_line_probabilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.log_line_probabilities (
    run_id integer,
    iteration_number integer,
    log_fname character varying(64),
    log_line bigint,
    log_probability double precision,
    log_count bigint
);


ALTER TABLE public.log_line_probabilities OWNER TO postgres;

--
-- Name: log_line_transitions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.log_line_transitions (
    run_id integer,
    iteration_number integer,
    log_initial_fname character varying(64),
    log_initial_line bigint,
    log_next_fname character varying(64),
    log_next_line bigint,
    transition_probability double precision,
    transition_count bigint
);


ALTER TABLE public.log_line_transitions OWNER TO postgres;

--
-- Name: machinehostnamehook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.machinehostnamehook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    machine_hostname character varying(32)
);


ALTER TABLE public.machinehostnamehook OWNER TO postgres;

--
-- Name: machinehostnamehook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.machinehostnamehook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.machinehostnamehook_run_id_seq OWNER TO postgres;

--
-- Name: machinehostnamehook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.machinehostnamehook_run_id_seq OWNED BY public.machinehostnamehook.run_id;


--
-- Name: oltpbenchmarkconfigurationhook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.oltpbenchmarkconfigurationhook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    benchmark_name text,
    scale_factor integer,
    benchmark_time integer,
    terminals integer,
    new_order_prob double precision,
    payment_prob double precision,
    order_status_prob double precision,
    delivery_prob double precision,
    stock_level_prob double precision,
    ycsb_read_prob double precision,
    ycsb_insert_prob double precision,
    ycsb_scan_prob double precision,
    ycsb_write_prob double precision,
    ycsb_delete_prob double precision,
    ycsb_rmw_prob double precision
);


ALTER TABLE public.oltpbenchmarkconfigurationhook OWNER TO postgres;

--
-- Name: oltpbenchmarkconfigurationhook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.oltpbenchmarkconfigurationhook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.oltpbenchmarkconfigurationhook_run_id_seq OWNER TO postgres;

--
-- Name: oltpbenchmarkconfigurationhook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.oltpbenchmarkconfigurationhook_run_id_seq OWNED BY public.oltpbenchmarkconfigurationhook.run_id;


--
-- Name: pgexprloptimizerhook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pgexprloptimizerhook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    optimizer_name text,
    next_run_param_names text[],
    next_run_param_values text[],
    optimizer_param_names text[],
    optimizer_param_values text[],
    target_metric text,
    predicted_metric double precision
);


ALTER TABLE public.pgexprloptimizerhook OWNER TO postgres;

--
-- Name: pgexprloptimizerhook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pgexprloptimizerhook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pgexprloptimizerhook_run_id_seq OWNER TO postgres;

--
-- Name: pgexprloptimizerhook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pgexprloptimizerhook_run_id_seq OWNED BY public.pgexprloptimizerhook.run_id;


--
-- Name: pgtransitionclusters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pgtransitionclusters (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    clusterid integer,
    member_run_ids integer[],
    member_iteration_numbers integer[]
);


ALTER TABLE public.pgtransitionclusters OWNER TO postgres;

--
-- Name: pgtransitionclusters_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pgtransitionclusters_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pgtransitionclusters_run_id_seq OWNER TO postgres;

--
-- Name: pgtransitionclusters_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pgtransitionclusters_run_id_seq OWNED BY public.pgtransitionclusters.run_id;


--
-- Name: postgresconfigurationhook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.postgresconfigurationhook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    configuration_name text[],
    configuration_value text[]
);


ALTER TABLE public.postgresconfigurationhook OWNER TO postgres;

--
-- Name: postgresconfigurationhook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.postgresconfigurationhook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.postgresconfigurationhook_run_id_seq OWNER TO postgres;

--
-- Name: postgresconfigurationhook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.postgresconfigurationhook_run_id_seq OWNED BY public.postgresconfigurationhook.run_id;


--
-- Name: postgresstatshook; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.postgresstatshook (
    run_id integer NOT NULL,
    iteration_number integer,
    machine_name character varying(128),
    datname text[],
    numbackends integer[],
    xact_commit bigint[],
    xact_rollback bigint[],
    blks_read bigint[],
    blks_hit bigint[],
    tup_returned bigint[],
    tup_fetched bigint[],
    tup_inserted bigint[],
    tup_updated bigint[],
    tup_deleted bigint[],
    conflicts bigint[],
    temp_files bigint[],
    temp_bytes bigint[],
    deadlocks bigint[],
    blk_read_time double precision[],
    blk_write_time double precision[]
);


ALTER TABLE public.postgresstatshook OWNER TO postgres;

--
-- Name: postgresstatshook_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.postgresstatshook_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.postgresstatshook_run_id_seq OWNER TO postgres;

--
-- Name: postgresstatshook_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.postgresstatshook_run_id_seq OWNED BY public.postgresstatshook.run_id;


--
-- Name: run_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.run_groups (
    run_id integer NOT NULL,
    run_group character varying(32) NOT NULL
);


ALTER TABLE public.run_groups OWNER TO postgres;

--
-- Name: run_groups_run_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.run_groups_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.run_groups_run_id_seq OWNER TO postgres;

--
-- Name: run_groups_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.run_groups_run_id_seq OWNED BY public.run_groups.run_id;


--
-- Name: run_identifier; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.run_identifier (
    id integer NOT NULL,
    creation_time timestamp without time zone
);


ALTER TABLE public.run_identifier OWNER TO postgres;

--
-- Name: run_identifier_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.run_identifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.run_identifier_id_seq OWNER TO postgres;

--
-- Name: run_identifier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.run_identifier_id_seq OWNED BY public.run_identifier.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tags (
    fname character varying(64) NOT NULL,
    line character varying(64) NOT NULL,
    tag character varying(64)
);


ALTER TABLE public.tags OWNER TO postgres;

--
-- Name: transition_cdfs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transition_cdfs (
    run_id integer NOT NULL,
    iteration_number integer NOT NULL,
    src_fname character varying(64) NOT NULL,
    src_line bigint NOT NULL,
    dst_fname character varying(64) NOT NULL,
    dst_line bigint NOT NULL,
    percentiles double precision[],
    percentile_values double precision[]
);


ALTER TABLE public.transition_cdfs OWNER TO postgres;

--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarkdatahook ALTER COLUMN run_id SET DEFAULT nextval('public.benchmarkdatahook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarkovertimehook ALTER COLUMN run_id SET DEFAULT nextval('public.benchmarkovertimehook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exp_iterations ALTER COLUMN run_id SET DEFAULT nextval('public.exp_iterations_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.machinehostnamehook ALTER COLUMN run_id SET DEFAULT nextval('public.machinehostnamehook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oltpbenchmarkconfigurationhook ALTER COLUMN run_id SET DEFAULT nextval('public.oltpbenchmarkconfigurationhook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pgexprloptimizerhook ALTER COLUMN run_id SET DEFAULT nextval('public.pgexprloptimizerhook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pgtransitionclusters ALTER COLUMN run_id SET DEFAULT nextval('public.pgtransitionclusters_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postgresconfigurationhook ALTER COLUMN run_id SET DEFAULT nextval('public.postgresconfigurationhook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postgresstatshook ALTER COLUMN run_id SET DEFAULT nextval('public.postgresstatshook_run_id_seq'::regclass);


--
-- Name: run_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_groups ALTER COLUMN run_id SET DEFAULT nextval('public.run_groups_run_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_identifier ALTER COLUMN id SET DEFAULT nextval('public.run_identifier_id_seq'::regclass);


--
-- Name: distance_weights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distance_weights
    ADD CONSTRAINT distance_weights_pkey PRIMARY KEY (run_id, iteration_number);


--
-- Name: exp_iterations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exp_iterations
    ADD CONSTRAINT exp_iterations_pkey PRIMARY KEY (run_id, iteration_number);


--
-- Name: run_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_groups
    ADD CONSTRAINT run_groups_pkey PRIMARY KEY (run_id, run_group);


--
-- Name: run_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_identifier
    ADD CONSTRAINT run_identifier_pkey PRIMARY KEY (id);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (fname, line);


--
-- Name: transition_cdfs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transition_cdfs
    ADD CONSTRAINT transition_cdfs_pkey PRIMARY KEY (run_id, iteration_number, src_fname, src_line, dst_fname, dst_line);


--
-- Name: distance_weights_last_updated_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX distance_weights_last_updated_idx ON public.distance_weights USING btree (run_id_last_updated);


--
-- Name: benchmarkdatahook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarkdatahook
    ADD CONSTRAINT benchmarkdatahook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: benchmarkovertimehook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.benchmarkovertimehook
    ADD CONSTRAINT benchmarkovertimehook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: distance_weights_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.distance_weights
    ADD CONSTRAINT distance_weights_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: exp_iterations_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exp_iterations
    ADD CONSTRAINT exp_iterations_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.run_identifier(id);


--
-- Name: log_line_probabilities_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.log_line_probabilities
    ADD CONSTRAINT log_line_probabilities_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: log_line_transitions_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.log_line_transitions
    ADD CONSTRAINT log_line_transitions_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: machinehostnamehook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.machinehostnamehook
    ADD CONSTRAINT machinehostnamehook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: oltpbenchmarkconfigurationhook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oltpbenchmarkconfigurationhook
    ADD CONSTRAINT oltpbenchmarkconfigurationhook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: pgexprloptimizerhook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pgexprloptimizerhook
    ADD CONSTRAINT pgexprloptimizerhook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: pgtransitionclusters_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pgtransitionclusters
    ADD CONSTRAINT pgtransitionclusters_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: postgresconfigurationhook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postgresconfigurationhook
    ADD CONSTRAINT postgresconfigurationhook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: postgresstatshook_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postgresstatshook
    ADD CONSTRAINT postgresstatshook_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: run_groups_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.run_groups
    ADD CONSTRAINT run_groups_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.run_identifier(id);


--
-- Name: transition_cdfs_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transition_cdfs
    ADD CONSTRAINT transition_cdfs_run_id_fkey FOREIGN KEY (run_id, iteration_number) REFERENCES public.exp_iterations(run_id, iteration_number);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

