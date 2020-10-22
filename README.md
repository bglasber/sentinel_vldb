# sentinel_vldb
Public source code release of [Sentinel](http://www.vldb.org/pvldb/vol13/p2720-glasbergen.pdf).

The core Sentinel code is in src, unit tests in test. Scripts that process and compare results are
located in the main directory.

## Integrating Sentinel with PostgreSQL

We tested Sentinel with PostgreSQL 9.6.13. Other versions of PostgreSQL will work, but you may need to modify the integration
points somewhat (See the changes we made in pg_diff.diff).

[sentinel_setup.sh](https://github.com/bglasber/sentinel_vldb/blob/main/sentinel_setup.sh) will download PostgreSQL 9.6.13 and apply the integration patch (pg_diff.diff). It will also install Sentinel. The default installation directories for Sentinel and PostgreSQL libraries are /usr/local/lib and /usr/local/include.

After running this script, you can just run PostgreSQL as normal. The default config we used is [here](https://github.com/bglasber/sentinel_vldb/blob/main/sentinel_postgresql.conf).

## Obtaining and Comparing Results

After you run an experiment against PostgreSQL, shut it down (/usr/local/pgsql/bin/pg_ctl -D ... stop). Once PostgreSQL stops, Sentinel will dump all of its tracing to /tmp.

From /tmp, run [merge_files.py](https://github.com/bglasber/sentinel_vldb/blob/main/merge_files.py) to combine the reservoirs of transition times. Afterward, use [create_sql_stmts.py](https://github.com/bglasber/sentinel_vldb/blob/main/create_sql_stmts.py) to create SQL statements of data from the experiment. Load the SQL data into a PostgreSQL database and then use [compute_top_sent_diffs.py](https://github.com/bglasber/sentinel_vldb/blob/main/compute_top_sent_diffs.py) to determine the differences in behaviour between experiments.

Example:

```
$ /usr/local/pgsql/bin/pg_ctl -D pg_tpcw_50g/ -l pg_tpcw_50g/pg.log stop
$ cd /tmp
$ ls *out
23965.23965.0.im.out  23968.23968.0.im.out  23971.23971.0.im.out  24070.24070.0.im.out  24073.24073.0.im.out  24076.24076.0.im.out  24106.24106.0.im.out  24167.24167.0.im.out
23966.23966.0.im.out  23969.23969.0.im.out  24067.24067.0.im.out  24071.24071.0.im.out  24074.24074.0.im.out  24077.24077.0.im.out  24140.24140.0.im.out  24170.24170.0.im.out
23967.23967.0.im.out  23970.23970.0.im.out  24069.24069.0.im.out  24072.24072.0.im.out  24075.24075.0.im.out  24093.24093.0.im.out  24154.24154.0.im.out
$ python3 path_to_merge_files/merge_files.py .
$ cd path_to_scripts
$ python3 parse_im_dumps.py > out_lines.txt
$ python3 create_sql_stmts.py 0 > sql_stmts.0.sql # experiment ID 0

# Before the next line, create sentdb on the dbhost you want.
$ /usr/local/pgsql/bin/psql -h dbhost -U postgres sentdb < sent_schema.sql
$ /usr/local/pgsql/bin/psql -h dbhost -U postgres sentdb < sql_stmts.0.sql # Load in results from experiment 0.

# Repeat the above process to for other workloads/configs you want to compare.

$ python3 compute_top_sent_diffs.py -r dbhost -d sentdb -u postgres 0 1 # Compare behaviour from experiments 0 and 1.
```

## Interpreting Sentinel Output

A behavioural comparison using compute_top_sent_diffs.py looks like this:
```
Aggregate Difference: 3.7153566997614763e-09
============================================================
Top 10 Event Probability Differences:
Ratio           Left Prob       Right Prob     Location            
------------------------------------------------------------
4.465029        0.000000        0.000000        xlog.c:8490         
4.465029        0.000000        0.000000        xlog.c:8711         
4.465029        0.000000        0.000000        slot.c:883          
4.465029        0.000000        0.000000        xlog.c:3729         
3.606370        0.000000        0.000000        slru.c:1389         
2.426262        0.000000        0.000000        xlog.c:3875         
2.060783        0.000000        0.000000        slru.c:1244         
1.227370        0.000027        0.000033        md.c:816            
1.227370        0.000027        0.000033        bufmgr.c:2778       
1.227370        0.000027        0.000033        md.c:839            
============================================================
Top 10 Event Transition Differences:
Ratio           Left Prob       Right Prob      Transition          
------------------------------------------------------------
7.499999999999997       0.0666666666666667      0.5             xlog.c:3875 -> slru.c:1389
7.317650312705967       1.16552425863916e-06    8.52889895569724e-06    postgres.c:1494 -> bufmgr.c:726
5.037070592676494       5.99556328317045e-05    0.000302000755001888    bufmgr.c:2778 -> xlog.c:3729
4.33333333333333        0.333333333333333       0.0769230769230769      xlog.c:8711 -> xlog.c:8095
4.33333333333333        0.333333333333333       0.0769230769230769      xlog.c:8711 -> ipc.c:229
4.33333333333333        0.333333333333333       0.0769230769230769      slot.c:883 -> xlog.c:3729
2.888888888888887       0.666666666666667       0.230769230769231       xlog.c:3729 -> slru.c:1389
2.800000000000002       0.933333333333333       0.333333333333333       xlog.c:3875 -> xlog.c:3875
2.538461538461541       0.333333333333333       0.846153846153846       xlog.c:8711 -> xlog.c:8490
2.4561403508771935      0.15            0.368421052631579       postmaster.c:3553 -> postmaster.c:3553

Top EMD Differences:

(29529.10745678152, 'bufmgr.c', '2778', 'bufmgr.c', '2698')
(27719.987192121614, 'lock.c', '1024', 'lock.c', '1033')
(3561.049653981198, 'postgres.c', '2471', 'xact.c', '2088')
(2099.5328726746047, 'md.c', '740', 'md.c', '763')
(82.912571578159, 'xact.c', '2088', 'postgres.c', '1236')
(62.85870998029976, 'tuplesort.c', '1173', 'pquery.c', '724')
(34.399446900000044, 'bufmgr.c', '726', 'bufmgr.c', '963')
(21.700570422398968, 'bufmgr.c', '774', 'postgres.c', '844')
(20.7163880985649, 'bufmgr.c', '774', 'bufmgr.c', '726')
(8.37500384115645, 'postgres.c', '2471', 'postgres.c', '1236')
```

Ratio indicates the ratio difference in event frequency/transition probability while EMD differences are the total earth-mover's distance in CDFs built for a particular transition across two experiments. The "Left Prob" is the probability from the first experiment ID you specify on the command line (here 0), "Right Prob" is the value for the second experiment ID (here 1). Each category reports the top differences. Normally, the each line is also highlighted red or blue indicating whether the second experiment had a greater value (Red = Right is the mnemonic), or the first (i.e., left) did (Blue colour). Aggregate difference is a single score that indicates "how different" the two experiment's behaviour was.

As an example, the above results come from comparing a 5 minute TPC-W experiment with checkpoint timeout set to 5 minutes vs. checkpoint interval set to 30 seconds. The top event frequency difference is on xlog.c:8490. Consulting the PostgreSQL source code shows that this line corresponds to checkpoint start. The other top messages also relate to WAL checkpointing.

## Other Info

The web-based UI is built on a tempate that has a restrictive license, so I cannot distribute it. However, I can provide Javascript snippets that we developed to render the graphs or figures shown in our demo upon request.

If there is other code not shown here that would help you, or you are having trouble setting up Sentinel, please send me an email!
