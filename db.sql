CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER,
  likes INTEGER,
  author INTEGER,
  message TEXT,
  published BOOLEAN,
  got_likes BOOLEAN,
  publish_at INTEGER
);

CREATE TABLE attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_owner_id INTEGER,
  src_document_id INTEGER,
  type TEXT,
  owner_id INTEGER,
  document_id INTEGER
);

CREATE TABLE post_attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER,
  attachment_id INTEGER
);