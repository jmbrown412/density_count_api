# Density Count API 

CONTENTS OF THIS FILE
---------------------
 * Introduction
 * Business Entities
 * Data Model
 * API
 * Creating Test Data
 * Production Technologies
 
INTRODUCTION
------------
Density Count API provides real-time and historical counts by Depth processing units (DPU) in specific Spaces. 
This project was based off of https://github.com/DensityCo/api-homework.

Density Count API receives information from DPUs when a person enters a space or leaves a space through a doorway.
A person entering a room is counted by saving a "+1" in the database and a person leaving a room is measured by
saving a "-1" in the database. This API provides the number of people in a Space (right now) or at specific time
in history (i.e. July 4th 2020 12:12 PM)

BUSINESS ENTITIES
----------------
The following entities exist to the business:
* DPU - Device counting people entering a space (+1) and leaving a space (-1).
* Doorway - Location in a Space where people enter and exit.
* Space - Locations which can have multiple Doorways.

DATA MODEL
-----------------
This project uses SQLite for the Database.
I used a code first approach for creating the tables.
Additionally, db_schema.sql is included to reflect the create statements for creating the tables.

Data considerations:
* DPUs are sometimes moved from one doorway to another. *Solved with Installations* 
* DPUs don't always send data up in real-time. Network downtime and other events can cause delayed events. *"dpu_event_time" in Api request*
* All times stored in UTC. *Timezone info needs to be stored also for conversions.*

Data Tables:
* Space - A location which can have many Doorways where people can enter and leave.
* Doorway - A portal in and out of a Space.
* Dpu - A device for counting people entering and leaving a Space.
* Installation - Because DPUs can be moved to other Doorways, an Installation is required to create a unique relationship
between a Doorway and a DPU. *A Doorway should only be allowed to have one active Installation at a time. *
* InstallationCount - Used to track people entering and leaving a Doorway for a specific Installation.

API
-----------------
API Considerations:
* DPUs sometimes send events out of order.
* DPUs don't always send data up in real-time. Network downtime and other events can cause delayed events.
* All times sent in UTC. *Timezone info needs to be stored also for conversions.*

To address the first two, the endpoint for the DPUs to send their count information should include a field "dpu_event_time"
and the api should create a field "event_received_time" and store these in the InstallationCount table. Doing so
allows the data to reflect the time the event happened on the device and the time the API received the event.

The main endpoint in this project is /spaces/{id} which can return real-time (count right now!) or historical counts 
(count for a space yesterday at 4:33 PM).

Real Time Counts - Simply call /spaces/{id} to get a Space object back including the count right now
Historical Counts - Call /spaces/{id}?time=<time> *time format = YYYY-MM-DD HH:MM i.e. '2020-06-23 20:21'*

CREATING TEST DATA
----------------------
Use the method 'seed_data' to create essential data for developing and testing with.

PRODUCTION TECHNOLOGIES
----------------------
This is just an MVP to demonstrate how data would be retrieved and there is no implementation in the API for inserting 
new count data. Let's talk about what technologies would be used in a Prod setting for both handling things like 100K DPUs
and things in general.

Add authentication/authorization to the API.

I would design this using a Producer - Consumer model. https://en.wikipedia.org/wiki/Producer%E2%80%93consumer_problem

Producing counts: Count information would be sent via a PUT endpoint like /dpus/{id} which would put the count information
into a common place so that it could be processed at scale by a Consumer.


Potential data solutions:
* Simple DB table
* Kafka
* AWS Kinesis
* AWS SQS

Consuming counts: The consumers responsibility is to pick up new count events from the common source and perform the business logic on the event
and ultimately getting the data into the source of truth for the system. In this case, the source of truth is the SQLite
database which is used to return count information.

Potential consumer solutions:
* Apache Flink (https://flink.apache.org/) connected to specific stream of incoming data.
* Simple cloud scheduler (AWS lambda, cron job, etc...) to pick up from stream.

Together, the Producer and Consumer provide a scalable solution for processing large amounts of DPU events being sent to the API.

As the data grows, queries will become slower. It is important to apply proper indexes for performant queries
as well as creating a cache between the application and the data store because taking load off of the DB will greatly improve the performance
of the queries against the DB. I'd recommend cacheing data in either memory, something like Redis and/or both.





