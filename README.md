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
  - [X] TSL2561 light level sensor
  - [ ] Others? (e.g. ir motion sensors)
- [X] Develop way to determine occupancy status from sensors
- [X] Build a low-energy monitoring script that can:
  - [X] respond to occupancy status requests (slack app websocket implementation)
  - [X] manage usage requests on a queue, notify users when room becomes free
  - [ ] log occupancy statistics

