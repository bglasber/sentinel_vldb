# sentinel_vldb
Public source code release of [Sentinel](http://www.vldb.org/pvldb/vol13/p2720-glasbergen.pdf).

The core Sentinel code is in src, unit tests in test. Scripts that process and compare results are
located in the main directory.

## Integrating Sentinel with PostgreSQL.

We tested Sentinel with PostgreSQL 9.6.13. Other versions of PostgreSQL will work, but you may need to modify the integration
points somewhat (See the changes we made in pg_diff.diff).

[sentinel_setup.sh](https://github.com/bglasber/sentinel_vldb/blob/main/sentinel_setup.sh) will download PostgreSQL 9.6.13 and apply the integration patch (pg_diff.diff). It will also install Sentinel. The default installation directories for Sentinel and PostgreSQL libraries are /usr/local/lib and /usr/local/include.

After running this script, you can just run PostgreSQL as normal. The default config we used is (here)[https://github.com/bglasber/sentinel_vldb/blob/main/sentinel_postgresql.conf].

## Obtaining and Comparing Results

After you run an experiment against PostgreSQL, shut it down (/usr/local/pgsql/bin/pg_ctl -D ... stop). Once PostgreSQL stops, Sentinel will dump all of its tracing to /tmp.

From /tmp, run (merge_files.py)[(here)[https://github.com/bglasber/sentinel_vldb/blob/main/merge_files.py] to combine the reservoirs of transition times. Afterward, use (create_sql_stmts)[https://github.com/bglasber/sentinel_vldb/blob/main/create_sql_stmts.py] to create SQL statements of data from the experiment. 


