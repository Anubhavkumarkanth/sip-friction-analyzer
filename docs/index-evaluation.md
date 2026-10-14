# Index evaluation: simulations(user_id, created_at DESC)

Query: the history endpoint's access pattern -- one user's simulations, newest first.
Table: 20,000 synthetic simulation rows across 200 users (test data, not real usage).
Captured on PostgreSQL 17.11. Both plans below are verbatim output.

## BEFORE (index dropped)
```
Sort  (cost=520.32..520.57 rows=100 width=76) (actual time=1.714..1.718 rows=100 loops=1)
  Sort Key: created_at DESC
  Sort Method: quicksort  Memory: 34kB
  Buffers: shared hit=270
  ->  Seq Scan on simulations  (cost=0.00..517.00 rows=100 width=76) (actual time=0.017..1.674 rows=100 loops=1)
        Filter: (user_id = 42)
        Rows Removed by Filter: 19900
        Buffers: shared hit=267
Planning:
  Buffers: shared hit=120
Planning Time: 1.716 ms
Execution Time: 1.798 ms
```

## AFTER (composite index created)
```
Sort  (cost=205.76..206.01 rows=100 width=76) (actual time=0.346..0.349 rows=100 loops=1)
  Sort Key: created_at DESC
  Sort Method: quicksort  Memory: 34kB
  Buffers: shared hit=103 read=2
  ->  Bitmap Heap Scan on simulations  (cost=5.06..202.43 rows=100 width=76) (actual time=0.061..0.307 rows=100 loops=1)
        Recheck Cond: (user_id = 42)
        Heap Blocks: exact=100
        Buffers: shared hit=100 read=2
        ->  Bitmap Index Scan on ix_simulations_user_created  (cost=0.00..5.04 rows=100 width=0) (actual time=0.043..0.043 rows=100 loops=1)
              Index Cond: (user_id = 42)
              Buffers: shared read=2
Planning:
  Buffers: shared hit=138 read=1
Planning Time: 2.374 ms
Execution Time: 0.473 ms
```

## What actually changed

| | Before | After |
|---|---|---|
| Access method | Seq Scan | Bitmap Index Scan → Bitmap Heap Scan |
| Rows discarded by the filter | 19,900 | 0 |
| Buffers touched | 270 | 105 |
| Execution time | 1.798 ms | 0.473 ms |

**The sort was not eliminated, and that is the interesting part.** The index is declared
`(user_id, created_at DESC)`, so it is tempting to assume PostgreSQL can read the rows out
of it already ordered and skip the sort entirely. It did not: both plans still contain a
`Sort` node.

The reason is the access method it chose. A **Bitmap** Index Scan collects matching row
locations into a bitmap and then visits the heap in physical page order, which is efficient
for many scattered rows but destroys index ordering. Only a plain Index Scan preserves it.
With 100 matching rows spread across 100 heap pages, the planner judged the bitmap approach
cheaper than an ordered index walk, and accepted the sort as the price.

So the index earned its place by **eliminating the 19,900-row filter**, not by removing the
sort — buffers touched dropped from 270 to 105.

**On the timings:** 1.8 ms to 0.5 ms is real but small in absolute terms, and this is 20,000
synthetic rows, not production traffic. The honest claim is that the index changed the access
method and cut the work measurably at this scale — not that it produced a dramatic speedup.

## Re-measuring it

The two plans above are single captures. `scripts/benchmark_history_index.py` rebuilds a seeded
data set (20,000 simulations, about 27,900 events, 200 users) and repeats every measurement, so the
result can be checked instead of taken on trust:

```bash
createdb sip_bench
python scripts/benchmark_history_index.py --database-url postgresql+psycopg2://user@localhost:5432/sip_bench
```

The database name has to end in `_bench`, because the script empties the `users` and `simulations`
tables before seeding.

Two queries are measured. *Simplified* is the one described at the top of this page: one user's runs,
newest first. *Endpoint* is what `GET /simulations` really runs: the same filter plus the
`LEFT JOIN` on `simulation_events`, `GROUP BY` and `LIMIT 20`.

Median execution time over 60 runs after warm-up, PostgreSQL 17.11 on Windows 11, user 42 (106 runs):

| Query | Without index | With index | Plan with the index |
|---|---|---|---|
| Simplified | 0.80 ms | 0.06 ms | Bitmap Index Scan on `ix_simulations_user_created` |
| Endpoint | 3.84 ms | 2.83 ms | the same index scan, then a hash join against all of `simulation_events` |

A second run (40 repetitions) gave 0.86 → 0.06 ms and 3.87 → 2.92 ms, and a third run of the committed
script (60 repetitions) gave 0.71 → 0.06 ms and 3.69 → 2.83 ms. The fastest runs were within about 10%
of the medians.

What this does and does not show:

- **The access-method change reproduces.** Without the index the planner scans every row of
  `simulations`; with it, it reads only the 106 rows that belong to the user. The simplified query
  gets roughly 13 times faster when the cache is warm. The 1.80 → 0.47 ms above is a single
  capture taken on a cold-ish cache (note `read=2` in the "after" plan), so the exact figures move
  with the machine and the cache state. The change of plan does not.
- **The whole endpoint improves far less.** At this size the planner still scans all of
  `simulation_events` and hash-joins it, so the index helps only the `simulations` side and the
  endpoint gets about 1.3 to 1.4 times faster across the three runs, not 4 times. Saying "the
  history endpoint is faster" would be accurate; saying "the history query is an order of magnitude
  faster" would not be.
- Everything here is synthetic data on one machine. It says nothing about production load, and a
  much larger events table would change the join strategy, and with it these numbers.
