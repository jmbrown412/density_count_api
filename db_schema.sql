CREATE TABLE doorway (
	id INTEGER NOT NULL,
	created_date DATETIME,
	space_id INTEGER,
	installation_id INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(space_id) REFERENCES space (id),
	FOREIGN KEY(installation_id) REFERENCES installation (id)
)

CREATE TABLE dpu (
	id INTEGER NOT NULL,
	created_date DATETIME,
	PRIMARY KEY (id)
)

CREATE TABLE installation (
	id INTEGER NOT NULL,
	active BOOLEAN,
	created_date DATETIME,
	updated_date DATETIME,
	doorway_id INTEGER,
	dpu_id INTEGER,
	PRIMARY KEY (id),
	CHECK (active IN (0, 1)),
	FOREIGN KEY(doorway_id) REFERENCES doorway (id),
	FOREIGN KEY(dpu_id) REFERENCES dpu (id)
)

CREATE TABLE installation_count (
	id INTEGER NOT NULL,
	created_date DATETIME,
	dpu_event_time DATETIME,
	installation_id INTEGER,
	count INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(installation_id) REFERENCES installation (id)
)

CREATE TABLE space (
	id INTEGER NOT NULL, 
	created_date DATETIME, 
	PRIMARY KEY (id)
)
