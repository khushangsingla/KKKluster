CREATE TYPE role_enum AS ENUM ('admin', 'guest');
CREATE TYPE status_enum AS ENUM ('waiting', 'running', 'completed');

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR,
    priority INT NOT NULL
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tasks (
    tid SERIAL PRIMARY KEY,
    id SERIAL,
    image VARCHAR NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
	FOREIGN KEY (id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS threads (
	thid SERIAL PRIMARY KEY,
	tid SERIAL,
	id SERIAL,
	retval INT,
	cmd VARCHAR,
	status status_enum DEFAULT 'waiting',
	FOREIGN KEY (tid) REFERENCES tasks(tid)
);
