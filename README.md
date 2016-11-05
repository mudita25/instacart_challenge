## Instacart Shopper Challenge
This challenge is broken into two parts. The first part is implementing the public-facing site that a prospective Instacart Shopper would see when hearing about the opportunities that Instacart offers. The second is writing analytics to monitor the progress of shoppers through the hiring funnel.

## Technical Stack
1. Programming Language - Python (Ver - 2.7.11)
2. Application Server   - Django (Ver - 1.10.2)
3. Database             - SQLite

Django is a open-source, high-level Python Web framework that encourages rapid development and clean, pragmatic design. Django is a good MVC framework for developing CRUD centric web applications.

Django comes with default support for SQLite DB which is used in developing this application. But it can be easily ported to any other database (Postgres, MySQL, Oracle) supported by Django's ORM layer. 

Django ORM also provides support for running DB migrations which is really helpful while developing web application and performing incremental db changes. Migrations for this application can be found here - 'https://github.com/mudita25/instacart_challenge/tree/master/instacart_shopper/instacart_shopper/migrations'.

This application is developed and tested with Python 2.7.11 and Django 1.10.2

## Running the Application

To run the application locally, clone this repository and run the following commands from project dir - instacart_shopper:

Apply db migrations:

`python manage.py migrate`

Run django server:

`python manage.py runserver`

This will start the django server on port 8000. The landing page of the application can then be accessed at the URL:

`http://localhost:8000/instacart_shopper/`

## Web APIs
### Shopper Registration and Application tracking
#### http://localhost:8000/instacart_shopper/
   * Allows the user to submit a fresh application by providing details or track an existing application by email.
   * Performs validations such as:
    * Malformed email or phone number
    * If the user's email or phone number is already registered while applying a new application.
    * If the user's email is not registered while tracking application.
   * User sessions are managed based on email using Django's session support.
   * Backend validation errors are communicated via Django's message support.

### Hiring funnel analytics
#### http://localhost:8000/instacart_shopper/funnel.json?start_date=START_DATE&end_date=END_DATE
   * This API generated the hiring funnel report between most recent Monday <= START_DATE and most closest Sunday >= END_DATE.
   * The funnel report is grouped by week (Monday to Sunday). 
   * The funnel report is generated in chronological order of dates.
   * API performs validations and the errors are communicated to user properly. Example validations:
     * Input parameters (START_DATE, END_DATE) should always be provided.
     * START_DATE should not be after END_DATE
   * Example:   
      `http://localhost:8000/instacart_shopper/funnel.json?start_date=2012-01-01&end_date=2012-12-31`

### Inserting seed data for testing funnel analytics
#### http://localhost:8000/instacart_shopper/seed_data/COUNT/
   * This API populates the database with COUNT random dummy shopper applicants.
   * Example: 
      `http://localhost:8000/instacart_shopper/seed_data/10000/`    

### Django Admin API
#### http://localhost:8000/admin/instacart_shopper/shopper/
   * Username : admin, Password : instacart 

## Performance and Scalability
The following design choices have helped scale this application:
   * **In-memory cache**
    
    Since the funnel API requires to read data from DB and group it by week, it is a very good candidate for in-memory caching. This helps speed-up the API greatly. Week range (Monday-Sunday) serves as cache key.
    
    This application is currently using a **Local in-memory cache**. In current implementation, whenever a new user registers in the system, we invalidate the cache for current week as the current week funnel stats have become stale now. Cache eviction has been set to 600s (5 mins). The cache is loaded lazily and on-demand from DB with the first call and subsequesnt requests for same week stats within 5 mins are served from cache. We do not want to grow our cache indefinitely, so we have set a max limit of 1000 entries in the cache. The cache config is located here: `https://github.com/mudita25/instacart_challenge/blob/master/instacart_shopper/instacart/settings.py#L84`
    
    If the number of entries to be cached is very high, then local-memory caching used for development purpose might not 
    suffice the performance requirements. In such a case, using a distributed cache like **Memcached** or **Redis** will be better. 

   * **Databse Indexing and partitioning**
    
    Since the funnel queries are date-range based, a B-Tree index on application_date column helps run the query very efficiently and speeds up the funnel analytics API. 
    If the data grows heavily, we can also do a date/ week-range based partitioning for the table.

   * This web application is currently running on the default development server provided by Django. Instead NGINX or other web servers can be used to handle production traffic.
   
## Screenshots
Screenshots for the various web application states and API's have been hosted here : https://github.com/mudita25/instacart_challenge/screenshots/

## TODO
1. Improve upon UI/ UX.
2. Add user authentication/ authorization.
3. Add unit tests.
