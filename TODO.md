# 🚀 SpaceTradersMCP API Endpoint Tooling Checklist

## API Source
- [x] Reference: [SpaceTraders OpenAPI Spec](https://spacetraders.io/openapi)
- [x] Tooling based on OpenAPI schema (curl examples, endpoint definitions, request/response schemas)

---

## Agents
- [x] GET /agent - Get Agent (View_Agent_Details)
- [x] GET /agents - List Agents (List_Agents)
- [x] GET /agents/{agentSymbol} - Get Public Agent

## Contracts
- [x] GET /contracts - List Contracts (List_Contracts)
- [x] GET /contracts/{contractId} - Get Contract (Get_Contract)
- [x] POST /contracts/{contractId}/accept - Accept Contract (Accept_Contract)
- [x] POST /contracts/{contractId}/deliver - Deliver Cargo to Contract (Deliver_Contract_Cargo)
- [x] POST /contracts/{contractId}/fulfill - Fulfill Contract (Fulfill_Contract)

## Factions
- [x] GET /factions - List Factions (List_Factions)
- [x] GET /factions/{factionSymbol} - Get Faction (Get_Faction)

## Fleet
- [x] GET /my/ships - List Ships (List_Ships)
- [x] POST /my/ships - Purchase Ship (Purchase_Ship)
- [x] GET /my/ships/{shipSymbol} - Get Ship (View_Ship_Details)
- [x] GET /my/ships/{shipSymbol}/cargo - Get Ship Cargo (View_Ship_Cargo)
- [x] POST /my/ships/{shipSymbol}/orbit - Orbit Ship (Orbit_Ship)
- [x] POST /my/ships/{shipSymbol}/refine - Ship Refine (Refine_Ship)
- [x] POST /my/ships/{shipSymbol}/chart - Create Chart (Chart_Waypoint)
- [x] GET /my/ships/{shipSymbol}/cooldown - Get Ship Cooldown (Get_Ship_Cooldown)
- [x] POST /my/ships/{shipSymbol}/dock - Dock Ship (Dock_Ship)
- [x] POST /my/ships/{shipSymbol}/survey - Create Survey (Create_Survey, verified)
- [x] POST /my/ships/{shipSymbol}/extract - Extract Resources (Extract_Resources)
- [ ] POST /my/ships/{shipSymbol}/siphon - Siphon Resources
- [ ] POST /my/ships/{shipSymbol}/extract/survey - Extract Resources with Survey
- [x] POST /my/ships/{shipSymbol}/jettison - Jettison Cargo (Jettison_Cargo)
- [ ] POST /my/ships/{shipSymbol}/jump - Jump Ship
- [x] POST /my/ships/{shipSymbol}/navigate - Navigate Ship (Navigate_Ship)
- [ ] PATCH /my/ships/{shipSymbol}/nav - Patch Ship Nav
- [ ] GET /my/ships/{shipSymbol}/nav - Get Ship Nav
- [ ] POST /my/ships/{shipSymbol}/warp - Warp Ship
- [x] POST /my/ships/{shipSymbol}/sell - Sell Cargo (Sell_Cargo)
- [x] POST /my/ships/{shipSymbol}/scan/systems - Scan Systems (Scan_Systems)
- [x] POST /my/ships/{shipSymbol}/scan/waypoints - Scan Waypoints (Scan_Waypoints)
- [x] POST /my/ships/{shipSymbol}/scan/ships - Scan Ships (Scan_Ships)
- [x] POST /my/ships/{shipSymbol}/refuel - Refuel Ship (Refuel_Ship)
- [ ] POST /my/ships/{shipSymbol}/purchase - Purchase Cargo
- [x] POST /my/ships/{shipSymbol}/transfer - Transfer Cargo (Transfer_Cargo)
- [x] POST /my/ships/{shipSymbol}/negotiate/contract - Negotiate Contract (Negotiate_Contract)
- [ ] GET /my/ships/{shipSymbol}/mounts - Get Mounts
- [ ] POST /my/ships/{shipSymbol}/mounts/install - Install Mount
- [ ] POST /my/ships/{shipSymbol}/mounts/remove - Remove Mount
- [ ] GET /my/ships/{shipSymbol}/scrap - Get Scrap Ship
- [ ] POST /my/ships/{shipSymbol}/scrap - Scrap Ship
- [ ] GET /my/ships/{shipSymbol}/repair - Get Repair Ship
- [ ] POST /my/ships/{shipSymbol}/repair - Repair Ship
- [ ] GET /my/ships/{shipSymbol}/modules - Get Ship Modules
- [ ] POST /my/ships/{shipSymbol}/modules/install - Install Ship Module
- [ ] POST /my/ships/{shipSymbol}/modules/remove - Remove Ship Module

## Systems
- [ ] GET /systems - List Systems
- [ ] GET /systems/{systemSymbol} - Get System
- [x] GET /systems/{systemSymbol}/waypoints - List Waypoints in System (List_Waypoints)
- [ ] GET /systems/{systemSymbol}/waypoints/{waypointSymbol} - Get Waypoint
- [x] GET /systems/{systemSymbol}/waypoints/{waypointSymbol}/market - Get Market (View_Market)
- [x] GET /systems/{systemSymbol}/waypoints/{waypointSymbol}/shipyard - Get Shipyard (View_Shipyard)
- [ ] GET /systems/{systemSymbol}/waypoints/{waypointSymbol}/jump-gate - Get Jump Gate
- [ ] GET /systems/{systemSymbol}/waypoints/{waypointSymbol}/construction-site - Get Construction Site
- [ ] POST /systems/{systemSymbol}/waypoints/{waypointSymbol}/construction-site/supply - Supply Construction Site

## Data
- [ ] GET /supply-chain - Get Supply Chain

## Global
- [ ] GET /game/status - Get Status
- [x] POST /register - Register New Agent (Register_Users)
