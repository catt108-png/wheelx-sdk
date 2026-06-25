/**
 * Type definitions for WheelX SDK
 */

import type { TransactionReceipt } from 'ethers';

export interface QuoteRequest {
  from_chain: number;
  to_chain: number;
  from_token: string;
  to_token: string;
  from_address: string;
  to_address: string;
  amount: number;
  slippage?: number;
}

export interface Tx {
  to: string;
  value: number;
  data: string;
  chainId?: number;
  gas?: number;
  maxFeePerGas?: number;
  maxPriorityFeePerGas?: number;
}

export interface ApproveAction {
  token: string;
  spender: string;
  amount: number;
}

export interface PriceImpactFormatted {
  bridge_fee: string;
  swap_fee: string;
  dst_gas_fee: string;
}

export interface QuoteResponse {
  request_id: string;
  amount_out: string;
  fee: string;
  tx: Tx;
  approve?: ApproveAction;
  slippage: number;
  min_receive: string;
  estimated_time: number;
  recipient: string;
  router_type: string;
  price_impact: PriceImpactFormatted;
  router: string;
  created_at: string;
  points: string;
}

export interface OrderResponse {
  order_id: string;
  from_chain: number;
  from_token: string;
  from_token_info?: TokenInfo | null;
  from_address: string;
  from_amount: string;
  to_chain: number;
  to_token: string;
  to_token_info?: TokenInfo | null;
  to_amount: string;
  to_address: string;
  open_tx_hash: string;
  open_block: number;
  open_timestamp: string;
  fill_tx_hash?: string | null;
  fill_block?: number | null;
  fill_timestamp?: string | null;
  status: OrderStatus;
  points: string;
}

export interface TokenInfo {
  symbol: string;
  name: string;
  decimals: number;
  address: string;
  chain_id: number;
  logo: string;
  tags: string[];
}

export type OrderStatus = 'Open' | 'Filled' | 'Failed' | 'Refund';

export interface SDKConfig {
  baseUrl?: string;
  timeout?: number;
}

export interface TransactionConfig {
  gasLimit?: number;
  maxFeePerGas?: bigint;
  maxPriorityFeePerGas?: bigint;
  nonce?: number;
}

export interface TransactionResult {
  hash: string;
  wait: () => Promise<TransactionReceipt | null>;
}
