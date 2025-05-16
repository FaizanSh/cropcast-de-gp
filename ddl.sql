-- public.farm_metrics definition

-- Drop table

-- DROP TABLE public.farm_metrics;

CREATE TABLE public.farm_metrics (
	stream_id text DEFAULT 'unknown'::text NOT NULL,
	batch_id int8 NOT NULL,
	avg_rainfall float8 NOT NULL,
	avg_sunlight_hours float8 NOT NULL,
	total_fertilizer int4 NOT NULL,
	soil_quality_index int4 NOT NULL,
	farm_size_hectares float8 NOT NULL,
	predicted_yield float8 DEFAULT 0 NOT NULL,
	records_count int4 DEFAULT 0 NOT NULL,
	processed_at timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL,
	is_processed bool DEFAULT false NOT NULL,
	CONSTRAINT farm_metrics_pkey PRIMARY KEY (stream_id, batch_id)
);
CREATE INDEX idx_farm_metrics_processed_at ON public.farm_metrics USING btree (processed_at DESC);

-- public.weather_history definition

-- Drop table

-- DROP TABLE public.weather_history;

CREATE TABLE public.weather_history (
	"timestamp" timestamp NOT NULL,
	temperature float8 NULL,
	windspeed float8 NULL,
	rain float8 NULL,
	CONSTRAINT weather_history_pkey PRIMARY KEY ("timestamp")
);