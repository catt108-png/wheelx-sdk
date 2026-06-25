import {
  QuoteRequest,
  QuoteResponse,
  OrderResponse,
  SDKConfig,
} from './types';
import { APIError, NetworkError, ValidationError } from './errors';

/**
 * WheelX SDK for interacting with the quote API
 */
export class WheelXSDK {
  private baseUrl: string;
  private timeout: number;

  constructor(config: SDKConfig = {}) {
    this.baseUrl = config.baseUrl || 'https://api.wheelx.fi';
    this.timeout = config.timeout || 30000;
  }

  /**
   * Get a quote for token swap/bridge
   */
  async getQuote(quoteRequest: QuoteRequest): Promise<QuoteResponse> {
    this.validateQuoteRequest(quoteRequest);

    const url = `${this.baseUrl}/v1/quote`;
    const payload = {
      from_chain: quoteRequest.from_chain,
      to_chain: quoteRequest.to_chain,
      from_token: quoteRequest.from_token,
      to_token: quoteRequest.to_token,
      from_address: quoteRequest.from_address,
      to_address: quoteRequest.to_address,
      amount: quoteRequest.amount,
      ...(quoteRequest.slippage !== undefined && { slippage: quoteRequest.slippage }),
    };

    try {
      const response = await this.fetchWithTimeout(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail?.[0]?.msg || errorMessage;
        } catch {
          // Ignore JSON parsing errors
        }
        throw new APIError(errorMessage, response.status);
      }

      const data = await response.json();
      return data as QuoteResponse;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new NetworkError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  /**
   * Get order status by request ID
   */
  async getOrderStatus(requestId: string): Promise<OrderResponse> {
    if (!requestId) {
      throw new ValidationError('Request ID is required');
    }

    const url = `${this.baseUrl}/v1/order/${requestId}`;

    try {
      const response = await this.fetchWithTimeout(url);

      if (!response.ok) {
        throw new APIError(`HTTP ${response.status}`, response.status);
      }

      const data = await response.json();
      return data as OrderResponse;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new NetworkError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  /**
   * Validate quote request parameters
   */
  private validateQuoteRequest(request: QuoteRequest): void {
    if (!request.from_chain || !request.to_chain) {
      throw new ValidationError('Chain IDs are required');
    }

    if (!request.from_token || !request.to_token) {
      throw new ValidationError('Token addresses are required');
    }

    if (!request.from_address || !request.to_address) {
      throw new ValidationError('Addresses are required');
    }

    if (!request.amount || request.amount <= 0) {
      throw new ValidationError('Valid amount is required');
    }

    if (request.slippage !== undefined && (request.slippage < 0 || request.slippage > 10000)) {
      throw new ValidationError('Slippage must be between 0 and 10000 (0-100%)');
    }
  }

  /**
   * Fetch with timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout');
      }
      throw error;
    }
  }
}
