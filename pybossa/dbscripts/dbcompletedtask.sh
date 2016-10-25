#!/bin/bash
DATABASE=your-db-name
USERNAME=your-db-username
HOSTNAME=your-db-hostname
export PGPASSWORD=your-db-password
# ignore column 'exported' addition if it exist in 'task' table
column_name=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT column_name FROM information_schema.columns WHERE table_name='task' and column_name='exported';"`
if [ -z "$column_name" ]; then
   echo "'exported' column doesnt exist. adding 'exported' column to 'task' table"
   # add subadmin column
   psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -c "ALTER TABLE task ADD COLUMN exported BOOLEAN DEFAULT FALSE;"
   # check oolumn created successfully
   column_name=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT column_name FROM information_schema.columns WHERE table_name='task' and column_name='exported';"`
   if [ -z "$column_name" ]; then
      echo "error adding column 'exported' to table 'task'"
      exit 1
   fi
fi
echo "'exported' column exist in 'task' table"
