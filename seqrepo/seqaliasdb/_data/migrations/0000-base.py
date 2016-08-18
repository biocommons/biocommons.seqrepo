from yoyo import step

step("""create table meta (key text not null, value text not null)""", """drop table meta""")

step("""create unique index meta_key_idx on meta(key)""", """drop index meta_key_idx""")

step("""create table log (ts timestamp not null default current_timestamp, v text not null, msg text not null);""",
     """drop table log""")

step("""insert into log (v,msg) values ('', 'database created')""")

step("""insert into meta (key, value) values ('schema version', '0')""")
