import asyncio
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
import json
import os
import requests
from typing import Optional

from spacetraders_utils import SpaceTradersClient, client as spacetraders_client
from utils import get_spacetraders_api_key

@dataclass
class SpaceTradersContext:
    """Context for the Space Traders MCP server."""
    client: SpaceTradersClient
    initialized: bool = False

# Global context instance
context: Optional[SpaceTradersContext] = None

@asynccontextmanager
async def spacetraders_lifespan(server: FastMCP) -> AsyncIterator[SpaceTradersContext]:
    """
    Manages the spacetraders client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        SpaceTradersContext: The context containing the SpaceTraders client
    """
    global context
    try:
        # Ensure API key is available
        get_spacetraders_api_key()
        
        # Create context if not exists
        if context is None:
            context = SpaceTradersContext(client=spacetraders_client)
        
        # Mark as initialized
        context.initialized = True
        yield context
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        raise
    finally:
        if context:
            context.initialized = False
            context = None

# Initialize FastMCP server
mcp = FastMCP(
    "Space-Traders-MCP",
    description="MCP server for SpaceTraders API integration",
    lifespan=spacetraders_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

def check_initialization(ctx: Context) -> None:
    """Check if the server is properly initialized."""
    if not ctx.request_context.lifespan_context or not ctx.request_context.lifespan_context.initialized:
        raise ValueError("Server initialization not complete. Please wait and try again.")

@mcp.tool()
async def Register_Users(ctx: Context, text: str) -> str:
    """Register a new user with the Space Traders API.

    This tool is used to register a new user with the Space Traders API.
    Format: 'Register with callsign: CALLSIGN and faction: FACTION'
    
    The registration will create a new agent with:
    - A command ship
    - 175,000 credits
    - A starting faction contract
    
    Note: Requires SPACETRADERS_API_KEY environment variable to be set with your account token
    from https://my.spacetraders.io
    """
    check_initialization(ctx)
    
    # Extract callsign and faction from the text
    parts = text.split()
    callsign = None
    faction = "COSMIC"  # Default faction
    
    # Try to extract callsign and faction from the text
    for i, word in enumerate(parts):
        if word.lower() == "callsign:" and i + 1 < len(parts):
            callsign = parts[i + 1]
        elif word.lower() == "faction:" and i + 1 < len(parts):
            faction = parts[i + 1]
    
    # If no callsign was found, return an error
    if not callsign:
        return "Please provide a callsign for registration. Format: 'Register with callsign: CALLSIGN and faction: FACTION'"
    
    # Prepare the registration data
    registration_data = {
        "symbol": callsign,
        "faction": faction
    }
    
    # Make the API request to register using the account token
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            'register',
            use_account_token=True,  # Use the account token for registration
            data=json.dumps(registration_data)
        )
        
        # Check if the request was successful
        if response.status_code == 201:
            result = response.json()
            # Save the token for future use
            token = result.get("data", {}).get("token")
            agent_data = result.get("data", {}).get("agent", {})
            
            # Store the token for future use
            ctx.request_context.lifespan_context.client.store_token(agent_data.get('symbol'), token)
            
            return f"Successfully registered agent {agent_data.get('symbol')} with faction {agent_data.get('startingFaction')}. Token has been stored for future use."
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Registration failed: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error during registration: {str(e)}"

@mcp.tool()
async def View_Agent_Details(ctx: Context, agent_symbol: str) -> str:
    """Get the current agent's status including credits, headquarters location, and other details.
    
    Args:
        agent_symbol: The symbol/callsign of the agent to view details for
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET', 
            'my/agent', 
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            agent_data = response.json().get("data", {})
            return json.dumps({
                "symbol": agent_data.get("symbol"),
                "headquarters": agent_data.get("headquarters"),
                "credits": agent_data.get("credits"),
                "startingFaction": agent_data.get("startingFaction"),
                "shipCount": agent_data.get("shipCount")
            }, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get agent details: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error retrieving agent details: {str(e)}"

@mcp.tool()
async def List_Ships(ctx: Context, agent_symbol: str) -> str:
    """Get a list of all ships under your command.

    Args:
        agent_symbol: The symbol/callsign of the agent whose ships to list
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET', 
            'my/ships', 
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            ships = response.json().get("data", [])
            formatted_ships = []
            
            for ship in ships:
                formatted_ships.append({
                    "symbol": ship.get("symbol"),
                    "registration": {
                        "name": ship.get("registration", {}).get("name"),
                        "role": ship.get("registration", {}).get("role"),
                    },
                    "nav": {
                        "status": ship.get("nav", {}).get("status"),
                        "location": ship.get("nav", {}).get("waypointSymbol"),
                    },
                    "cargo": {
                        "capacity": ship.get("cargo", {}).get("capacity"),
                        "units": ship.get("cargo", {}).get("units"),
                    }
                })
                
            return json.dumps(formatted_ships, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to list ships: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error listing ships: {str(e)}"

@mcp.tool()
async def View_Market(ctx: Context, agent_symbol: str, waypoint_symbol: str) -> str:
    """View market data at a specific waypoint.

    Args:
        agent_symbol: The symbol/callsign of the agent making the request
        waypoint_symbol: The symbol of the waypoint/market to view (must have Marketplace trait)
    """
    check_initialization(ctx)
    
    try:
        # Extract system symbol from waypoint symbol (waypoints are formatted as "SYSTEM-X-Y")
        system_symbol = "-".join(waypoint_symbol.split("-")[:2])
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET', 
            f'systems/{system_symbol}/waypoints/{waypoint_symbol}/market', 
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            market_data = response.json().get("data", {})
            return json.dumps({
                "symbol": market_data.get("symbol"),
                "exports": [item.get("symbol") for item in market_data.get("exports", [])],
                "imports": [item.get("symbol") for item in market_data.get("imports", [])],
                "exchange": [item.get("symbol") for item in market_data.get("exchange", [])],
                "transactions": market_data.get("transactions", [])[:5],  # Show only recent transactions
                "tradeGoods": [{
                    "symbol": good.get("symbol"),
                    "type": good.get("type"),
                    "supply": good.get("supply"),
                    "purchasePrice": good.get("purchasePrice"),
                    "sellPrice": good.get("sellPrice")
                } for good in market_data.get("tradeGoods", [])]
            }, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to view market: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error viewing market: {str(e)}"

@mcp.tool()
async def List_Factions(ctx: Context) -> str:
    """Get a list of all available factions in the SpaceTraders game.
    
    This tool provides detailed information about all factions, including their symbols, names, 
    descriptions, headquarters, traits, and recruitment status to help users choose a faction.
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET', 
            'factions',
            use_account_token=True
        )
        
        if response.status_code == 200:
            factions = response.json().get("data", [])
            formatted_factions = []
            
            for faction in factions:
                formatted_factions.append({
                    "symbol": faction.get("symbol"),
                    "name": faction.get("name"),
                    "description": faction.get("description"),
                    "headquarters": faction.get("headquarters"),
                    "traits": [trait.get("name") for trait in faction.get("traits", [])]
                })
                
            return json.dumps(formatted_factions, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to list factions: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error listing factions: {str(e)}"

@mcp.tool()
async def Get_Faction(ctx: Context, faction_symbol: str) -> str:
    """View the details of a specific faction.
    
    Args:
        faction_symbol: The symbol of the faction to view
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'factions/{faction_symbol}',
            use_account_token=True
        )
        
        if response.status_code == 200:
            faction = response.json().get("data", {})
            
            result = {
                "symbol": faction.get("symbol"),
                "name": faction.get("name"),
                "description": faction.get("description"),
                "headquarters": faction.get("headquarters"),
                "traits": [{
                    "symbol": trait.get("symbol"),
                    "name": trait.get("name"),
                    "description": trait.get("description")
                } for trait in faction.get("traits", [])],
                "isRecruiting": faction.get("isRecruiting")
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get faction details: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error getting faction details: {str(e)}"

@mcp.tool()
async def List_Contracts(ctx: Context, agent_symbol: str) -> str:
    """Get a list of all contracts for an agent.

    Args:
        agent_symbol: The symbol/callsign of the agent whose contracts to list
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET', 
            'my/contracts',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            contracts_data = response.json().get("data", [])
            formatted_contracts = []
            
            for contract in contracts_data:
                # Format the contract details
                contract_info = {
                    "id": contract.get("id"),
                    "faction": contract.get("factionSymbol"),
                    "type": contract.get("type"),
                    "accepted": contract.get("accepted"),
                    "fulfilled": contract.get("fulfilled"),
                    "expiration": contract.get("deadlineToAccept"),
                    "terms": {
                        "deadline": contract.get("terms", {}).get("deadline"),
                        "payment": contract.get("terms", {}).get("payment", {}),
                        "deliver": contract.get("terms", {}).get("deliver", [])
                    }
                }
                formatted_contracts.append(contract_info)
            
            return json.dumps(formatted_contracts, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to list contracts: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error listing contracts: {str(e)}"

@mcp.tool()
async def Negotiate_Contract(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Negotiate a new contract using a ship.
    
    The ship must be present at a waypoint with a faction to negotiate a contract.
    An agent can only have 1 active contract at a time.

    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to use for negotiation
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/negotiate/contract',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            contract_data = response.json().get("data", {}).get("contract", {})
            
            # Format the contract details
            contract_info = {
                "id": contract_data.get("id"),
                "faction": contract_data.get("factionSymbol"),
                "type": contract_data.get("type"),
                "terms": {
                    "deadline": contract_data.get("terms", {}).get("deadline"),
                    "payment": contract_data.get("terms", {}).get("payment", {}),
                    "deliver": [{
                        "tradeSymbol": item.get("tradeSymbol"),
                        "destinationSymbol": item.get("destinationSymbol"),
                        "unitsRequired": item.get("unitsRequired"),
                        "unitsFulfilled": item.get("unitsFulfilled", 0)
                    } for item in contract_data.get("terms", {}).get("deliver", [])]
                }
            }
            
            return json.dumps(contract_info, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to negotiate contract: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error negotiating contract: {str(e)}"

@mcp.tool()
async def Accept_Contract(ctx: Context, agent_symbol: str, contract_id: str) -> str:
    """Accept a contract.
    
    You can only accept contracts that:
    - Were offered to you
    - Have not been accepted yet
    - Have not expired
    
    On accepting a contract, you will receive the advance payment immediately.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        contract_id: The ID of the contract to accept
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/contracts/{contract_id}/accept',
            agent_symbol=agent_symbol,
            data='{}'  # Empty JSON object to satisfy Content-Type requirement
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            agent_data = data.get("agent", {})
            contract_data = data.get("contract", {})
            
            result = {
                "agent": {
                    "credits": agent_data.get("credits"),
                    "shipCount": agent_data.get("shipCount")
                },
                "contract": {
                    "id": contract_data.get("id"),
                    "faction": contract_data.get("factionSymbol"),
                    "type": contract_data.get("type"),
                    "accepted": contract_data.get("accepted"),
                    "fulfilled": contract_data.get("fulfilled"),
                    "expiration": contract_data.get("deadlineToAccept"),
                    "terms": {
                        "deadline": contract_data.get("terms", {}).get("deadline"),
                        "payment": contract_data.get("terms", {}).get("payment", {}),
                        "deliver": contract_data.get("terms", {}).get("deliver", [])
                    }
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to accept contract: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error accepting contract: {str(e)}"

@mcp.tool()
async def List_Waypoints(ctx: Context, agent_symbol: str, system_symbol: str, waypoint_type: str = None, trait: str = None) -> str:
    """List waypoints in a system, optionally filtered by type and/or trait.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        system_symbol: The symbol of the system to search in
        waypoint_type: Optional type to filter waypoints by (e.g., 'ENGINEERED_ASTEROID', 'ASTEROID', 'PLANET')
        trait: Optional trait to filter waypoints by (e.g., 'SHIPYARD', 'MARKETPLACE')
    """
    check_initialization(ctx)
    
    try:
        # Build the endpoint with optional filters
        endpoint = f'systems/{system_symbol}/waypoints'
        filters = []
        
        if waypoint_type:
            filters.append(f'type={waypoint_type}')
        if trait:
            filters.append(f'traits={trait}')
            
        if filters:
            endpoint += '?' + '&'.join(filters)
            
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            endpoint,
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            waypoints_data = response.json().get("data", [])
            formatted_waypoints = []
            
            for waypoint in waypoints_data:
                formatted_waypoint = {
                    "symbol": waypoint.get("symbol"),
                    "type": waypoint.get("type"),
                    "systemSymbol": waypoint.get("systemSymbol"),
                    "x": waypoint.get("x"),
                    "y": waypoint.get("y"),
                    "orbitals": waypoint.get("orbitals", []),
                    "traits": [
                        {
                            "symbol": trait.get("symbol"),
                            "name": trait.get("name"),
                            "description": trait.get("description")
                        } for trait in waypoint.get("traits", [])
                    ],
                    "faction": waypoint.get("faction", {}).get("symbol") if waypoint.get("faction") else None
                }
                formatted_waypoints.append(formatted_waypoint)
            
            return json.dumps(formatted_waypoints, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to list waypoints: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error listing waypoints: {str(e)}"

@mcp.tool()
async def View_Shipyard(ctx: Context, agent_symbol: str, waypoint_symbol: str) -> str:
    """View the shipyard for a waypoint.
    
    Args:
        agent_symbol: The symbol/callsign of the agent making the request
        waypoint_symbol: The symbol of the waypoint/shipyard to view (must have Shipyard trait)
    """
    check_initialization(ctx)
    
    try:
        # Extract system symbol from waypoint symbol (waypoints are formatted as "SYSTEM-X-Y")
        system_symbol = "-".join(waypoint_symbol.split("-")[:2])
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'systems/{system_symbol}/waypoints/{waypoint_symbol}/shipyard',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            shipyard_data = response.json().get("data", {})
            
            # Format the response to show relevant ship information
            formatted_data = {
                "symbol": shipyard_data.get("symbol"),
                "shipTypes": shipyard_data.get("shipTypes", []),
                "modifications": {
                    "fee": shipyard_data.get("modificationsFee")
                },
                "ships": []
            }
            
            # Add detailed ship information if available
            for ship in shipyard_data.get("ships", []):
                ship_info = {
                    "type": ship.get("type"),
                    "name": ship.get("name"),
                    "description": ship.get("description"),
                    "supply": ship.get("supply"),
                    "purchasePrice": ship.get("purchasePrice"),
                    "frame": {
                        "symbol": ship.get("frame", {}).get("symbol"),
                        "name": ship.get("frame", {}).get("name"),
                        "description": ship.get("frame", {}).get("description"),
                        "moduleSlots": ship.get("frame", {}).get("moduleSlots"),
                        "mountingPoints": ship.get("frame", {}).get("mountingPoints"),
                        "fuelCapacity": ship.get("frame", {}).get("fuelCapacity")
                    },
                    "reactor": {
                        "symbol": ship.get("reactor", {}).get("symbol"),
                        "name": ship.get("reactor", {}).get("name"),
                        "description": ship.get("reactor", {}).get("description"),
                        "powerOutput": ship.get("reactor", {}).get("powerOutput")
                    },
                    "engine": {
                        "symbol": ship.get("engine", {}).get("symbol"),
                        "name": ship.get("engine", {}).get("name"),
                        "description": ship.get("engine", {}).get("description"),
                        "speed": ship.get("engine", {}).get("speed")
                    },
                    "modules": ship.get("modules", []),
                    "mounts": ship.get("mounts", []),
                    "crew": ship.get("crew", {})
                }
                formatted_data["ships"].append(ship_info)
            
            return json.dumps(formatted_data, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to view shipyard: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error viewing shipyard: {str(e)}"

@mcp.tool()
async def Purchase_Ship(ctx: Context, agent_symbol: str, ship_type: str, waypoint_symbol: str) -> str:
    """Purchase a ship from a Shipyard.
    
    A ship under your agent's ownership must be present at the waypoint,
    the waypoint must have a Shipyard, and the Shipyard must sell the desired ship type.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_type: The type of ship to purchase (e.g., 'SHIP_MINING_DRONE')
        waypoint_symbol: The symbol of the waypoint where to purchase the ship
    """
    check_initialization(ctx)
    
    try:
        # Prepare the purchase data
        purchase_data = {
            "shipType": ship_type,
            "waypointSymbol": waypoint_symbol
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            'my/ships',
            agent_symbol=agent_symbol,
            data=json.dumps(purchase_data)
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            
            # Format the response with relevant details
            result = {
                "agent": {
                    "credits": data.get("agent", {}).get("credits"),
                    "shipCount": data.get("agent", {}).get("shipCount")
                },
                "ship": {
                    "symbol": data.get("ship", {}).get("symbol"),
                    "registration": {
                        "name": data.get("ship", {}).get("registration", {}).get("name"),
                        "role": data.get("ship", {}).get("registration", {}).get("role")
                    },
                    "nav": {
                        "status": data.get("ship", {}).get("nav", {}).get("status"),
                        "location": data.get("ship", {}).get("nav", {}).get("waypointSymbol")
                    },
                    "frame": {
                        "symbol": data.get("ship", {}).get("frame", {}).get("symbol"),
                        "moduleSlots": data.get("ship", {}).get("frame", {}).get("moduleSlots"),
                        "mountingPoints": data.get("ship", {}).get("frame", {}).get("mountingPoints"),
                        "fuelCapacity": data.get("ship", {}).get("frame", {}).get("fuelCapacity")
                    },
                    "reactor": {
                        "symbol": data.get("ship", {}).get("reactor", {}).get("symbol"),
                        "powerOutput": data.get("ship", {}).get("reactor", {}).get("powerOutput")
                    },
                    "engine": {
                        "symbol": data.get("ship", {}).get("engine", {}).get("symbol"),
                        "speed": data.get("ship", {}).get("engine", {}).get("speed")
                    },
                    "modules": data.get("ship", {}).get("modules", []),
                    "mounts": data.get("ship", {}).get("mounts", []),
                    "cargo": {
                        "capacity": data.get("ship", {}).get("cargo", {}).get("capacity"),
                        "units": data.get("ship", {}).get("cargo", {}).get("units")
                    }
                },
                "transaction": {
                    "waypointSymbol": data.get("transaction", {}).get("waypointSymbol"),
                    "shipSymbol": data.get("transaction", {}).get("shipSymbol"),
                    "price": data.get("transaction", {}).get("price"),
                    "agentSymbol": data.get("transaction", {}).get("agentSymbol")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to purchase ship: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error purchasing ship: {str(e)}"

@mcp.tool()
async def Orbit_Ship(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Move a ship into orbit at its current location.
    
    The ship must be capable of moving into orbit at the time of the request.
    Ships in orbit can navigate or extract resources but cannot access the local market or shipyard.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to move into orbit
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/orbit',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            nav_data = response.json().get("data", {}).get("nav", {})
            
            result = {
                "status": nav_data.get("status"),
                "waypointSymbol": nav_data.get("waypointSymbol"),
                "route": {
                    "destination": {
                        "symbol": nav_data.get("route", {}).get("destination", {}).get("symbol"),
                        "type": nav_data.get("route", {}).get("destination", {}).get("type"),
                        "systemSymbol": nav_data.get("route", {}).get("destination", {}).get("systemSymbol"),
                        "x": nav_data.get("route", {}).get("destination", {}).get("x"),
                        "y": nav_data.get("route", {}).get("destination", {}).get("y")
                    },
                    "departure": {
                        "symbol": nav_data.get("route", {}).get("origin", {}).get("symbol"),
                        "type": nav_data.get("route", {}).get("origin", {}).get("type"),
                        "systemSymbol": nav_data.get("route", {}).get("origin", {}).get("systemSymbol"),
                        "x": nav_data.get("route", {}).get("origin", {}).get("x"),
                        "y": nav_data.get("route", {}).get("origin", {}).get("y")
                    },
                    "arrival": nav_data.get("route", {}).get("arrival"),
                    "departureTime": nav_data.get("route", {}).get("departureTime")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to move ship into orbit: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error moving ship into orbit: {str(e)}"

@mcp.tool()
async def Navigate_Ship(ctx: Context, agent_symbol: str, ship_symbol: str, waypoint_symbol: str) -> str:
    """Navigate a ship to a specific waypoint.
    
    The ship must be in orbit to use this command. The ship will enter a IN_TRANSIT status
    and most actions will be locked until it arrives at its destination.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to navigate
        waypoint_symbol: The symbol of the waypoint to navigate to
    """
    check_initialization(ctx)
    
    try:
        # Prepare the navigation data
        navigation_data = {
            "waypointSymbol": waypoint_symbol
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/navigate',
            agent_symbol=agent_symbol,
            data=json.dumps(navigation_data)
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            nav_data = data.get("nav", {})
            fuel = data.get("fuel", {})
            
            result = {
                "nav": {
                    "status": nav_data.get("status"),
                    "waypointSymbol": nav_data.get("waypointSymbol"),
                    "route": {
                        "destination": {
                            "symbol": nav_data.get("route", {}).get("destination", {}).get("symbol"),
                            "type": nav_data.get("route", {}).get("destination", {}).get("type"),
                            "systemSymbol": nav_data.get("route", {}).get("destination", {}).get("systemSymbol"),
                            "x": nav_data.get("route", {}).get("destination", {}).get("x"),
                            "y": nav_data.get("route", {}).get("destination", {}).get("y")
                        },
                        "departure": {
                            "symbol": nav_data.get("route", {}).get("origin", {}).get("symbol"),
                            "type": nav_data.get("route", {}).get("origin", {}).get("type"),
                            "systemSymbol": nav_data.get("route", {}).get("origin", {}).get("systemSymbol"),
                            "x": nav_data.get("route", {}).get("origin", {}).get("x"),
                            "y": nav_data.get("route", {}).get("origin", {}).get("y")
                        },
                        "arrival": nav_data.get("route", {}).get("arrival"),
                        "departureTime": nav_data.get("route", {}).get("departureTime")
                    }
                },
                "fuel": {
                    "current": fuel.get("current"),
                    "capacity": fuel.get("capacity"),
                    "consumed": {
                        "amount": fuel.get("consumed", {}).get("amount"),
                        "timestamp": fuel.get("consumed", {}).get("timestamp")
                    }
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to navigate ship: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error navigating ship: {str(e)}"

@mcp.tool()
async def Dock_Ship(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Dock a ship at its current waypoint.
    
    The ship must be in orbit to dock. Ships can dock at any waypoint that has a 
    compatible dock for the ship's size. Docking is required to access the local market,
    shipyard, or to refuel the ship.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to dock
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/dock',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            nav_data = response.json().get("data", {}).get("nav", {})
            
            result = {
                "status": nav_data.get("status"),
                "waypointSymbol": nav_data.get("waypointSymbol"),
                "route": {
                    "destination": {
                        "symbol": nav_data.get("route", {}).get("destination", {}).get("symbol"),
                        "type": nav_data.get("route", {}).get("destination", {}).get("type"),
                        "systemSymbol": nav_data.get("route", {}).get("destination", {}).get("systemSymbol"),
                        "x": nav_data.get("route", {}).get("destination", {}).get("x"),
                        "y": nav_data.get("route", {}).get("destination", {}).get("y")
                    }
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to dock ship: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error docking ship: {str(e)}"

@mcp.tool()
async def Refuel_Ship(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Refuel a ship at its current waypoint.
    
    The ship must be docked at a waypoint with a marketplace to refuel.
    Refueling costs credits based on the amount of fuel required.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to refuel
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/refuel',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            agent = data.get("agent", {})
            fuel = data.get("fuel", {})
            transaction = data.get("transaction", {})
            
            result = {
                "agent": {
                    "credits": agent.get("credits")
                },
                "fuel": {
                    "current": fuel.get("current"),
                    "capacity": fuel.get("capacity")
                },
                "transaction": {
                    "totalPrice": transaction.get("totalPrice"),
                    "units": transaction.get("units"),
                    "pricePerUnit": transaction.get("pricePerUnit")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to refuel ship: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error refueling ship: {str(e)}"

@mcp.tool()
async def View_Ship_Cargo(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Get the current cargo inventory of a ship.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to check cargo
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/ships/{ship_symbol}/cargo',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            cargo_data = response.json().get("data", {})
            
            result = {
                "capacity": cargo_data.get("capacity"),
                "units": cargo_data.get("units"),
                "inventory": [{
                    "symbol": item.get("symbol"),
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "units": item.get("units")
                } for item in cargo_data.get("inventory", [])]
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to view cargo: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error viewing cargo: {str(e)}"

@mcp.tool()
async def Jettison_Cargo(ctx: Context, agent_symbol: str, ship_symbol: str, cargo_symbol: str, units: int) -> str:
    """Jettison (throw away) cargo from your ship.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to jettison cargo from
        cargo_symbol: The symbol of the cargo item to jettison
        units: The number of units to jettison
    """
    check_initialization(ctx)
    
    try:
        # Prepare the jettison data
        jettison_data = {
            "symbol": cargo_symbol,
            "units": units
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/jettison',
            agent_symbol=agent_symbol,
            data=json.dumps(jettison_data)
        )
        
        if response.status_code == 200:
            cargo_data = response.json().get("data", {}).get("cargo", {})
            
            result = {
                "cargo": {
                    "capacity": cargo_data.get("capacity"),
                    "units": cargo_data.get("units"),
                    "inventory": [{
                        "symbol": item.get("symbol"),
                        "units": item.get("units")
                    } for item in cargo_data.get("inventory", [])]
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to jettison cargo: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error jettisoning cargo: {str(e)}"

@mcp.tool()
async def Sell_Cargo(ctx: Context, agent_symbol: str, ship_symbol: str, cargo_symbol: str, units: int) -> str:
    """Sell cargo at the current waypoint's marketplace.
    
    The ship must be docked at a waypoint with a marketplace.
    This function will automatically dock the ship if it isn't already docked.

    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship selling cargo
        cargo_symbol: The symbol of the cargo item to sell
        units: The number of units to sell
    """
    check_initialization(ctx)
    
    try:
        # First, check ship's current status
        ship_response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/ships/{ship_symbol}',
            agent_symbol=agent_symbol
        )
        
        if ship_response.status_code == 200:
            nav_status = ship_response.json().get("data", {}).get("nav", {}).get("status")
            
            # If not docked, attempt to dock first
            if nav_status != "DOCKED":
                dock_response = ctx.request_context.lifespan_context.client.make_request(
                    'POST',
                    f'my/ships/{ship_symbol}/dock',
                    agent_symbol=agent_symbol
                )
                
                if dock_response.status_code != 200:
                    return f"Failed to dock before selling: {dock_response.json().get('error', {}).get('message', 'Unknown error')}"
        
        # Prepare the sell data
        sell_data = {
            "symbol": cargo_symbol,
            "units": units
        }
        
        # Now attempt to sell
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/sell',
            agent_symbol=agent_symbol,
            data=json.dumps(sell_data)
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            agent = data.get("agent", {})
            cargo = data.get("cargo", {})
            transaction = data.get("transaction", {})
            
            result = {
                "agent": {
                    "credits": agent.get("credits")
                },
                "cargo": {
                    "capacity": cargo.get("capacity"),
                    "units": cargo.get("units"),
                    "inventory": [{
                        "symbol": item.get("symbol"),
                        "units": item.get("units")
                    } for item in cargo.get("inventory", [])]
                },
                "transaction": {
                    "waypointSymbol": transaction.get("waypointSymbol"),
                    "tradeSymbol": transaction.get("tradeSymbol"),
                    "type": transaction.get("type"),
                    "units": transaction.get("units"),
                    "pricePerUnit": transaction.get("pricePerUnit"),
                    "totalPrice": transaction.get("totalPrice")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to sell cargo: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error selling cargo: {str(e)}"

@mcp.tool()
async def Extract_Resources(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Extract resources from a waypoint using the ship's mining equipment.
    
    The ship must be in orbit and at a valid extraction point (like an asteroid).
    After extraction, the ship will enter a cooldown period before it can extract again.
    This function will automatically put the ship in orbit if it isn't already.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform extraction
    """
    check_initialization(ctx)
    
    try:
        # First, check ship's current status
        ship_response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/ships/{ship_symbol}',
            agent_symbol=agent_symbol
        )
        
        if ship_response.status_code == 200:
            nav_status = ship_response.json().get("data", {}).get("nav", {}).get("status")
            
            # If not in orbit, attempt to orbit first
            if nav_status != "IN_ORBIT":
                orbit_response = ctx.request_context.lifespan_context.client.make_request(
                    'POST',
                    f'my/ships/{ship_symbol}/orbit',
                    agent_symbol=agent_symbol
                )
                
                if orbit_response.status_code != 200:
                    return f"Failed to achieve orbit before extraction: {orbit_response.json().get('error', {}).get('message', 'Unknown error')}"
        
        # Now attempt extraction
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/extract',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            extraction = data.get("extraction", {})
            cargo = data.get("cargo", {})
            cooldown = data.get("cooldown", {})
            
            result = {
                "extraction": {
                    "shipSymbol": extraction.get("shipSymbol"),
                    "yield": {
                        "symbol": extraction.get("yield", {}).get("symbol"),
                        "units": extraction.get("yield", {}).get("units")
                    }
                },
                "cargo": {
                    "capacity": cargo.get("capacity"),
                    "units": cargo.get("units"),
                    "inventory": cargo.get("inventory", [])
                },
                "cooldown": {
                    "shipSymbol": cooldown.get("shipSymbol"),
                    "totalSeconds": cooldown.get("totalSeconds"),
                    "remainingSeconds": cooldown.get("remainingSeconds"),
                    "expiration": cooldown.get("expiration")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to extract resources: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error extracting resources: {str(e)}"

@mcp.tool()
async def Transfer_Cargo(ctx: Context, agent_symbol: str, source_ship: str, destination_ship: str, cargo_symbol: str, units: int) -> str:
    """Transfer cargo between two ships.
    
    Both ships must be at the same waypoint and in the same state (both docked or both in orbit).
    The receiving ship must have enough cargo capacity for the transferred goods.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        source_ship: The symbol of the ship transferring cargo
        destination_ship: The symbol of the ship receiving cargo
        cargo_symbol: The symbol of the cargo item to transfer
        units: The number of units to transfer
    """
    check_initialization(ctx)
    
    try:
        # Prepare the transfer data
        transfer_data = {
            "tradeSymbol": cargo_symbol,
            "units": units,
            "shipSymbol": destination_ship
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{source_ship}/transfer',
            agent_symbol=agent_symbol,
            data=json.dumps(transfer_data)
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            cargo = data.get("cargo", {})
            
            result = {
                "cargo": {
                    "capacity": cargo.get("capacity"),
                    "units": cargo.get("units"),
                    "inventory": [{
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "units": item.get("units")
                    } for item in cargo.get("inventory", [])]
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to transfer cargo: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error transferring cargo: {str(e)}"

@mcp.tool()
async def View_Ship_Details(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Get detailed information about a specific ship.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to view details for
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/ships/{ship_symbol}',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            ship_data = response.json().get("data", {})
            
            result = {
                "symbol": ship_data.get("symbol"),
                "registration": ship_data.get("registration", {}),
                "nav": ship_data.get("nav", {}),
                "crew": ship_data.get("crew", {}),
                "frame": ship_data.get("frame", {}),
                "reactor": ship_data.get("reactor", {}),
                "engine": ship_data.get("engine", {}),
                "modules": ship_data.get("modules", []),
                "mounts": ship_data.get("mounts", []),
                "cargo": ship_data.get("cargo", {}),
                "fuel": ship_data.get("fuel", {})
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get ship details: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error getting ship details: {str(e)}"

@mcp.tool()
async def Scan_Systems(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Scan for nearby systems using a ship's sensor array.
    
    Requires a ship to have the Sensor Array mount installed.
    The ship will enter a cooldown after scanning.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform the scan
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/scan/systems',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            systems = data.get("systems", [])
            cooldown = data.get("cooldown", {})
            
            result = {
                "systems": [{
                    "symbol": system.get("symbol"),
                    "sectorSymbol": system.get("sectorSymbol"),
                    "type": system.get("type"),
                    "x": system.get("x"),
                    "y": system.get("y"),
                    "distance": system.get("distance")
                } for system in systems],
                "cooldown": {
                    "shipSymbol": cooldown.get("shipSymbol"),
                    "totalSeconds": cooldown.get("totalSeconds"),
                    "remainingSeconds": cooldown.get("remainingSeconds"),
                    "expiration": cooldown.get("expiration")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to scan systems: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error scanning systems: {str(e)}"

@mcp.tool()
async def Scan_Waypoints(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Scan for nearby waypoints using a ship's sensor array.
    
    Requires a ship to have the Sensor Array mount installed.
    Can reveal traits of uncharted waypoints.
    The ship will enter a cooldown after scanning.

    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform the scan
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/scan/waypoints',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            waypoints = data.get("waypoints", [])
            cooldown = data.get("cooldown", {})
            
            result = {
                "waypoints": [{
                    "symbol": waypoint.get("symbol"),
                    "type": waypoint.get("type"),
                    "systemSymbol": waypoint.get("systemSymbol"),
                    "x": waypoint.get("x"),
                    "y": waypoint.get("y"),
                    "orbitals": waypoint.get("orbitals", []),
                    "traits": [
                        {
                            "symbol": trait.get("symbol"),
                            "name": trait.get("name"),
                            "description": trait.get("description")
                        } for trait in waypoint.get("traits", [])
                    ],
                    "chart": waypoint.get("chart", {})
                } for waypoint in waypoints],
                "cooldown": {
                    "shipSymbol": cooldown.get("shipSymbol"),
                    "totalSeconds": cooldown.get("totalSeconds"),
                    "remainingSeconds": cooldown.get("remainingSeconds"),
                    "expiration": cooldown.get("expiration")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to scan waypoints: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error scanning waypoints: {str(e)}"

@mcp.tool()
async def Scan_Ships(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Scan for nearby ships using a ship's sensor array.
    
    Requires a ship to have the Sensor Array mount installed.
    The ship will enter a cooldown after scanning.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform the scan
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/scan/ships',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            ships = data.get("ships", [])
            cooldown = data.get("cooldown", {})
            
            result = {
                "ships": [{
                    "symbol": ship.get("symbol"),
                    "registration": {
                        "name": ship.get("registration", {}).get("name"),
                        "role": ship.get("registration", {}).get("role"),
                        "factionSymbol": ship.get("registration", {}).get("factionSymbol")
                    },
                    "nav": {
                        "systemSymbol": ship.get("nav", {}).get("systemSymbol"),
                        "waypointSymbol": ship.get("nav", {}).get("waypointSymbol"),
                        "status": ship.get("nav", {}).get("status")
                    },
                    "frame": {
                        "symbol": ship.get("frame", {}).get("symbol")
                    }
                } for ship in ships],
                "cooldown": {
                    "shipSymbol": cooldown.get("shipSymbol"),
                    "totalSeconds": cooldown.get("totalSeconds"),
                    "remainingSeconds": cooldown.get("remainingSeconds"),
                    "expiration": cooldown.get("expiration")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to scan ships: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error scanning ships: {str(e)}"

@mcp.tool()
async def Get_Contract(ctx: Context, agent_symbol: str, contract_id: str) -> str:
    """Get the details of a specific contract.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        contract_id: The ID of the contract to view
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/contracts/{contract_id}',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            contract = response.json().get("data", {})
            
            # Format the contract details
            result = {
                "id": contract.get("id"),
                "factionSymbol": contract.get("factionSymbol"),
                "type": contract.get("type"),
                "terms": {
                    "deadline": contract.get("terms", {}).get("deadline"),
                    "payment": contract.get("terms", {}).get("payment", {}),
                    "deliver": [{
                        "tradeSymbol": item.get("tradeSymbol"),
                        "destinationSymbol": item.get("destinationSymbol"),
                        "unitsRequired": item.get("unitsRequired"),
                        "unitsFulfilled": item.get("unitsFulfilled")
                    } for item in contract.get("terms", {}).get("deliver", [])]
                },
                "accepted": contract.get("accepted"),
                "fulfilled": contract.get("fulfilled"),
                "deadlineToAccept": contract.get("deadlineToAccept")
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get contract: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error getting contract: {str(e)}"

@mcp.tool()
async def Deliver_Contract_Cargo(ctx: Context, agent_symbol: str, contract_id: str, ship_symbol: str, trade_symbol: str, units: int) -> str:
    """Deliver cargo to fulfill a contract.
    
    The ship must be at the delivery location specified in the contract's terms,
    and must have the required cargo units in its hold.
    Delivered cargo will be removed from the ship.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        contract_id: The ID of the contract to deliver to
        ship_symbol: The symbol of the ship delivering cargo
        trade_symbol: The symbol of the cargo to deliver
        units: The number of units to deliver
    """
    check_initialization(ctx)
    
    try:
        # Prepare the delivery data
        delivery_data = {
            "shipSymbol": ship_symbol,
            "tradeSymbol": trade_symbol,
            "units": units
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/contracts/{contract_id}/deliver',
            agent_symbol=agent_symbol,
            data=json.dumps(delivery_data)
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            contract = data.get("contract", {})
            cargo = data.get("cargo", {})
            
            result = {
                "contract": {
                    "id": contract.get("id"),
                    "factionSymbol": contract.get("factionSymbol"),
                    "type": contract.get("type"),
                    "fulfilled": contract.get("fulfilled"),
                    "terms": {
                        "deadline": contract.get("terms", {}).get("deadline"),
                        "payment": contract.get("terms", {}).get("payment", {}),
                        "deliver": [{
                            "tradeSymbol": item.get("tradeSymbol"),
                            "destinationSymbol": item.get("destinationSymbol"),
                            "unitsRequired": item.get("unitsRequired"),
                            "unitsFulfilled": item.get("unitsFulfilled")
                        } for item in contract.get("terms", {}).get("deliver", [])]
                    }
                },
                "cargo": {
                    "capacity": cargo.get("capacity"),
                    "units": cargo.get("units"),
                    "inventory": [{
                        "symbol": item.get("symbol"),
                        "units": item.get("units")
                    } for item in cargo.get("inventory", [])]
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to deliver cargo: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error delivering cargo: {str(e)}"

@mcp.tool()
async def Fulfill_Contract(ctx: Context, agent_symbol: str, contract_id: str) -> str:
    """Fulfill a contract after all delivery terms have been met.
    
    Can only be used on contracts that have all of their delivery terms fulfilled.
    This will complete the contract and award the remaining payment.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        contract_id: The ID of the contract to fulfill
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/contracts/{contract_id}/fulfill',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            agent = data.get("agent", {})
            contract = data.get("contract", {})
            
            result = {
                "agent": {
                    "credits": agent.get("credits")
                },
                "contract": {
                    "id": contract.get("id"),
                    "factionSymbol": contract.get("factionSymbol"),
                    "type": contract.get("type"),
                    "fulfilled": contract.get("fulfilled"),
                    "accepted": contract.get("accepted"),
                    "terms": {
                        "deadline": contract.get("terms", {}).get("deadline"),
                        "payment": contract.get("terms", {}).get("payment", {}),
                        "deliver": [{
                            "tradeSymbol": item.get("tradeSymbol"),
                            "destinationSymbol": item.get("destinationSymbol"),
                            "unitsRequired": item.get("unitsRequired"),
                            "unitsFulfilled": item.get("unitsFulfilled")
                        } for item in contract.get("terms", {}).get("deliver", [])]
                    }
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to fulfill contract: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error fulfilling contract: {str(e)}"

@mcp.tool()
async def List_Agents(ctx: Context, agent_symbol: str) -> str:
    """Fetch details about all agents in the game.
    
    Args:
        agent_symbol: The symbol/callsign of the agent making the request
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            'agents',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get("data", [])
            meta = data.get("meta", {})
            
            result = {
                "agents": [{
                    "accountId": agent.get("accountId"),
                    "symbol": agent.get("symbol"),
                    "headquarters": agent.get("headquarters"),
                    "credits": agent.get("credits"),
                    "startingFaction": agent.get("startingFaction"),
                    "shipCount": agent.get("shipCount")
                } for agent in agents],
                "meta": {
                    "total": meta.get("total"),
                    "page": meta.get("page"),
                    "limit": meta.get("limit")
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to list agents: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error listing agents: {str(e)}"

@mcp.tool()
async def Get_Public_Agent(ctx: Context, agent_symbol: str) -> str:
    """Get public details for a specific agent by symbol.
    
    Args:
        agent_symbol: The symbol/callsign of the agent to look up
    """
    check_initialization(ctx)
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'agents/{agent_symbol}'
        )
        if response.status_code == 200:
            agent_data = response.json().get("data", {})
            return json.dumps({
                "symbol": agent_data.get("symbol"),
                "headquarters": agent_data.get("headquarters"),
                "credits": agent_data.get("credits"),
                "startingFaction": agent_data.get("startingFaction"),
                "shipCount": agent_data.get("shipCount")
            }, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get public agent details: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error retrieving public agent details: {str(e)}"

@mcp.tool()
async def Refine_Ship(ctx: Context, agent_symbol: str, ship_symbol: str, produce: str) -> str:
    """Attempt to refine raw materials on your ship.
    
    The ship must have a Refinery module installed and have the necessary raw materials.
    When refining, 100 basic goods will be converted into 10 processed goods.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform refining
        produce: The type of good to produce (IRON, COPPER, SILVER, GOLD, ALUMINUM, PLATINUM, URANITE, MERITIUM, FUEL)
    """
    check_initialization(ctx)
    
    try:
        # Prepare the refining data
        refine_data = {
            "produce": produce
        }
        
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/refine',
            agent_symbol=agent_symbol,
            data=json.dumps(refine_data)
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json().get("data", {})
            cargo = data.get("cargo", {})
            cooldown = data.get("cooldown", {})
            produced = data.get("produced", [])
            consumed = data.get("consumed", [])
            
            result = {
                "cargo": {
                    "capacity": cargo.get("capacity"),
                    "units": cargo.get("units"),
                    "inventory": [{
                        "symbol": item.get("symbol"),
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "units": item.get("units")
                    } for item in cargo.get("inventory", [])]
                },
                "cooldown": {
                    "shipSymbol": cooldown.get("shipSymbol"),
                    "totalSeconds": cooldown.get("totalSeconds"),
                    "remainingSeconds": cooldown.get("remainingSeconds"),
                    "expiration": cooldown.get("expiration")
                },
                "produced": [{
                    "tradeSymbol": item.get("tradeSymbol"),
                    "units": item.get("units")
                } for item in produced],
                "consumed": [{
                    "tradeSymbol": item.get("tradeSymbol"),
                    "units": item.get("units")
                } for item in consumed]
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to refine materials: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error refining materials: {str(e)}"

@mcp.tool()
async def Chart_Waypoint(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Command a ship to chart the waypoint at its current location.
    
    Most waypoints in the universe are uncharted by default. These waypoints have their traits 
    hidden until they have been charted by a ship. Charting a waypoint will record your agent 
    as the one who created the chart, and all other agents will be able to see the waypoint's traits.
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to perform the charting
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/chart',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 201:
            data = response.json().get("data", {})
            chart = data.get("chart", {})
            waypoint = data.get("waypoint", {})
            
            result = {
                "chart": {
                    "waypointSymbol": chart.get("waypointSymbol"),
                    "submittedBy": chart.get("submittedBy"),
                    "submittedOn": chart.get("submittedOn")
                },
                "waypoint": {
                    "symbol": waypoint.get("symbol"),
                    "type": waypoint.get("type"),
                    "systemSymbol": waypoint.get("systemSymbol"),
                    "x": waypoint.get("x"),
                    "y": waypoint.get("y"),
                    "orbitals": waypoint.get("orbitals", []),
                    "traits": [
                        {
                            "symbol": trait.get("symbol"),
                            "name": trait.get("name"),
                            "description": trait.get("description")
                        } for trait in waypoint.get("traits", [])
                    ],
                    "chart": waypoint.get("chart", {})
                }
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to chart waypoint: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error charting waypoint: {str(e)}"

@mcp.tool()
async def Get_Ship_Cooldown(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Retrieve the details of your ship's reactor cooldown.
    
    Some actions such as activating your jump drive, scanning, or extracting resources tax your 
    reactor and result in a cooldown. Your ship cannot perform additional actions until your 
    cooldown has expired. The duration of your cooldown is relative to the power consumption 
    of the related modules or mounts for the action taken.
    
    Returns "No cooldown" if the ship has no active cooldown (204 status code).
    
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to check cooldown for
    """
    check_initialization(ctx)
    
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'GET',
            f'my/ships/{ship_symbol}/cooldown',
            agent_symbol=agent_symbol
        )
        
        if response.status_code == 204:
            return "No cooldown"
        elif response.status_code == 200:
            cooldown = response.json().get("data", {})
            
            result = {
                "shipSymbol": cooldown.get("shipSymbol"),
                "totalSeconds": cooldown.get("totalSeconds"),
                "remainingSeconds": cooldown.get("remainingSeconds"),
                "expiration": cooldown.get("expiration")
            }
            
            return json.dumps(result, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to get ship cooldown: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error getting ship cooldown: {str(e)}"

@mcp.tool()
async def Create_Survey(ctx: Context, agent_symbol: str, ship_symbol: str) -> str:
    """Create a survey on a waypoint using a ship with a Surveyor mount.
    Args:
        agent_symbol: The symbol/callsign of the agent
        ship_symbol: The symbol of the ship to use for surveying
    """
    check_initialization(ctx)
    try:
        response = ctx.request_context.lifespan_context.client.make_request(
            'POST',
            f'my/ships/{ship_symbol}/survey',
            agent_symbol=agent_symbol
        )
        if response.status_code == 201:
            data = response.json().get("data", {})
            cooldown = data.get("cooldown", {})
            surveys = data.get("surveys", [])
            return json.dumps({
                "cooldown": cooldown,
                "surveys": surveys
            }, indent=2)
        else:
            error_message = response.json().get("error", {}).get("message", "Unknown error")
            return f"Failed to create survey: {error_message} (Status code: {response.status_code})"
    except Exception as e:
        return f"Error creating survey: {str(e)}"

async def main():
    """Main entry point for the MCP server."""
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
