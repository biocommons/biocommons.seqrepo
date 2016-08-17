from yoyo import step

step("""
create table seqalias (
    seqalias_id integer primary key,
    seq_id text not null,
    namespace text not null,
    alias text not null,
    added timestamp not null default current_timestamp,
    is_current int not null default 1
)""", """drop table seqalias""")

# current alias must be unique with a namespace
step("""
create unique index seqalias_unique_ns_alias_idx on seqalias(namespace, alias) where is_current = 1
""")

step("""
create index seqalias_seq_id_idx on seqalias(seq_id)
""")

step("""
create index seqalias_namespace_idx on seqalias(namespace)
""")

step("""
create index seqalias_alias_idx on seqalias(alias)
""")

step("""
update meta set value = '1' where key = 'schema version'
""")
