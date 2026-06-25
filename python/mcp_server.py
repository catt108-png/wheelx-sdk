"""
WheelX MCP Server for Model Context Protocol

This server provides WheelX DeFi functionality through MCP tools and resources.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from fastmcp import FastMCP

# Reuse existing SDK classes
from src.wheelx_sdk.wheelx_sdk import (
    WheelXSDK,
    QuoteRequest,
    QuoteResponse,
    OrderResponse
)

# Initialize FastMCP server
mcp = FastMCP("WheelX MCP Server")

# Initialize SDK
sdk = WheelXSDK()


@mcp.tool()
async def get_quote(
    from_chain: int,
    to_chain: int,
    from_token: str,
    to_token: str,
    from_address: str,
    to_address: str,
    amount: int,
    slippage: Optional[int] = None
) -> Dict[str, Any]:
    """Get a quote for token swap/bridge between chains.

    Args:
        from_chain: Source chain ID (e.g., 1 for Ethereum)
        to_chain: Destination chain ID (e.g., 1 for Ethereum)
        from_token: Source token address
        to_token: Destination token address
        from_address: User's source address
        to_address: User's destination address
        amount: Amount to swap (in token decimals)
        slippage: Slippage tolerance in basis points (optional)

    Returns:
        Quote information including output amount, fees, and transaction data
    """
    try:
        quote_request = QuoteRequest(
            from_chain=from_chain,
            to_chain=to_chain,
            from_token=from_token,
            to_token=to_token,
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            slippage=slippage
        )

        quote = sdk.get_quote(quote_request)

        return {
            "request_id": quote.request_id,
            "amount_out": quote.amount_out,
            "fee": quote.fee,
            "min_receive": quote.min_receive,
            "estimated_time": quote.estimated_time,
            "slippage": quote.slippage,
            "router_type": quote.router_type,
            "router": quote.router,
            "points": quote.points,
            "approve_required": quote.approve is not None,
            "approve_details": {
                "token": quote.approve.token if quote.approve else None,
                "spender": quote.approve.spender if quote.approve else None,
                "amount": quote.approve.amount if quote.approve else None
            } if quote.approve else None,
            "transaction": {
                "to": quote.tx.to,
                "value": quote.tx.value,
                "data": quote.tx.data,
                "chainId": quote.tx.chainId,
                "gas": quote.tx.gas,
                "maxFeePerGas": quote.tx.maxFeePerGas,
                "maxPriorityFeePerGas": quote.tx.maxPriorityFeePerGas
            },
            "price_impact": {
                "bridge_fee": quote.price_impact.bridge_fee,
                "swap_fee": quote.price_impact.swap_fee,
                "dst_gas_fee": quote.price_impact.dst_gas_fee
            }
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_order_status(request_id: str) -> Dict[str, Any]:
    """Get the status of a previously submitted order.

    Args:
        request_id: The request ID from a previous quote

    Returns:
        Order status information including transaction hashes and current state
    """
    try:
        order = sdk.get_order_status(request_id)

        return {
            "order_id": order.order_id,
            "status": order.status,
            "from_chain": order.from_chain,
            "from_token": order.from_token,
            "from_amount": order.from_amount,
            "to_chain": order.to_chain,
            "to_token": order.to_token,
            "to_amount": order.to_amount,
            "from_address": order.from_address,
            "to_address": order.to_address,
            "open_tx_hash": order.open_tx_hash,
            "open_block": order.open_block,
            "open_timestamp": order.open_timestamp,
            "fill_tx_hash": order.fill_tx_hash,
            "fill_block": order.fill_block,
            "fill_timestamp": order.fill_timestamp,
            "points": order.points,
            "from_token_info": {
                "symbol": order.from_token_info.symbol,
                "name": order.from_token_info.name,
                "decimals": order.from_token_info.decimals,
                "address": order.from_token_info.address,
                "chain_id": order.from_token_info.chain_id,
                "logo": order.from_token_info.logo,
                "tags": order.from_token_info.tags
            } if order.from_token_info else None,
            "to_token_info": {
                "symbol": order.to_token_info.symbol,
                "name": order.to_token_info.name,
                "decimals": order.to_token_info.decimals,
                "address": order.to_token_info.address,
                "chain_id": order.to_token_info.chain_id,
                "logo": order.to_token_info.logo,
                "tags": order.to_token_info.tags
            } if order.to_token_info else None
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_supported_chains() -> Dict[str, Any]:
    """Get list of supported blockchain networks.

    Returns:
        Information about supported chains and their configurations
    """
    try:
        # This would typically call an API endpoint for supported chains
        # For now, return a static list of major chains
        chains = {
            "1": {"name": "Ethereum Mainnet", "native_currency": "ETH", "explorer": "https://etherscan.io"},
            "10": {"name": "Optimism", "native_currency": "ETH", "explorer": "https://optimistic.etherscan.io"},
            "56": {"name": "BNB Smart Chain", "native_currency": "BNB", "explorer": "https://bscscan.com"},
            "137": {"name": "Polygon", "native_currency": "MATIC", "explorer": "https://polygonscan.com"},
            "42161": {"name": "Arbitrum One", "native_currency": "ETH", "explorer": "https://arbiscan.io"},
            "8453": {"name": "Base", "native_currency": "ETH", "explorer": "https://basescan.org"},
            "43114": {"name": "Avalanche C-Chain", "native_currency": "AVAX", "explorer": "https://snowtrace.io"}
        }

        return {
            "supported_chains": chains,
            "total_chains": len(chains)
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def calculate_token_amount(amount: float, decimals: int) -> Dict[str, Any]:
    """Calculate the raw token amount from human-readable amount.

    Args:
        amount: Human-readable token amount (e.g., 1.5 for 1.5 tokens)
        decimals: Token decimals (e.g., 18 for ETH, 6 for USDC)

    Returns:
        Raw token amount in smallest units
    """
    try:
        raw_amount = int(amount * (10 ** decimals))
        return {
            "human_amount": amount,
            "decimals": decimals,
            "raw_amount": raw_amount,
            "formatted": f"{amount} tokens = {raw_amount} in raw units"
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def estimate_gas_cost(chain_id: int, gas_limit: int = 21000) -> Dict[str, Any]:
    """Estimate gas cost for a transaction on a specific chain.

    Args:
        chain_id: Chain ID to estimate gas for
        gas_limit: Estimated gas limit for the transaction

    Returns:
        Estimated gas cost in native currency and USD
    """
    try:
        # This is a simplified estimation - in production you'd use gas price APIs
        gas_prices = {
            1: {"gwei": 30, "eth_price": 2000},  # Ethereum
            10: {"gwei": 0.1, "eth_price": 2000},  # Optimism
            56: {"gwei": 5, "bnb_price": 300},  # BSC
            137: {"gwei": 50, "matic_price": 0.7},  # Polygon
            42161: {"gwei": 0.1, "eth_price": 2000},  # Arbitrum
            8453: {"gwei": 0.1, "eth_price": 2000},  # Base
            43114: {"gwei": 25, "avax_price": 30}  # Avalanche
        }

        chain_info = gas_prices.get(chain_id, {"gwei": 10, "eth_price": 2000})

        # Calculate gas cost
        gas_cost_gwei = gas_limit * chain_info["gwei"]
        gas_cost_eth = gas_cost_gwei / 1e9

        # Estimate USD cost
        if chain_id in [1, 10, 42161, 8453]:  # ETH chains
            usd_cost = gas_cost_eth * chain_info["eth_price"]
        elif chain_id == 56:  # BSC
            usd_cost = gas_cost_eth * chain_info["bnb_price"]
        elif chain_id == 137:  # Polygon
            usd_cost = gas_cost_eth * chain_info["matic_price"]
        elif chain_id == 43114:  # Avalanche
            usd_cost = gas_cost_eth * chain_info["avax_price"]
        else:
            usd_cost = gas_cost_eth * 2000  # Default ETH price

        return {
            "chain_id": chain_id,
            "gas_limit": gas_limit,
            "gas_price_gwei": chain_info["gwei"],
            "total_gas_gwei": gas_cost_gwei,
            "total_gas_native": gas_cost_eth,
            "estimated_usd_cost": round(usd_cost, 2),
            "note": "This is a rough estimation. Actual gas costs may vary."
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def compare_quotes(
    from_chain: int,
    to_chain: int,
    from_token: str,
    to_token: str,
    from_address: str,
    to_address: str,
    amount: int,
    slippage: Optional[int] = None
) -> Dict[str, Any]:
    """Get multiple quotes with different slippage settings for comparison.

    Args:
        Same as get_quote, but returns multiple quotes for comparison

    Returns:
        Comparison of quotes with different slippage settings
    """
    try:
        slippage_values = [10, 50, 100] if slippage is None else [slippage]
        quotes = []

        for slippage_val in slippage_values:
            quote_request = QuoteRequest(
                from_chain=from_chain,
                to_chain=to_chain,
                from_token=from_token,
                to_token=to_token,
                from_address=from_address,
                to_address=to_address,
                amount=amount,
                slippage=slippage_val
            )

            quote = sdk.get_quote(quote_request)
            quotes.append({
                "slippage": slippage_val,
                "amount_out": quote.amount_out,
                "min_receive": quote.min_receive,
                "fee": quote.fee,
                "request_id": quote.request_id
            })

        return {
            "comparison": quotes,
            "best_quote": max(quotes, key=lambda x: float(x["amount_out"])),
            "safest_quote": min(quotes, key=lambda x: x["slippage"])
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.resource("wheelx://chains/{chain_id}/tokens")
async def get_chain_tokens(chain_id: str) -> str:
    """Get popular tokens for a specific chain.

    Args:
        chain_id: Chain ID to get tokens for

    Returns:
        JSON string with popular tokens on the specified chain
    """
    try:
        # Common tokens by chain
        token_lists = {
            "1": [  # Ethereum
                {"symbol": "ETH", "address": "0x0000000000000000000000000000000000000000", "decimals": 18},
                {"symbol": "USDC", "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6},
                {"symbol": "USDT", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
                {"symbol": "DAI", "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "decimals": 18},
                {"symbol": "WBTC", "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "decimals": 8}
            ],
            "10": [  # Optimism
                {"symbol": "ETH", "address": "0x0000000000000000000000000000000000000000", "decimals": 18},
                {"symbol": "USDC", "address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607", "decimals": 6},
                {"symbol": "USDT", "address": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58", "decimals": 6}
            ],
            "56": [  # BSC
                {"symbol": "BNB", "address": "0x0000000000000000000000000000000000000000", "decimals": 18},
                {"symbol": "BUSD", "address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56", "decimals": 18},
                {"symbol": "USDT", "address": "0x55d398326f99059fF775485246999027B3197955", "decimals": 18}
            ]
        }

        tokens = token_lists.get(chain_id, [])
        return json.dumps({
            "chain_id": chain_id,
            "tokens": tokens,
            "count": len(tokens)
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("wheelx://status")
async def get_service_status() -> str:
    """Get WheelX service status and availability.

    Returns:
        JSON string with service status information
    """
    try:
        # Check if the service is responsive
        response = requests.get("https://wheelx.fi", timeout=5)
        status = "operational" if response.status_code == 200 else "degraded"

        return json.dumps({
            "service": "WheelX",
            "status": status,
            "response_time": response.elapsed.total_seconds(),
            "last_checked": str(asyncio.get_event_loop().time())
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "service": "WheelX",
            "status": "unavailable",
            "error": str(e)
        })


@mcp.resource("wheelx://docs/usage")
async def get_usage_docs() -> str:
    """Get usage documentation for the WheelX MCP server.

    Returns:
        Markdown documentation for using the MCP server
    """
    return """# WheelX MCP Server Usage Guide

## Available Tools

### get_quote
Get a quote for token swap/bridge between chains.

**Parameters:**
- `from_chain`: Source chain ID (e.g., 1 for Ethereum)
- `to_chain`: Destination chain ID
- `from_token`: Source token address
- `to_token`: Destination token address
- `from_address`: User's source address
- `to_address`: User's destination address
- `amount`: Amount to swap (in token decimals)
- `slippage`: Slippage tolerance in basis points (optional)

### get_order_status
Get the status of a previously submitted order.

**Parameters:**
- `request_id`: The request ID from a previous quote

### get_supported_chains
Get list of supported blockchain networks.

### calculate_token_amount
Calculate the raw token amount from human-readable amount.

**Parameters:**
- `amount`: Human-readable token amount
- `decimals`: Token decimals

### estimate_gas_cost
Estimate gas cost for a transaction on a specific chain.

**Parameters:**
- `chain_id`: Chain ID to estimate gas for
- `gas_limit`: Estimated gas limit (default: 21000)

### compare_quotes
Get multiple quotes with different slippage settings for comparison.

## Available Resources

- `wheelx://chains/{chain_id}/tokens` - Get popular tokens for a chain
- `wheelx://status` - Get service status
- `wheelx://docs/usage` - This documentation

## Example Usage

```python
# Get a quote for swapping USDC to USDT on Ethereum
quote = await get_quote(
    from_chain=1,
    to_chain=1,
    from_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    to_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    from_address="0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
    to_address="0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
    amount=1000000,
    slippage=50
)
```
"""


if __name__ == "__main__":
    # Run the MCP server
    print("Starting WheelX MCP Server...")
    print("Available tools:")
    for tool_name in mcp.tools:
        print(f"  - {tool_name}")
    print("\nAvailable resources:")
    for resource_name in mcp.resources:
        print(f"  - {resource_name}")
    print("\nServer is running...")
    mcp.run()