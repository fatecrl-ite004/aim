CREATE TABLE demo_run (
    demo_run_id UUID PRIMARY KEY,
    idempotency_key UUID NOT NULL UNIQUE,
    replay_run_id UUID REFERENCES replay_run(replay_run_id),
    status TEXT NOT NULL CHECK (status IN ('queued','running','completed','failed')),
    progress JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_code TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX demo_run_single_active_idx ON demo_run ((true))
    WHERE status IN ('queued','running');
CREATE INDEX demo_run_created_idx ON demo_run(created_at DESC);
