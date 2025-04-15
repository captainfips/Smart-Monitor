CREATE DATABASE smart_monitor;
\c smart_monitor;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE billing_data (
 created TIMESTAMPTZ NOT NULL,
 cycle tstzrange,
 import_price REAL NOT NULL,
 export_price REAL NOT NULL,
 yearly_price REAL NOT NULL,
 EXCLUDE USING GIST (cycle WITH &&));

CREATE TABLE fronius_data (
 time TIMESTAMPTZ NOT NULL,
 energy_day BIGINT,
 energy_year BIGINT,
 energy_total BIGINT,
 ac_frequency REAL,
 ac_power REAL,
 dc_power REAL,
 dc1_current REAL,
 dc1_voltage REAL,
 dc1_power REAL,
 dc2_current REAL,
 dc2_voltage REAL,
 dc2_power REAL,
 UNIQUE (time));
SELECT create_hypertable('fronius_data', 'time');

CREATE MATERIALIZED VIEW fronius_daily
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1d', time, 'Europe/Vienna') AS day,
  max(energy_day) as energy,
  min(energy_total) as min_energy_total,
  max(energy_total) as max_energy_total,
  avg(ac_power) as ac_power,
  avg(dc_power) as dc_power,
  avg(dc1_power) as dc1_power,
  avg(dc2_power) as dc2_power,
  max(ac_power) as max_ac_power,
  max(dc_power) as max_dc_power
FROM fronius_data
GROUP BY 1
WITH NO DATA;
SELECT add_continuous_aggregate_policy('fronius_daily',
  start_offset => INTERVAL '3d',
  end_offset => INTERVAL '1d',
  schedule_interval => INTERVAL '1d',
  initial_start => date_trunc('day', now(), 'Europe/Vienna'),
  timezone => 'Europe/Vienna');
CALL refresh_continuous_aggregate('fronius_daily', NULL, date_trunc('day', now(), 'Europe/Vienna'));

CREATE TABLE iskra_data (
 time TIMESTAMPTZ NOT NULL,
 energy_in BIGINT,
 energy_out BIGINT,
 power_in BIGINT,
 power_out BIGINT,
 UNIQUE (time));
SELECT create_hypertable('iskra_data', 'time');

CREATE MATERIALIZED VIEW iskra_daily
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1d', time, 'Europe/Vienna') AS day,
  max(energy_in) as total_energy_in,
  max(energy_in) - min(energy_in) as daily_energy_in,
  -- max(energy_in) - lag(max(energy_in)) OVER (ORDER BY date_trunc('day', time, 'Europe/Vienna')) as daily_energy_in,
  max(power_in) as max_power_in,
  min(power_in) as min_power_in,
  avg(power_in) as avg_power_in,

  max(energy_out) as total_energy_out,
  max(energy_out) - min(energy_out) as daily_energy_out,
  -- max(energy_out) - lag(max(energy_out)) OVER (ORDER BY date_trunc('day', time, 'Europe/Vienna')) as daily_energy_out,
  max(power_out) as max_power_out,
  min(power_out) as min_power_out,
  avg(power_out) as avg_power_out
FROM iskra_data
GROUP BY 1
WITH NO DATA;
SELECT add_continuous_aggregate_policy('iskra_daily',
  start_offset => INTERVAL '3d',
  end_offset => INTERVAL '1d',
  schedule_interval => INTERVAL '1d',
  initial_start => date_trunc('day', now(), 'Europe/Vienna'),
  timezone => 'Europe/Vienna');
CALL refresh_continuous_aggregate('iskra_daily', NULL, date_trunc('day', now(), 'Europe/Vienna'));



CREATE TABLE eastron_data (
 time TIMESTAMPTZ NOT NULL,
 frequency REAL,
 energy_keller BIGINT,
 power_keller REAL,
 energy_erdgeschoss BIGINT,
 power_erdgeschoss REAL,
 energy_obergeschoss BIGINT,
 power_obergeschoss REAL,
 power_total_max REAL,
 UNIQUE (time));
SELECT create_hypertable('eastron_data', 'time');

CREATE MATERIALIZED VIEW eastron_daily
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1d', time, 'Europe/Vienna') AS day,
  max(energy_keller) as total_energy_keller,
  max(energy_keller) - min(energy_keller) as daily_energy_keller,
  max(power_keller) as max_power_keller,
  min(power_keller) as min_power_keller,
  avg(power_keller) as avg_power_keller,

  max(energy_erdgeschoss) as total_energy_erdgeschoss,
  max(energy_erdgeschoss) - min(energy_erdgeschoss) as daily_energy_erdgeschoss,
  max(power_erdgeschoss) as max_power_erdgeschoss,
  min(power_erdgeschoss) as min_power_erdgeschoss,
  avg(power_erdgeschoss) as avg_power_erdgeschoss,

  max(energy_obergeschoss) as total_energy_obergeschoss,
  max(energy_obergeschoss) - min(energy_obergeschoss) as daily_energy_obergeschoss,
  max(power_obergeschoss) as max_power_obergeschoss,
  min(power_obergeschoss) as min_power_obergeschoss,
  avg(power_obergeschoss) as avg_power_obergeschoss
FROM eastron_data
GROUP BY 1
WITH NO DATA;
SELECT add_continuous_aggregate_policy('eastron_daily',
  start_offset => INTERVAL '3d',
  end_offset => INTERVAL '1d',
  schedule_interval => INTERVAL '1d',
  initial_start => date_trunc('day', now(), 'Europe/Vienna'),
  timezone => 'Europe/Vienna');
CALL refresh_continuous_aggregate('eastron_daily', NULL, date_trunc('day', now(), 'Europe/Vienna'));

CREATE TABLE example_data (
 time TIMESTAMPTZ NOT NULL,
 frequency REAL,
 power_example REAL,
 energy_example BIGINT,
 UNIQUE (time));
SELECT create_hypertable('example_data', 'time');

CREATE MATERIALIZED VIEW example_daily
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1d', time, 'Europe/Vienna') AS day,
  max(energy_example) as total_energy_example,
  max(energy_example) - min(energy_example) as daily_energy_example,
  max(power_example) as max_power_example,
  min(power_example) as min_power_example,
  avg(power_example) as avg_power_example
FROM example_data
GROUP BY 1
WITH NO DATA;
SELECT add_continuous_aggregate_policy('example_daily',
  start_offset => INTERVAL '3d',
  end_offset => INTERVAL '1d',
  schedule_interval => INTERVAL '1d',
  initial_start => date_trunc('day', now(), 'Europe/Vienna'),
  timezone => 'Europe/Vienna');
CALL refresh_continuous_aggregate('example_daily', NULL, date_trunc('day', now(), 'Europe/Vienna'));

CREATE TABLE bme280_data (
 time TIMESTAMPTZ NOT NULL,
 temperature0 REAL,
 temperature1 REAL,
 humidity0 REAL,
 humidity1 REAL,
 water0 REAL GENERATED ALWAYS AS (13.2473226 * humidity0 * exp((17.67 * temperature0)/(temperature0 + 243.5)) / (273.15 + temperature0)) STORED,
 water1 REAL GENERATED ALWAYS AS (13.2473226 * humidity1 * exp((17.67 * temperature1)/(temperature1 + 243.5)) / (273.15 + temperature1)) STORED,
 UNIQUE (time));
SELECT create_hypertable('bme280_data', 'time');

-- 2244242

CREATE MATERIALIZED VIEW bme280_daily
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1d', time, 'Europe/Vienna') AS day,
  max(temperature0) as temperature0_max,
  min(temperature0) as temperature0_min,
  avg(temperature0) as temperature0_avg,

  max(temperature1) as temperature1_max,
  min(temperature1) as temperature1_min,
  avg(temperature1) as temperature1_avg,

  max(humidity0) as humidity0_max,
  min(humidity0) as humidity0_min,
  avg(humidity0) as humidity0_avg,

  max(humidity1) as humidity1_max,
  min(humidity1) as humidity1_min,
  avg(humidity1) as humidity1_avg,

  max(water0) as water0_max,
  min(water0) as water0_min,
  avg(water0) as water0_avg,

  max(water1) as water1_max,
  min(water1) as water1_min,
  avg(water1) as water1_avg
FROM bme280_data
GROUP BY 1
WITH NO DATA;
SELECT add_continuous_aggregate_policy('bme280_daily',
  start_offset => INTERVAL '3d',
  end_offset => INTERVAL '1d',
  schedule_interval => INTERVAL '1d',
  initial_start => date_trunc('day', now(), 'Europe/Vienna'),
  timezone => 'Europe/Vienna');
CALL refresh_continuous_aggregate('bme280_daily', NULL, date_trunc('day', now(), 'Europe/Vienna'));


CREATE ROLE grafana LOGIN PASSWORD 'grafana';
CREATE ROLE temperature_logger LOGIN PASSWORD 'temperature';
CREATE ROLE gas_logger LOGIN PASSWORD 'gas';
CREATE ROLE water_logger LOGIN PASSWORD 'water';

GRANT select ON billing_data TO grafana;
GRANT select ON fronius_data TO grafana;
GRANT select ON fronius_daily TO grafana;
GRANT select ON iskra_data TO grafana;
GRANT select ON iskra_daily TO grafana;
GRANT select ON eastron_data TO grafana;
GRANT select ON eastron_daily TO grafana;
GRANT select ON example_data TO grafana;
GRANT select ON example_daily TO grafana;
GRANT select ON bme280_data TO grafana;
GRANT select ON bme280_daily TO grafana;

GRANT INSERT ON bme280_data TO temperature_logger;