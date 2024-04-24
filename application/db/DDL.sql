CREATE TYPE role_enum AS ENUM ('admin', 'guest');

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR,
    priority INT NOT NULL
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tasks (
    tid SERIAL,
    id SERIAL,
    cmd VARCHAR NOT NULL,
    image VARCHAR NOT NULL,
    completed BOOLEAN NOT NULL,
	FOREIGN KEY (id) REFERENCES users(id)
);
