from yoyo import step

step("""
create table seqinfo (
    seq_id text primary key,
    len integer not null,
    alpha text not null,
    added timestamp not null default current_timestamp,
    relpath text not null
)""", """drop table seqinfo""")

step("""create unique index seqinfo_seq_id_idx on seqinfo(seq_id)""")

step("""update meta set value = '1' where key = 'schema version'""")
