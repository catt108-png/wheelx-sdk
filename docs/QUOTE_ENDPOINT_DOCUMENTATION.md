# WheelX Quote API Documentation

## Overview

The `/v1/quote` endpoint provides token swap and bridge quotes with detailed transaction information for EVM-compatible chains. It returns both pricing information and the complete transaction data needed to execute the swap.

## Endpoint

```
POST https://api.wheelx.fi/v1/quote
```

## Request

### Request Body Schema

```typescript
interface QuoteRequest {
  from_chain: number;          // Source chain ID (e.g., 1 for Ethereum)
  to_chain: number;            // Destination chain ID
  from_token: string;          // Source token address
  to_token: string;            // Destination token address
  from_address: string;        // User's wallet address (source)
  to_address: string;          // Recipient address (destination)
  amount: number;              // Amount to swap (in smallest units)
  slippage?: number;           // Optional slippage tolerance (default: auto)
}
```

### Example Request

```json
{
  "from_chain": 1,
  "to_chain": 1,
  "from_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "to_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "from_address": "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
  "to_address": "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
  "amount": 1000000,
  "slippage": 50,
}
```

## Response

### Response Schema

```typescript
interface QuoteResponse {
  request_id: string;          // Unique identifier for this quote
  amount_out: string;          // Expected output amount
  fee: string;                 // Total fee amount
  tx: Tx;                     // Transaction data for execution
  approve?: ApproveAction;     // Optional approval transaction data
  slippage: number;           // Applied slippage percentage
  min_receive: string;        // Minimum amount to receive after slippage
  estimated_time: number;     // Estimated completion time in seconds
  recipient: string;          // Recipient address
  router_type: RouterType;    // Type of operation (swap/bridge/wrap/unwrap)
  price_impact: PriceImpactFormatted; // Detailed fee breakdown
  router: string;             // Router identifier
  created_at: string;         // Quote creation timestamp
  points: string;             // Points earned for this transaction
}

interface Tx {
  to: string;                 // Contract address to interact with
  value: number;              // ETH value to send (for native token swaps)
  data: string;               // Transaction calldata
  chainId?: number;           // Chain ID
  gas?: number;               // Estimated gas limit
  maxFeePerGas?: number;      // Max fee per gas (EIP-1559)
  maxPriorityFeePerGas?: number; // Max priority fee per gas (EIP-1559)
}

interface ApproveAction {
  token: string;              // Token address to approve
  spender: string;            // Spender contract address
  amount: number;             // Amount to approve
}

interface PriceImpactFormatted {
  bridge_fee: string;         // Bridge fee amount
  swap_fee: string;           // Swap fee amount
  dst_gas_fee: string;        // Destination gas fee
}

type RouterType = "swap" | "bridge" | "wrap" | "unwrap";
```

### Example Response

```json
{
  "request_id": "quote_123456789",
  "amount_out": "999500",
  "fee": "500",
  "tx": {
    "to": "0x1234567890123456789012345678901234567890",
    "value": 0,
    "data": "0x1234567890abcdef...",
    "chainId": 1,
    "gas": 210000,
    "maxFeePerGas": 30000000000,
    "maxPriorityFeePerGas": 2000000000
  },
  "approve": {
    "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "spender": "0x1234567890123456789012345678901234567890",
    "amount": 1000000
  },
  "slippage": 50,
  "min_receive": "999000",
  "estimated_time": 10,
  "recipient": "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
  "router_type": "swap",
  "price_impact": {
    "bridge_fee": "0",
    "swap_fee": "500",
    "dst_gas_fee": "0"
  },
  "router": "wheelx",
  "created_at": "2024-01-01T12:00:00Z",
  "points": "10"
}
```

## Usage Flow

### 1. Get Quote
First, call the quote endpoint to get pricing and transaction data.

### 2. Check Approval
If the response includes an `approve` object, you need to approve the spender to spend your tokens before executing the swap.

### 3. Execute Transaction
Use the transaction data from the `tx` object to sign and broadcast the transaction using your preferred Web3 library.

### 4. Monitor Order
Use the `request_id` to track the order status via the `/v1/order/{request_id}` endpoint.

## Error Handling

- **422 Validation Error**: Invalid request parameters
- **500 Internal Server Error**: Server-side issues
- **429 Rate Limit**: Too many requests

## Rate Limits

- Default: 100 requests per minute per IP
- Contact support for higher limits

## Supported Chains

Common chain IDs:
- 1: Ethereum Mainnet
- 56: BSC
- 137: Polygon
- 42161: Arbitrum
- 10: Optimism
- 8453: Base

## Notes

- All amounts are in the smallest units of the token (wei for ETH, 6 decimals for USDC, etc.)
- Quotes are valid for 30 seconds
- Always verify the `min_receive` amount before executing transactions
- Use the `points` field to track rewards for users
