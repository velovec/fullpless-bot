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

CREATE TABLE videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER,
  video_id INTEGER
);

CREATE TABLE documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_owner_id INTEGER,
  src_document_id INTEGER,
  owner_id INTEGER,
  document_id INTEGER
);

CREATE TABLE post_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER,
  document_id INTEGER
);

CREATE TABLE post_videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER,
  video_id INTEGER
);