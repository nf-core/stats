use nf_core_stats_bot;

select timestamp, followers_count from twitter.account_stats
where timestamp < epoch(TIMESTAMP '2023-04-28 00:00:00');
