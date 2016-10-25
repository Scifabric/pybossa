#!/bin/bash
DATABASE=your-db-name
USERNAME=your-db-username
HOSTNAME=your-db-hostname
export PGPASSWORD=your-db-password
# ignore column 'subadmin' addition if it exist in 'user' table
column_name=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT column_name FROM information_schema.columns WHERE table_name='user' and column_name='subadmin';"`
if [ -z "$column_name" ]; then
   echo "'subadmin' column doesnt exist. adding 'subadmin' column to 'user' table"
   # add subadmin column
   psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -c "ALTER TABLE public.user ADD COLUMN subadmin BOOLEAN DEFAULT FALSE;"
   # check column created successfully
   column_name=`psql --host $HOSTNAME --user $USERNAME --dbname $DATABASE -Atc "SELECT column_name FROM information_schema.columns WHERE table_name='user' and column_name='subadmin';"`
   if [ -z "$column_name" ]; then
      echo "error adding column 'subadmin' to table 'user'"
      exit 1
   fi
fi
echo "'subadmin' column exist in 'user' table"
