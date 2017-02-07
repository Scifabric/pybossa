#!/bin/bash
DATABASE=your-db-name
USERNAME=your-db-username
HOSTNAME=your-db-hostname
export PGPASSWORD=your-db-password
# ignore table '' addition if it exists already
table=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT EXISTS (SELECT 1 FROM   information_schema.tables WHERE  table_schema = 'public' AND table_name = 'project_coowner');"`
echo table
if [ "$table" = "f" ]; then
   echo "'project_coowner table doesn't exist. adding 'project_coowner' table"
   # add project_coowner table
   psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -c "CREATE TABLE project_coowner (project_id integer NOT NULL,coowner_id integer NOT NULL); ALTER TABLE public.project_coowner OWNER TO pybossa; ALTER TABLE ONLY project_coowner ADD CONSTRAINT project_coowner_pkey PRIMARY KEY (project_id, coowner_id); ALTER TABLE ONLY project_coowner ADD CONSTRAINT project_coowner_coowner_id_fkey FOREIGN KEY (coowner_id) REFERENCES \"user\"(id) ON DELETE CASCADE; ALTER TABLE ONLY project_coowner ADD CONSTRAINT project_coowner_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE;"
   # check table created successfully
   table=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT EXISTS (SELECT 1 FROM   information_schema.tables WHERE  table_schema = 'public' AND table_name = 'project_coowner');"`
   if [ "$table" = "f" ]; then
      echo "error adding table 'project_coowner' to database"
      exit 1
   fi
fi
echo "'project_coowner' table exists in the database"
