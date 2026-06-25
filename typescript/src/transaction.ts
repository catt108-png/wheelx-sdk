import { ethers } from 'ethers';
import { Tx, TransactionConfig, TransactionResult } from './types';
import { TransactionError } from './errors';

/**
 * Transaction executor for WheelX SDK
 */
export class TransactionExecutor {
  private provider: ethers.Provider;
  private signer?: ethers.Signer;

  constructor(provider: ethers.Provider | string, signer?: ethers.Signer) {
    if (typeof provider === 'string') {
      this.provider = new ethers.JsonRpcProvider(provider);
    } else {
      this.provider = provider;
    }
    this.signer = signer;
  }

  /**
   * Set signer for transaction execution
   */
  setSigner(signer: ethers.Signer): void {
    this.signer = signer;
  }

  /**
   * Build transaction from quote response
   */
  async buildTransaction(
    txData: Tx,
    fromAddress: string,
    config: TransactionConfig = {}
  ): Promise<ethers.TransactionRequest> {
    if (!this.signer) {
      throw new TransactionError('Signer is required for transaction building');
    }

    const transaction: ethers.TransactionRequest = {
      to: txData.to,
      value: BigInt(txData.value),
      data: txData.data,
      chainId: txData.chainId,
    };

    // Get nonce if not provided
    if (config.nonce === undefined) {
      transaction.nonce = await this.provider.getTransactionCount(fromAddress);
    } else {
      transaction.nonce = config.nonce;
    }

    // Handle gas parameters
    if (txData.maxFeePerGas && txData.maxPriorityFeePerGas) {
      // EIP-1559 transaction
      transaction.maxFeePerGas = BigInt(txData.maxFeePerGas);
      transaction.maxPriorityFeePerGas = BigInt(txData.maxPriorityFeePerGas);
    } else {
      // Legacy transaction
      transaction.gasPrice = await this.provider.getFeeData().then(data => data.gasPrice);
    }

    // Handle gas limit
    if (config.gasLimit) {
      transaction.gasLimit = BigInt(config.gasLimit);
    } else if (txData.gas) {
      transaction.gasLimit = BigInt(txData.gas);
    } else {
      // Estimate gas if not provided
      try {
        transaction.gasLimit = await this.provider.estimateGas({
          ...transaction,
          from: fromAddress,
        });
      } catch (error) {
        throw new TransactionError(
          `Failed to estimate gas: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      }
    }

    // Override with custom config
    if (config.maxFeePerGas) {
      transaction.maxFeePerGas = config.maxFeePerGas;
    }
    if (config.maxPriorityFeePerGas) {
      transaction.maxPriorityFeePerGas = config.maxPriorityFeePerGas;
    }

    return transaction;
  }

  /**
   * Sign and send transaction
   */
  async signAndSendTransaction(
    transaction: ethers.TransactionRequest
  ): Promise<TransactionResult> {
    if (!this.signer) {
      throw new TransactionError('Signer is required for transaction execution');
    }

    try {
      const txResponse = await this.signer.sendTransaction(transaction);

      return {
        hash: txResponse.hash,
        wait: () => txResponse.wait(),
      };
    } catch (error) {
      throw new TransactionError(
        `Failed to send transaction: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Execute quote transaction
   */
  async executeQuoteTransaction(
    txData: Tx,
    fromAddress: string,
    config: TransactionConfig = {}
  ): Promise<TransactionResult> {
    const transaction = await this.buildTransaction(txData, fromAddress, config);
    return this.signAndSendTransaction(transaction);
  }

  /**
   * Wait for transaction confirmation
   */
  async waitForTransaction(
    txHash: string,
    confirmations: number = 1,
    timeout: number = 120000
  ): Promise<ethers.TransactionReceipt> {
    try {
      const receipt = await this.provider.waitForTransaction(txHash, confirmations, timeout);

      if (!receipt) {
        throw new TransactionError('Transaction receipt not found');
      }

      if (receipt.status === 0) {
        throw new TransactionError('Transaction failed');
      }

      return receipt;
    } catch (error) {
      if (error instanceof TransactionError) {
        throw error;
      }
      throw new TransactionError(
        `Failed to wait for transaction: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Get transaction receipt
   */
  async getTransactionReceipt(txHash: string): Promise<ethers.TransactionReceipt | null> {
    return this.provider.getTransactionReceipt(txHash);
  }

  /**
   * Get transaction status
   */
  async getTransactionStatus(txHash: string): Promise<'pending' | 'confirmed' | 'failed'> {
    const receipt = await this.getTransactionReceipt(txHash);

    if (!receipt) {
      return 'pending';
    }

    return receipt.status === 1 ? 'confirmed' : 'failed';
  }
}