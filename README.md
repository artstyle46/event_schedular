# event_schedular

This is a lightweight event schedular for benchmarking scheduling of large number of events using redis (for storing modified data view), celery(for task scheduling) and PSQL (for storing actual data). We will also use django framework for maintaining migrations and creating tables.

Database relations and schema

1. Table Name: field_value
  fields: 1. id
          2. NUllable<date_field> (random date time field with value from today and tomorrow.)
          3. string_field: (random string)
          5. field_id
          
2. Table Name: Trigger
  fields: 1. id
          2. field_id
          3. time
          4. period
          5. offset_type
          6. date_offset
 
 3. Table Name: Contact
   user model from django
   
 4. Table Name: Field
    fields: 1. id
            2. field_type: (string/date)
            3. is_active: bool
            
            
for Populating the data into database,use command: python manage.py populate.
