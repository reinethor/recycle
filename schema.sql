create table user (
  uidd integer primary key autoincrement,
  username text not null,
  email text not null,
  pw_hash text not null,
  day integer not null
);
