package wheelx

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/big"
	"net/http"
	"strconv"
	"time"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
)

// QuoteRequest represents the request parameters for getting a quote
type QuoteRequest struct {
	FromChain   int    `json:"from_chain"`
	ToChain     int    `json:"to_chain"`
	FromToken   string `json:"from_token"`
	ToToken     string `json:"to_token"`
	FromAddress string `json:"from_address"`
	ToAddress   string `json:"to_address"`
	Amount      int    `json:"amount"`
	Slippage    *int   `json:"slippage,omitempty"`
}

// Tx represents transaction data
type Tx struct {
	To                   string  `json:"to"`
	Value                string  `json:"value"`
	Data                 string  `json:"data"`
	ChainId              *int    `json:"chainId,omitempty"`
	Gas                  *string `json:"gas,omitempty"`
	MaxFeePerGas         *string `json:"maxFeePerGas,omitempty"`
	MaxPriorityFeePerGas *string `json:"maxPriorityFeePerGas,omitempty"`
}

// ApproveAction represents approval transaction data
type ApproveAction struct {
	Token   string `json:"token"`
	Spender string `json:"spender"`
	Amount  string `json:"amount"`
}

// PriceImpactFormatted represents price impact breakdown
type PriceImpactFormatted struct {
	BridgeFee string `json:"bridge_fee"`
	SwapFee   string `json:"swap_fee"`
	DstGasFee string `json:"dst_gas_fee"`
}

// RouteInfo represents route information (router name + logo)
type RouteInfo struct {
	Name string `json:"name"`
	Logo string `json:"logo"`
}

// QuoteItem represents an individual router quote within quotes[] array
type QuoteItem struct {
	RequestId string      `json:"request_id"`
	Router    string      `json:"router"`
	AmountOut string      `json:"amount_out"`
	Tx        Tx          `json:"tx"`
	Routes    []RouteInfo `json:"routes"`
	GasFee    *string     `json:"gas_fee,omitempty"`
}

// QuoteResponse represents the quote response
type QuoteResponse struct {
	RequestId      string               `json:"request_id"`
	AmountOut      string               `json:"amount_out"`
	Fee            string               `json:"fee"`
	Tx             Tx                   `json:"tx"`
	Approve        *ApproveAction        `json:"approve,omitempty"`
	Slippage       int                  `json:"slippage"`
	MinReceive     string               `json:"min_receive"`
	EstimatedTime  float64              `json:"estimated_time"`
	Recipient      string               `json:"recipient"`
	RouterType     string               `json:"router_type"`
	PriceImpact    PriceImpactFormatted `json:"price_impact"`
	Router         string               `json:"router"`
	CreatedAt      string               `json:"created_at"`
	Points         string               `json:"points"`
	Quotes         []QuoteItem          `json:"quotes"`
	Routes         []RouteInfo          `json:"routes"`
	DepositAddress *string              `json:"deposit_address,omitempty"`
	GasFee         *string              `json:"gas_fee,omitempty"`
	BridgeOrderId  *string              `json:"bridge_order_id,omitempty"`
	QuoteMessage   *string              `json:"quote_message,omitempty"`
}

// TokenInfo represents token information
type TokenInfo struct {
	Symbol   string   `json:"symbol"`
	Name     string   `json:"name"`
	Decimals int      `json:"decimals"`
	Address  string   `json:"address"`
	ChainID  int      `json:"chain_id"`
	Logo     string   `json:"logo"`
	Tags     []string `json:"tags"`
}

// OrderResponse represents order status response
type OrderResponse struct {
	OrderId       string     `json:"order_id"`
	FromChain     int        `json:"from_chain"`
	FromToken     string     `json:"from_token"`
	FromTokenInfo *TokenInfo `json:"from_token_info,omitempty"`
	FromAddress   string     `json:"from_address"`
	FromAmount    string     `json:"from_amount"`
	ToChain       int        `json:"to_chain"`
	ToToken       string     `json:"to_token"`
	ToTokenInfo   *TokenInfo `json:"to_token_info,omitempty"`
	ToAmount      string     `json:"to_amount"`
	ToAddress     string     `json:"to_address"`
	OpenTxHash    string     `json:"open_tx_hash"`
	OpenBlock     int        `json:"open_block"`
	OpenTimestamp string     `json:"open_timestamp"`
	FillTxHash    *string    `json:"fill_tx_hash,omitempty"`
	FillBlock     *int       `json:"fill_block,omitempty"`
	FillTimestamp *string    `json:"fill_timestamp,omitempty"`
	Status        string     `json:"status"`
	Points        string     `json:"points"`
}

// WheelXSDK provides methods to interact with WheelX API
type WheelXSDK struct {
	BaseURL string
	Client  *http.Client
}

// NewWheelXSDK creates a new WheelX SDK instance
func NewWheelXSDK(baseURL string) *WheelXSDK {
	if baseURL == "" {
		baseURL = "https://api.wheelx.fi"
	}

	return &WheelXSDK{
		BaseURL: baseURL,
		Client:  &http.Client{Timeout: 30 * time.Second},
	}
}

// GetQuote gets a quote for token swap/bridge
func (sdk *WheelXSDK) GetQuote(ctx context.Context, req QuoteRequest) (*QuoteResponse, error) {
	url := sdk.BaseURL + "/v1/quote"

	// Prepare request body
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := sdk.Client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed: %s - %s", resp.Status, string(respBody))
	}

	// Parse response
	var quoteResp QuoteResponse
	if err := json.Unmarshal(respBody, &quoteResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &quoteResp, nil
}

// GetOrderStatus gets order status by request ID
func (sdk *WheelXSDK) GetOrderStatus(ctx context.Context, requestID string) (*OrderResponse, error) {
	url := sdk.BaseURL + "/v1/order/" + requestID

	httpReq, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := sdk.Client.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed: %s - %s", resp.Status, string(respBody))
	}

	var orderResp OrderResponse
	if err := json.Unmarshal(respBody, &orderResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &orderResp, nil
}

// TransactionExecutor provides methods to execute transactions
type TransactionExecutor struct {
	Client *ethclient.Client
}

// NewTransactionExecutor creates a new transaction executor
func NewTransactionExecutor(rpcURL string) (*TransactionExecutor, error) {
	client, err := ethclient.Dial(rpcURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Ethereum client: %w", err)
	}

	return &TransactionExecutor{
		Client: client,
	}, nil
}

// BuildTransaction builds a transaction for signing
func (e *TransactionExecutor) BuildTransaction(ctx context.Context, txData Tx, fromAddress common.Address) (*types.Transaction, error) {
	// Get nonce
	nonce, err := e.Client.PendingNonceAt(ctx, fromAddress)
	if err != nil {
		return nil, fmt.Errorf("failed to get nonce: %w", err)
	}

	// Get gas price
	gasPrice, err := e.Client.SuggestGasPrice(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get gas price: %w", err)
	}

	// Parse transaction data
	data := common.FromHex(txData.Data)
	to := common.HexToAddress(txData.To)

	// Parse Value from string to big.Int
	value := new(big.Int)
	if txData.Value != "" {
		value.SetString(txData.Value, 10)
	}

	// Parse Gas from string
	var gasLimit uint64
	if txData.Gas != nil && *txData.Gas != "" {
		gasLimit, _ = strconv.ParseUint(*txData.Gas, 10, 64)
	}

	// Create transaction
	tx := types.NewTx(&types.LegacyTx{
		Nonce:    nonce,
		To:       &to,
		Value:    value,
		Gas:      gasLimit,
		GasPrice: gasPrice,
		Data:     data,
	})

	return tx, nil
}

// BuildEIP1559Transaction builds an EIP-1559 transaction
func (e *TransactionExecutor) BuildEIP1559Transaction(ctx context.Context, txData Tx, fromAddress common.Address) (*types.Transaction, error) {
	// Get nonce
	nonce, err := e.Client.PendingNonceAt(ctx, fromAddress)
	if err != nil {
		return nil, fmt.Errorf("failed to get nonce: %w", err)
	}

	// Get chain ID
	chainID, err := e.Client.ChainID(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get chain ID: %w", err)
	}

	// Get gas tip cap (priority fee)
	gasTipCap, err := e.Client.SuggestGasTipCap(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get gas tip cap: %w", err)
	}

	// Get gas fee cap
	header, err := e.Client.HeaderByNumber(ctx, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get header: %w", err)
	}
	baseFee := new(big.Int).Mul(header.BaseFee, big.NewInt(2))
	gasFeeCap := new(big.Int).Add(gasTipCap, baseFee)

	// Parse transaction data
	data := common.FromHex(txData.Data)
	to := common.HexToAddress(txData.To)

	// Create EIP-1559 transaction
	// Parse Value and Gas from string
	eipValue := new(big.Int)
	if txData.Value != "" {
		eipValue.SetString(txData.Value, 10)
	}
	var eipGas uint64
	if txData.Gas != nil && *txData.Gas != "" {
		eipGas, _ = strconv.ParseUint(*txData.Gas, 10, 64)
	}

	tx := types.NewTx(&types.DynamicFeeTx{
		ChainID:   chainID,
		Nonce:     nonce,
		GasTipCap: gasTipCap,
		GasFeeCap: gasFeeCap,
		Gas:       eipGas,
		To:        &to,
		Value:     eipValue,
		Data:      data,
	})

	return tx, nil
}

// SignAndSendTransaction signs and sends a transaction
func (e *TransactionExecutor) SignAndSendTransaction(ctx context.Context, tx *types.Transaction, privateKey string) (common.Hash, error) {
	// Parse private key
	key, err := crypto.HexToECDSA(privateKey)
	if err != nil {
		return common.Hash{}, fmt.Errorf("failed to parse private key: %w", err)
	}

	// Get chain ID
	chainID, err := e.Client.ChainID(ctx)
	if err != nil {
		return common.Hash{}, fmt.Errorf("failed to get chain ID: %w", err)
	}

	// Sign transaction
	signedTx, err := types.SignTx(tx, types.NewEIP155Signer(chainID), key)
	if err != nil {
		return common.Hash{}, fmt.Errorf("failed to sign transaction: %w", err)
	}

	// Send transaction
	err = e.Client.SendTransaction(ctx, signedTx)
	if err != nil {
		return common.Hash{}, fmt.Errorf("failed to send transaction: %w", err)
	}

	return signedTx.Hash(), nil
}

// WaitForTransaction waits for transaction confirmation
func (e *TransactionExecutor) WaitForTransaction(ctx context.Context, txHash common.Hash) (*types.Receipt, error) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-ticker.C:
			receipt, err := e.Client.TransactionReceipt(ctx, txHash)
			if err != nil {
				if err.Error() == "not found" {
					continue
				}
				return nil, fmt.Errorf("failed to get transaction receipt: %w", err)
			}
			return receipt, nil
		}
	}
}

// Example usage
/*
func main() {
	// Initialize SDK
	sdk := NewWheelXSDK("")

	// Create quote request
	req := QuoteRequest{
		FromChain:   1,
		ToChain:     1,
		FromToken:   "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
		ToToken:     "0xdAC17F958D2ee523a2206206994597C13D831ec7",   // USDT
		FromAddress: "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
		ToAddress:   "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
		Amount:      1000000, // 1 USDC (6 decimals)
		Slippage:    &[]int{50}[0],
	}

	// Get quote
	ctx := context.Background()
	quote, err := sdk.GetQuote(ctx, req)
	if err != nil {
		log.Fatalf("Failed to get quote: %v", err)
	}

	fmt.Printf("Quote received: %s tokens\n", quote.AmountOut)
	fmt.Printf("Request ID: %s\n", quote.RequestId)
	fmt.Printf("Min receive: %s\n", quote.MinReceive)

	// Check if approval is needed
	if quote.Approve != nil {
		fmt.Printf("Approval needed for token: %s\n", quote.Approve.Token)
		fmt.Printf("Spender: %s\n", quote.Approve.Spender)
		fmt.Printf("Amount: %s\n", quote.Approve.Amount)
	}

	// Example transaction execution (requires Ethereum client and private key)
	// executor, err := NewTransactionExecutor("https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
	// if err != nil {
	//     log.Fatalf("Failed to create executor: %v", err)
	// }
	//
	// fromAddress := common.HexToAddress(req.FromAddress)
	// tx, err := executor.BuildEIP1559Transaction(ctx, quote.Tx, fromAddress)
	// if err != nil {
	//     log.Fatalf("Failed to build transaction: %v", err)
	// }
	//
	// txHash, err := executor.SignAndSendTransaction(ctx, tx, "YOUR_PRIVATE_KEY")
	// if err != nil {
	//     log.Fatalf("Failed to send transaction: %v", err)
	// }
	//
	// fmt.Printf("Transaction sent: %s\n", txHash.Hex())
	//
	// receipt, err := executor.WaitForTransaction(ctx, txHash)
	// if err != nil {
	//     log.Fatalf("Failed to wait for transaction: %v", err)
	// }
	//
	// fmt.Printf("Transaction confirmed in block: %d\n", receipt.BlockNumber)
}
*/
