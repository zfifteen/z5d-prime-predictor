/**
 * Z-Ghost Wallet Interface
 * 
 * Drop-in replacement for standard HD wallet functions using Z-Ghost Protocol
 * for ephemeral address generation. Provides a familiar API while delivering
 * superior privacy through Z5D prime prediction-based key derivation.
 * 
 * Key Differences from Standard HD Wallets:
 * - No xpub/xprv support (no derivation path exposure)
 * - Addresses cannot be linked through derivation analysis
 * - Each address requires the master seed to derive the private key
 * 
 * MIT Licensed - No patent claims
 */

import { ZGhostAddressGen, AddressGenerationResult, ZGhostAddressGenConfig } from '../core/zGhostAddressGen';
import { PrivacyScore, PrivacyScoreResult } from '../metrics/privacyScore';
import { createHash, randomBytes } from 'crypto';

/**
 * Wallet configuration options
 */
export interface ZGhostWalletConfig extends ZGhostAddressGenConfig {
  /** Network (mainnet or testnet) - affects address format */
  network?: 'mainnet' | 'testnet';
  /** Maximum number of addresses to cache */
  maxCacheSize?: number;
  /** Enable privacy scoring on batch operations */
  enablePrivacyScoring?: boolean;
}

/**
 * Address info returned by wallet methods
 */
export interface AddressInfo {
  /** Bitcoin address string */
  address: string;
  /** Transaction index used to derive this address */
  index: number;
  /** Whether this address has been used before (from cache) */
  isNew: boolean;
}

/**
 * Wallet state information
 */
export interface WalletState {
  /** Current address index (next unused) */
  currentIndex: number;
  /** Number of addresses generated so far */
  addressesGenerated: number;
  /** Number of addresses in cache */
  cachedAddresses: number;
  /** Latest privacy score (if enabled) */
  privacyScore?: number;
}

/**
 * Z-Ghost Wallet
 * 
 * Provides wallet functionality using Z-Ghost Protocol for enhanced privacy.
 * Designed as a drop-in replacement for standard HD wallet interfaces.
 */
export class ZGhostWallet {
  private generator: ZGhostAddressGen;
  private config: ZGhostWalletConfig;
  private currentIndex: number;
  private addressCache: Map<string, AddressGenerationResult>;
  private indexToAddress: Map<number, string>;
  private seedFingerprint: string;

  /**
   * Create a new Z-Ghost Wallet
   * 
   * @param seed - Master seed (256 bits / 32 bytes as hex or Buffer)
   * @param config - Wallet configuration options
   */
  constructor(seed: Buffer | string, config: ZGhostWalletConfig = {}) {
    const seedBuffer = typeof seed === 'string' ? Buffer.from(seed, 'hex') : seed;
    
    if (seedBuffer.length !== 32) {
      throw new Error('Seed must be exactly 256 bits (32 bytes)');
    }
    
    this.config = {
      network: config.network ?? 'mainnet',
      maxCacheSize: config.maxCacheSize ?? 10000,
      enablePrivacyScoring: config.enablePrivacyScoring ?? false,
      ...config,
    };
    
    this.generator = new ZGhostAddressGen(seedBuffer, this.config);
    this.currentIndex = 0;
    this.addressCache = new Map();
    this.indexToAddress = new Map();
    
    // Create seed fingerprint (first 4 bytes of double SHA256)
    const hash1 = createHash('sha256').update(seedBuffer).digest();
    const hash2 = createHash('sha256').update(hash1).digest();
    this.seedFingerprint = hash2.subarray(0, 4).toString('hex');
  }

  /**
   * Create a new wallet with a randomly generated seed
   * 
   * @param config - Wallet configuration options
   * @returns New ZGhostWallet instance and the generated seed
   */
  static create(config: ZGhostWalletConfig = {}): { wallet: ZGhostWallet; seed: Buffer } {
    const seed = randomBytes(32);
    const wallet = new ZGhostWallet(seed, config);
    return { wallet, seed };
  }

  /**
   * Create a wallet from a mnemonic phrase (BIP39 compatible)
   * Note: This is a simplified implementation. For production use,
   * proper BIP39 mnemonic handling should be used.
   * 
   * @param mnemonic - Space-separated mnemonic words
   * @param passphrase - Optional passphrase
   * @param config - Wallet configuration options
   * @returns ZGhostWallet instance
   */
  static fromMnemonic(
    mnemonic: string,
    passphrase: string = '',
    config: ZGhostWalletConfig = {}
  ): ZGhostWallet {
    // Simple PBKDF2-like derivation (simplified for this implementation)
    // In production, use proper BIP39 implementation
    const salt = `mnemonic${passphrase}`;
    const mnemonicBuffer = Buffer.from(mnemonic.normalize('NFKD'), 'utf8');
    const saltBuffer = Buffer.from(salt.normalize('NFKD'), 'utf8');
    
    // Iterative hashing to derive seed
    let derived = createHash('sha512').update(mnemonicBuffer).update(saltBuffer).digest();
    for (let i = 0; i < 2048; i++) {
      derived = createHash('sha512').update(derived).update(saltBuffer).digest();
    }
    
    // Use first 32 bytes as seed
    const seed = derived.subarray(0, 32);
    return new ZGhostWallet(seed, config);
  }

  /**
   * Get a new unused address
   * 
   * @returns New address info
   */
  getNewAddress(): AddressInfo {
    const result = this.generateAtIndex(this.currentIndex);
    this.currentIndex++;
    
    return {
      address: result.address,
      index: result.index,
      isNew: true,
    };
  }

  /**
   * Get multiple new addresses
   * 
   * @param count - Number of addresses to generate
   * @returns Array of address info
   */
  getNewAddresses(count: number): AddressInfo[] {
    if (count <= 0 || !Number.isInteger(count)) {
      throw new Error('Count must be a positive integer');
    }
    
    const addresses: AddressInfo[] = [];
    for (let i = 0; i < count; i++) {
      addresses.push(this.getNewAddress());
    }
    
    return addresses;
  }

  /**
   * Get address at a specific index (may return cached address)
   * 
   * @param index - Transaction index
   * @returns Address info
   */
  getAddressAtIndex(index: number): AddressInfo {
    if (index < 0 || !Number.isInteger(index)) {
      throw new Error('Index must be a non-negative integer');
    }
    
    const cachedAddress = this.indexToAddress.get(index);
    if (cachedAddress) {
      return {
        address: cachedAddress,
        index,
        isNew: false,
      };
    }
    
    const result = this.generateAtIndex(index);
    return {
      address: result.address,
      index,
      isNew: true,
    };
  }

  /**
   * Get the private key for a specific address
   * 
   * @param address - Bitcoin address string
   * @returns Private key as hex string, or null if address not found
   */
  getPrivateKey(address: string): string | null {
    const cached = this.addressCache.get(address);
    if (cached) {
      return cached.privateKey;
    }
    
    // Address not in cache - cannot derive without knowing the index
    // In a real implementation, you might scan recent indices
    return null;
  }

  /**
   * Get the private key for an address by its index
   * 
   * @param index - Transaction index
   * @returns Private key as hex string
   */
  getPrivateKeyAtIndex(index: number): string {
    if (index < 0 || !Number.isInteger(index)) {
      throw new Error('Index must be a non-negative integer');
    }
    
    const cachedAddress = this.indexToAddress.get(index);
    if (cachedAddress) {
      const cached = this.addressCache.get(cachedAddress);
      if (cached) {
        return cached.privateKey;
      }
    }
    
    const result = this.generateAtIndex(index);
    return result.privateKey;
  }

  /**
   * Export extended public key - NOT SUPPORTED in Z-Ghost Protocol
   * 
   * @throws Error always - Z-Ghost does not support xpub
   */
  exportXPub(): never {
    throw new Error(
      'Z-Ghost Protocol does not support extended public keys (xpub). ' +
      'This is by design - xpub export would compromise the privacy benefits ' +
      'of Z-Ghost by exposing the derivation pattern. Each address must be ' +
      'derived from the master seed independently.'
    );
  }

  /**
   * Export extended private key - NOT SUPPORTED in Z-Ghost Protocol
   * 
   * @throws Error always - Z-Ghost does not support xprv
   */
  exportXPrv(): never {
    throw new Error(
      'Z-Ghost Protocol does not support extended private keys (xprv). ' +
      'Use the master seed directly for wallet backup and recovery.'
    );
  }

  /**
   * Check if an address belongs to this wallet
   * 
   * @param address - Bitcoin address to check
   * @returns True if address is in cache (derived from this wallet)
   */
  isOwnAddress(address: string): boolean {
    return this.addressCache.has(address);
  }

  /**
   * Find the index for a given address
   * 
   * @param address - Bitcoin address to find
   * @returns Index if found, null otherwise
   */
  findAddressIndex(address: string): number | null {
    const cached = this.addressCache.get(address);
    return cached?.index ?? null;
  }

  /**
   * Get current wallet state
   * 
   * @returns Wallet state information
   */
  getState(): WalletState {
    return {
      currentIndex: this.currentIndex,
      addressesGenerated: this.addressCache.size,
      cachedAddresses: this.addressCache.size,
      privacyScore: undefined, // Will be populated if privacy scoring is enabled
    };
  }

  /**
   * Calculate privacy score for generated addresses
   * 
   * @returns Privacy score result
   */
  calculatePrivacyScore(): PrivacyScoreResult {
    const entries = Array.from(this.addressCache.values());
    
    if (entries.length < 2) {
      throw new Error('At least 2 addresses are required to calculate privacy score');
    }
    
    const addresses = entries.map(e => e.address);
    const privateKeys = entries.map(e => Buffer.from(e.privateKey, 'hex'));
    
    return PrivacyScore.calculate(addresses, privateKeys);
  }

  /**
   * Generate privacy report for the wallet
   * 
   * @returns Formatted privacy report string
   */
  generatePrivacyReport(): string {
    const score = this.calculatePrivacyScore();
    return PrivacyScore.generateReport(score);
  }

  /**
   * Get the seed fingerprint (for wallet identification without exposing seed)
   * 
   * @returns 8-character hex fingerprint
   */
  getFingerprint(): string {
    return this.seedFingerprint;
  }

  /**
   * Reset the wallet index (for testing or recovery scenarios)
   * 
   * @param newIndex - New starting index (default: 0)
   */
  resetIndex(newIndex: number = 0): void {
    if (newIndex < 0 || !Number.isInteger(newIndex)) {
      throw new Error('Index must be a non-negative integer');
    }
    this.currentIndex = newIndex;
  }

  /**
   * Clear the address cache
   * Useful for memory management or starting fresh
   */
  clearCache(): void {
    this.addressCache.clear();
    this.indexToAddress.clear();
    this.generator.clearCache();
  }

  /**
   * Internal method to generate address at specific index and cache it
   */
  private generateAtIndex(index: number): AddressGenerationResult {
    const result = this.generator.generate(index);
    
    // Cache the result
    this.cacheResult(result);
    
    return result;
  }

  /**
   * Internal method to cache an address generation result
   */
  private cacheResult(result: AddressGenerationResult): void {
    // Enforce cache size limit
    if (this.addressCache.size >= (this.config.maxCacheSize ?? 10000)) {
      // Remove oldest entries (first 10%)
      const toRemove = Math.floor(this.addressCache.size * 0.1);
      const keys = Array.from(this.addressCache.keys()).slice(0, toRemove);
      for (const key of keys) {
        const entry = this.addressCache.get(key);
        if (entry) {
          this.indexToAddress.delete(entry.index);
        }
        this.addressCache.delete(key);
      }
    }
    
    this.addressCache.set(result.address, result);
    this.indexToAddress.set(result.index, result.address);
  }
}

// Export default for convenience
export default ZGhostWallet;
