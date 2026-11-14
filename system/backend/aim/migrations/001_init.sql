CREATE TABLE replay_run (
    replay_run_id UUID PRIMARY KEY,
    dataset TEXT NOT NULL,
    dataset_case TEXT NOT NULL,
    service_name TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    source_manifest JSONB NOT NULL,
    replayer_version TEXT NOT NULL,
    mapping_version TEXT NOT NULL,
    raw_start_unix_nano NUMERIC(20,0) NOT NULL,
    raw_end_unix_nano NUMERIC(20,0) NOT NULL,
    display_start_unix_nano NUMERIC(20,0) NOT NULL,
    display_end_unix_nano NUMERIC(20,0) NOT NULL,
    status TEXT NOT NULL DEFAULT 'created'
        CHECK (status IN ('created','ingesting','ingested','processing','processed','failed')),
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CHECK (raw_start_unix_nano >= 0 AND raw_end_unix_nano >= raw_start_unix_nano),
    CHECK (display_start_unix_nano >= raw_start_unix_nano),
    CHECK (display_end_unix_nano > display_start_unix_nano),
    CHECK (raw_end_unix_nano >= display_end_unix_nano)
);

CREATE TABLE service_entity (
    service_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    UNIQUE (replay_run_id, service_name),
    UNIQUE (service_id, replay_run_id)
);

CREATE TABLE service_instance (
    service_instance_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    service_id UUID NOT NULL,
    instance_name TEXT NOT NULL,
    UNIQUE (service_id, instance_name),
    UNIQUE (service_instance_id, replay_run_id),
    FOREIGN KEY (service_id, replay_run_id)
        REFERENCES service_entity(service_id, replay_run_id) ON DELETE CASCADE
);

CREATE TABLE ingest_batch (
    ingest_batch_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    payload_sha256 CHAR(64) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('accepted')),
    accepted_data_points INTEGER NOT NULL CHECK (accepted_data_points >= 0),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (replay_run_id, payload_sha256),
    UNIQUE (ingest_batch_id, replay_run_id)
);

CREATE TABLE source_metric_definition (
    source_metric_definition_id UUID PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    unit TEXT NOT NULL,
    aggregation_temporality SMALLINT NOT NULL,
    is_monotonic BOOLEAN NOT NULL,
    UNIQUE (metric_name, metric_type, unit, aggregation_temporality, is_monotonic)
);

CREATE TABLE metric_series (
    metric_series_id UUID PRIMARY KEY,
    service_instance_id UUID NOT NULL REFERENCES service_instance(service_instance_id) ON DELETE CASCADE,
    source_metric_definition_id UUID NOT NULL REFERENCES source_metric_definition(source_metric_definition_id),
    source_cmdb_id TEXT NOT NULL,
    scope_name TEXT NOT NULL DEFAULT '',
    scope_version TEXT NOT NULL DEFAULT '',
    scope_attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    normalized_attributes JSONB NOT NULL,
    series_fingerprint CHAR(64) NOT NULL,
    UNIQUE (service_instance_id, series_fingerprint),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw_metric_point (
    raw_metric_point_id BIGSERIAL PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    ingest_batch_id UUID NOT NULL,
    metric_series_id UUID NOT NULL REFERENCES metric_series(metric_series_id),
    source_timestamp_unix_nano NUMERIC(20,0) NOT NULL,
    start_time_unix_nano NUMERIC(20,0),
    value_type TEXT NOT NULL CHECK (value_type IN ('int','double')),
    value_int BIGINT,
    value_double DOUBLE PRECISION,
    source_file_sha256 CHAR(64) NOT NULL,
    source_row_ordinal BIGINT NOT NULL CHECK (source_row_ordinal > 0),
    resource_attributes JSONB NOT NULL,
    scope_attributes JSONB NOT NULL,
    datapoint_attributes JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (source_timestamp_unix_nano >= 0 AND source_timestamp_unix_nano < 18446744073709551616),
    CHECK (start_time_unix_nano IS NULL OR
           (start_time_unix_nano >= 0 AND start_time_unix_nano < 18446744073709551616)),
    CHECK ((value_type = 'int' AND value_int IS NOT NULL AND value_double IS NULL) OR
           (value_type = 'double' AND value_double IS NOT NULL AND value_int IS NULL)),
    CHECK (value_double IS NULL OR
           (value_double > '-Infinity'::double precision AND value_double < 'Infinity'::double precision)),
    UNIQUE (replay_run_id, source_file_sha256, source_row_ordinal),
    FOREIGN KEY (ingest_batch_id, replay_run_id)
        REFERENCES ingest_batch(ingest_batch_id, replay_run_id) ON DELETE CASCADE
);

CREATE TABLE ground_truth_event (
    ground_truth_event_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    service_instance_id UUID NOT NULL REFERENCES service_instance(service_instance_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type = 'injected_fault'),
    failure_type TEXT NOT NULL,
    start_unix_nano NUMERIC(20,0) NOT NULL,
    end_unix_nano NUMERIC(20,0) NOT NULL,
    source_file_sha256 CHAR(64) NOT NULL,
    source_event_ordinal BIGINT NOT NULL CHECK (source_event_ordinal > 0),
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (start_unix_nano >= 0 AND end_unix_nano > start_unix_nano),
    UNIQUE (replay_run_id, source_file_sha256, source_event_ordinal),
    FOREIGN KEY (service_instance_id, replay_run_id)
        REFERENCES service_instance(service_instance_id, replay_run_id) ON DELETE CASCADE
);

CREATE TABLE transform_run (
    transform_run_id UUID PRIMARY KEY,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running','complete','failed')),
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE (transform_run_id, replay_run_id)
);

CREATE TABLE observation_window (
    observation_window_id UUID PRIMARY KEY,
    transform_run_id UUID NOT NULL REFERENCES transform_run(transform_run_id) ON DELETE CASCADE,
    replay_run_id UUID NOT NULL REFERENCES replay_run(replay_run_id) ON DELETE CASCADE,
    service_instance_id UUID NOT NULL REFERENCES service_instance(service_instance_id) ON DELETE CASCADE,
    window_start_unix_nano NUMERIC(20,0) NOT NULL,
    window_end_unix_nano NUMERIC(20,0) NOT NULL,
    CHECK (window_start_unix_nano >= 0 AND window_end_unix_nano > window_start_unix_nano),
    UNIQUE (transform_run_id, service_instance_id, window_start_unix_nano, window_end_unix_nano),
    UNIQUE (observation_window_id, transform_run_id),
    FOREIGN KEY (transform_run_id, replay_run_id)
        REFERENCES transform_run(transform_run_id, replay_run_id) ON DELETE CASCADE,
    FOREIGN KEY (service_instance_id, replay_run_id)
        REFERENCES service_instance(service_instance_id, replay_run_id) ON DELETE CASCADE
);

CREATE TABLE derived_metric_definition (
    derived_metric_definition_id UUID PRIMARY KEY,
    metric_name TEXT NOT NULL,
    unit TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    UNIQUE (metric_name, unit)
);

CREATE TABLE metric_coverage (
    metric_coverage_id UUID PRIMARY KEY,
    transform_run_id UUID NOT NULL,
    observation_window_id UUID NOT NULL,
    derived_metric_definition_id UUID NOT NULL REFERENCES derived_metric_definition(derived_metric_definition_id),
    coverage_state TEXT NOT NULL
        CHECK (coverage_state IN ('complete','partial','missing','invalid','not_applicable')),
    reason TEXT,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (observation_window_id, transform_run_id)
        REFERENCES observation_window(observation_window_id, transform_run_id) ON DELETE CASCADE,
    UNIQUE (transform_run_id, observation_window_id, derived_metric_definition_id)
);

CREATE TABLE derived_metric_point (
    derived_metric_point_id BIGSERIAL PRIMARY KEY,
    transform_run_id UUID NOT NULL,
    observation_window_id UUID NOT NULL,
    derived_metric_definition_id UUID NOT NULL REFERENCES derived_metric_definition(derived_metric_definition_id),
    value DOUBLE PRECISION NOT NULL,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (observation_window_id, transform_run_id)
        REFERENCES observation_window(observation_window_id, transform_run_id) ON DELETE CASCADE,
    CHECK (value > '-Infinity'::double precision AND value < 'Infinity'::double precision),
    UNIQUE (transform_run_id, observation_window_id, derived_metric_definition_id)
);

CREATE TABLE derived_point_source (
    derived_metric_point_id BIGINT NOT NULL REFERENCES derived_metric_point(derived_metric_point_id) ON DELETE CASCADE,
    raw_metric_point_id BIGINT NOT NULL REFERENCES raw_metric_point(raw_metric_point_id) ON DELETE RESTRICT,
    PRIMARY KEY (derived_metric_point_id, raw_metric_point_id)
);

CREATE INDEX raw_metric_point_series_time_idx
    ON raw_metric_point(metric_series_id, source_timestamp_unix_nano);
CREATE INDEX raw_metric_point_replay_idx
    ON raw_metric_point(replay_run_id, source_timestamp_unix_nano);
CREATE INDEX metric_series_instance_idx
    ON metric_series(service_instance_id, source_metric_definition_id);
CREATE INDEX observation_window_time_idx
    ON observation_window(transform_run_id, service_instance_id, window_start_unix_nano, window_end_unix_nano);
CREATE INDEX derived_metric_point_lookup_idx
    ON derived_metric_point(transform_run_id, observation_window_id, derived_metric_definition_id);
CREATE INDEX ground_truth_event_time_idx
    ON ground_truth_event(replay_run_id, service_instance_id, start_unix_nano, end_unix_nano);
