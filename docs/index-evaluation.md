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
