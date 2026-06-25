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
  value: string;
  data: string;
  chainId?: number;
  gas?: string | null;
  maxFeePerGas?: string | null;
  maxPriorityFeePerGas?: string | null;
}

export interface ApproveAction {
  token: string;
  spender: string;
  amount: string;
}

export interface PriceImpactFormatted {
  bridge_fee: string;
  swap_fee: string;
  dst_gas_fee: string;
}

export interface RouteInfo {
  name: string;
  logo: string;
}

export interface QuoteItem {
  request_id: string;
  router: string;
  amount_out: string;
  tx: Tx;
  routes: RouteInfo[];
  gas_fee?: string | null;
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
  quotes: QuoteItem[];
  routes: RouteInfo[];
  deposit_address?: string | null;
  gas_fee?: string | null;
  bridge_order_id?: string | null;
  quote_message?: string | null;
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
  routes: string[];
  bridge_order_id?: string | null;
  deposit_address?: string | null;
  to_platform_id?: number | null;
  order_value?: string | null;
  reward_type?: string | null;
  reward_value?: string | null;
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
