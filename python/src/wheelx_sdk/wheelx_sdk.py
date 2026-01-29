"""
WheelX Python SDK for quote API and transaction execution
"""

import json
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
import requests


@dataclass
class QuoteRequest:
    """Quote request parameters"""
    from_chain: int
    to_chain: int
    from_token: str
    to_token: str
    from_address: str
    to_address: str
    amount: int
    slippage: Optional[int] = None


@dataclass
class Tx:
    """Transaction data"""
    to: str
    value: int
    data: str
    chainId: Optional[int] = None
    gas: Optional[int] = None
    maxFeePerGas: Optional[int] = None
    maxPriorityFeePerGas: Optional[int] = None


@dataclass
class ApproveAction:
    """Approval transaction data"""
    token: str
    spender: str
    amount: int


@dataclass
class PriceImpactFormatted:
    """Price impact breakdown"""
    bridge_fee: str
    swap_fee: str
    dst_gas_fee: str


@dataclass
class TokenInfo:
    """Token information"""
    symbol: str
    name: str
    decimals: int
    address: str
    chain_id: int
    logo: str
    tags: list[str]


@dataclass
class OrderResponse:
    """Order status response data"""
    order_id: str
    from_chain: int
    from_token: str
    from_token_info: Optional[TokenInfo]
    from_address: str
    from_amount: str
    to_chain: int
    to_token: str
    to_token_info: Optional[TokenInfo]
    to_amount: str
    to_address: str
    open_tx_hash: str
    open_block: int
    open_timestamp: str
    fill_tx_hash: Optional[str]
    fill_block: Optional[int]
    fill_timestamp: Optional[str]
    status: str
    points: str


@dataclass
class QuoteResponse:
    """Quote response data"""
    request_id: str
    amount_out: str
    fee: str
    tx: Tx
    approve: Optional[ApproveAction]
    slippage: int
    min_receive: str
    estimated_time: int
    recipient: str
    router_type: str
    price_impact: PriceImpactFormatted
    router: str
    created_at: str
    points: str


class WheelXSDK:
    """WheelX SDK for quote API and transaction execution"""

    def __init__(self, base_url: str = "https://api.wheelx.fi"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_quote(self, quote_request: QuoteRequest) -> QuoteResponse:
        """
        Get a quote for token swap/bridge

        Args:
            quote_request: Quote request parameters

        Returns:
            QuoteResponse: Quote response with transaction data

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/v1/quote"

        payload = {
            "from_chain": quote_request.from_chain,
            "to_chain": quote_request.to_chain,
            "from_token": quote_request.from_token,
            "to_token": quote_request.to_token,
            "from_address": quote_request.from_address,
            "to_address": quote_request.to_address,
            "amount": quote_request.amount,
        }

        if quote_request.slippage is not None:
            payload["slippage"] = quote_request.slippage

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        data = response.json()

        # Parse transaction data
        tx_data = data.get("tx", {})
        tx = Tx(
            to=tx_data.get("to"),
            value=tx_data.get("value", 0),
            data=tx_data.get("data"),
            chainId=tx_data.get("chainId"),
            gas=tx_data.get("gas"),
            maxFeePerGas=tx_data.get("maxFeePerGas"),
            maxPriorityFeePerGas=tx_data.get("maxPriorityFeePerGas")
        )

        # Parse approval data if present
        approve_data = data.get("approve")
        approve = None
        if approve_data:
            approve = ApproveAction(
                token=approve_data.get("token"),
                spender=approve_data.get("spender"),
                amount=approve_data.get("amount")
            )

        # Parse price impact
        price_impact_data = data.get("price_impact", {})
        price_impact = PriceImpactFormatted(
            bridge_fee=price_impact_data.get("bridge_fee", "0"),
            swap_fee=price_impact_data.get("swap_fee", "0"),
            dst_gas_fee=price_impact_data.get("dst_gas_fee", "0")
        )

        return QuoteResponse(
            request_id=data.get("request_id"),
            amount_out=data.get("amount_out"),
            fee=data.get("fee"),
            tx=tx,
            approve=approve,
            slippage=data.get("slippage"),
            min_receive=data.get("min_receive"),
            estimated_time=data.get("estimated_time", 10),
            recipient=data.get("recipient"),
            router_type=data.get("router_type", "swap"),
            price_impact=price_impact,
            router=data.get("router", "wheelx"),
            created_at=data.get("created_at"),
            points=data.get("points", "0")
        )

    def get_order_status(self, request_id: str) -> OrderResponse:
        """
        Get order status by request ID

        Args:
            request_id: Quote request ID

        Returns:
            OrderResponse: Order status information

        Raises:
            Exception: If API request fails
        """
        url = f"{self.base_url}/v1/order/{request_id}"
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()

        # Parse token info if present
        from_token_info_data = data.get("from_token_info")
        from_token_info = None
        if from_token_info_data:
            from_token_info = TokenInfo(
                symbol=from_token_info_data.get("symbol"),
                name=from_token_info_data.get("name"),
                decimals=from_token_info_data.get("decimals"),
                address=from_token_info_data.get("address"),
                chain_id=from_token_info_data.get("chain_id"),
                logo=from_token_info_data.get("logo"),
                tags=from_token_info_data.get("tags", [])
            )

        to_token_info_data = data.get("to_token_info")
        to_token_info = None
        if to_token_info_data:
            to_token_info = TokenInfo(
                symbol=to_token_info_data.get("symbol"),
                name=to_token_info_data.get("name"),
                decimals=to_token_info_data.get("decimals"),
                address=to_token_info_data.get("address"),
                chain_id=to_token_info_data.get("chain_id"),
                logo=to_token_info_data.get("logo"),
                tags=to_token_info_data.get("tags", [])
            )

        return OrderResponse(
            order_id=data.get("order_id"),
            from_chain=data.get("from_chain"),
            from_token=data.get("from_token"),
            from_token_info=from_token_info,
            from_address=data.get("from_address"),
            from_amount=data.get("from_amount"),
            to_chain=data.get("to_chain"),
            to_token=data.get("to_token"),
            to_token_info=to_token_info,
            to_amount=data.get("to_amount"),
            to_address=data.get("to_address"),
            open_tx_hash=data.get("open_tx_hash"),
            open_block=data.get("open_block"),
            open_timestamp=data.get("open_timestamp"),
            fill_tx_hash=data.get("fill_tx_hash"),
            fill_block=data.get("fill_block"),
            fill_timestamp=data.get("fill_timestamp"),
            status=data.get("status"),
            points=data.get("points", "0")
        )


class TransactionExecutor:
    """Helper class for executing transactions using web3.py"""

    def __init__(self, web3_provider_url: str):
        """
        Initialize transaction executor

        Args:
            web3_provider_url: Web3 provider URL (e.g., Infura, Alchemy)
        """
        try:
            from web3 import Web3
            self.web3 = Web3(Web3.HTTPProvider(web3_provider_url))
            if not self.web3.is_connected():
                raise Exception("Failed to connect to Web3 provider")
        except ImportError:
            raise ImportError("web3.py is required for transaction execution. Install with: pip install web3")

    def build_transaction(self, tx_data: Tx, account_address: str) -> Dict[str, Any]:
        """
        Build transaction dictionary for signing

        Args:
            tx_data: Transaction data from quote response
            account_address: User's wallet address

        Returns:
            Dict: Transaction dictionary ready for signing
        """
        transaction = {
            'to': self.web3.to_checksum_address(tx_data.to),
            'value': tx_data.value,
            'data': tx_data.data,
            'chainId': tx_data.chainId,
            'nonce': self.web3.eth.get_transaction_count(account_address),
        }

        # Add gas parameters
        if tx_data.gas:
            transaction['gas'] = tx_data.gas

        # Add EIP-1559 gas parameters
        if tx_data.maxFeePerGas and tx_data.maxPriorityFeePerGas:
            transaction['maxFeePerGas'] = tx_data.maxFeePerGas
            transaction['maxPriorityFeePerGas'] = tx_data.maxPriorityFeePerGas
        else:
            # Fallback to legacy gas
            gas_price = self.web3.eth.gas_price
            transaction['gasPrice'] = gas_price

        return transaction

    def sign_and_send_transaction(self, transaction: Dict[str, Any], private_key: str) -> str:
        """
        Sign and send transaction

        Args:
            transaction: Transaction dictionary
            private_key: Private key for signing

        Returns:
            str: Transaction hash

        Raises:
            Exception: If transaction fails
        """
        signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.web3.to_hex(tx_hash)

    def wait_for_transaction(self, tx_hash: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Wait for transaction confirmation

        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds

        Returns:
            Dict: Transaction receipt
        """
        return self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)


# Example usage
if __name__ == "__main__":
    # Initialize SDK
    sdk = WheelXSDK()

    # Create quote request
    quote_request = QuoteRequest(
        from_chain=1,
        to_chain=1,
        from_token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        to_token="0xdAC17F958D2ee523a2206206994597C13D831ec7",    # USDT
        from_address="0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
        to_address="0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
        amount=1000000,  # 1 USDC (6 decimals)
        slippage=50
    )

    try:
        # Get quote
        quote = sdk.get_quote(quote_request)
        print(f"Quote received: {quote.amount_out} tokens")
        print(f"Request ID: {quote.request_id}")
        print(f"Min receive: {quote.min_receive}")

        # Check if approval is needed
        if quote.approve:
            print(f"Approval needed for token: {quote.approve.token}")
            print(f"Spender: {quote.approve.spender}")
            print(f"Amount: {quote.approve.amount}")

        # Example transaction execution (requires web3 and private key)
        # executor = TransactionExecutor("https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
        # transaction = executor.build_transaction(quote.tx, quote_request.from_address)
        # tx_hash = executor.sign_and_send_transaction(transaction, "YOUR_PRIVATE_KEY")
        # print(f"Transaction sent: {tx_hash}")
        # receipt = executor.wait_for_transaction(tx_hash)
        # print(f"Transaction confirmed in block: {receipt.blockNumber}")

    except Exception as e:
        print(f"Error: {e}")
