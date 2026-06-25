package main

import (
	"context"
	"fmt"
	"log"

	"github.com/wheelx-fi/wheelx-sdk/go/wheelx"
)

func main() {
	// Initialize SDK
	sdk := wheelx.NewWheelXSDK("")

	// Create quote request for USDC to USDT swap on Ethereum
	req := wheelx.QuoteRequest{
		FromChain:   1,                                            // Ethereum
		ToChain:     1,                                            // Ethereum
		FromToken:   "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
		ToToken:     "0xdAC17F958D2ee523a2206206994597C13D831ec7", // USDT
		FromAddress: "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
		ToAddress:   "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
		Amount:      1000000,       // 1 USDC (6 decimals)
		Slippage:    &[]int{50}[0], // 0.5% slippage
	}

	// Get quote
	ctx := context.Background()
	quote, err := sdk.GetQuote(ctx, req)
	if err != nil {
		log.Fatalf("Failed to get quote: %v", err)
	}

	fmt.Println("=== Quote Received ===")
	fmt.Printf("Request ID: %s\n", quote.RequestId)
	fmt.Printf("From: %d USDC\n", req.Amount)
	fmt.Printf("To: %s USDT\n", quote.AmountOut)
	fmt.Printf("Fee: %s USDT\n", quote.Fee)
	fmt.Printf("Min Receive: %s USDT\n", quote.MinReceive)
	fmt.Printf("Slippage: %.2f%%\n", float64(quote.Slippage)/100)
	fmt.Printf("Estimated Time: %d seconds\n", quote.EstimatedTime)
	fmt.Printf("Points Earned: %s\n", quote.Points)

	// Check if approval is needed
	if quote.Approve != nil {
		fmt.Println("\n=== Approval Required ===")
		fmt.Printf("Token: %s\n", quote.Approve.Token)
		fmt.Printf("Spender: %s\n", quote.Approve.Spender)
		fmt.Printf("Amount: %s\n", quote.Approve.Amount)
	}

	// Show transaction details
	fmt.Println("\n=== Transaction Details ===")
	fmt.Printf("To: %s\n", quote.Tx.To)
	fmt.Printf("Value: %s wei\n", quote.Tx.Value)
	if quote.Tx.Gas != nil {
		fmt.Printf("Gas: %s\n", *quote.Tx.Gas)
	}
	if len(quote.Tx.Data) > 50 {
		fmt.Printf("Data: %s...\n", quote.Tx.Data[:50])
	} else {
		fmt.Printf("Data: %s\n", quote.Tx.Data)
	}

	// Example of checking order status
	fmt.Println("\n=== Order Status Query Example ===")
	fmt.Printf("You can check order status later using request ID: %s\n", quote.RequestId)
	fmt.Println("Example code:")
	fmt.Printf("  orderStatus, err := sdk.GetOrderStatus(ctx, \"%s\")\n", quote.RequestId)
	fmt.Printf("  if err != nil {\n")
	fmt.Printf("      log.Fatal(err)\n")
	fmt.Printf("  }\n")
	fmt.Printf("  fmt.Println(\"Order Status:\", orderStatus.Status)\n")

	// Example of transaction execution (commented out for safety)
	// Uncomment and provide your private key to execute
	//
	// executor, err := wheelx.NewTransactionExecutor("https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
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
	// fmt.Printf("\nTransaction sent: %s\n", txHash.Hex())
	//
	// receipt, err := executor.WaitForTransaction(ctx, txHash)
	// if err != nil {
	//     log.Fatalf("Failed to wait for transaction: %v", err)
	// }
	//
	// fmt.Printf("Transaction confirmed in block: %d\n", receipt.BlockNumber)
}
