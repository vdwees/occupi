# Occupi
Room occupancy monitoring based on Raspberry Pi

## Project Objectives
- Create deployable raspberry pi systems that can detect room occupancy
- Have each system provide a way to request occupancy statistics
  and in particular current status of the room.
- Expose a way to request that a particular Pi notify you when a room
  becomes free, and keep requests on a queue. For instance, when a group
  of people have to share a single washroom.

## Stretch Goals
- Pi's monitor each other for resiliency
- Made data accessible to support security or energy auditing

## Tasklist
- Build easy-to-use api classes for supported sensors
  - [X] TSL2561 occupancy sensor
- [ ] Develop way to determine occupancy status from sensors
- [ ] Build a low-energy monitoring script that can respond to occupancy 
  status requests and log occupancy statistics

