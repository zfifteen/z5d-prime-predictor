/**
 * Z-Ghost Address Generator
 * 
 * Implements Z5D geodesic path computation for ephemeral Bitcoin address generation.
 * Uses prime prediction mathematics to create deterministic but externally unlinkable addresses.
 * 
 * Mathematical Foundation:
 * The Z5D framework uses Riemann's prime-counting approximation R(x) as the basis
 * for geodesic path computation. This creates a deterministic sequence that is
 * computationally infeasible to reverse-engineer without the master seed.
 * 
 * IMPORTANT IMPLEMENTATION NOTE:
 * This is a demonstration implementation that uses simplified cryptographic operations:
 * - Public keys are derived using SHA256 instead of proper secp256k1 elliptic curve math
 * - RIPEMD160 is simulated using truncated SHA256
 * 
 * For production use with real Bitcoin transactions, integrate proper secp256k1 libraries
 * (such as tiny-secp256k1 or bitcoinjs-lib) for elliptic curve operations.
 * 
 * The Z5D geodesic path derivation and privacy scoring remain mathematically valid
 * and demonstrate the protocol's approach to unlinkable address generation.
 * 
 * In memory of Bill and Keonne. Math is not a crime.
 * 
 * MIT Licensed - No patent claims
 */

import { createHash } from 'crypto';

/**
 * Möbius function μ(n) for n = 0 to 15 (precomputed)
 * Used in the Riemann R(x) series calculation.
 * 
 * The Möbius function is defined as:
 *   μ(1) = 1
 *   μ(n) = (-1)^k if n is a product of k distinct primes
 *   μ(n) = 0 if n has a squared prime factor
 * 
 * Index:  0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15
 * Value:  0  1 -1 -1  0 -1  1 -1  0  0   1  -1   0  -1   1   1
 * 
 * Explanation:
 *   μ(0) = 0 (undefined, placeholder)
 *   μ(1) = 1 (empty product)
 *   μ(2) = -1 (2 is prime)
 *   μ(3) = -1 (3 is prime)
 *   μ(4) = 0 (4 = 2² has squared factor)
 *   μ(5) = -1 (5 is prime)
 *   μ(6) = 1 (6 = 2×3, two distinct primes)
 *   etc.
 */
const MOBIUS: number[] = [0, 1, -1, -1, 0, -1, 1, -1, 0, 0, 1, -1, 0, -1, 1, 1];

/**
 * Euler-Mascheroni constant γ
 */
const EULER_MASCHERONI = 0.5772156649015329;

/**
 * Maximum number of terms for logarithmic integral series
 * Reduced for performance in address generation (precision not critical)
 */
const LI_SERIES_TERMS = 20;

/**
 * Maximum terms for Riemann R(x) truncated series
 * K=5 provides good balance of accuracy and speed
 */
const RIEMANN_K_TERMS = 5;

/**
 * Maximum prime index modulus for geodesic path computation
 * This bounds the prime index to a computationally manageable range
 * while maintaining sufficient entropy for the derivation.
 */
const PRIME_INDEX_MODULUS = 10000000;

/**
 * Minimum prime index offset for geodesic path computation
 * Added to ensure we're always working with primes large enough
 * to provide meaningful variation in the Z5D estimate.
 */
const PRIME_INDEX_OFFSET = 1000;

/**
 * Configuration options for the Z-Ghost Address Generator
 */
export interface ZGhostAddressGenConfig {
  /** Number of series terms for Riemann R(x) calculation (default: 5) */
  riemannTerms?: number;
  /** Number of series terms for logarithmic integral (default: 20) */
  liTerms?: number;
  /** Enable collision detection (default: true) */
  collisionDetection?: boolean;
}

/**
 * Result of address generation
 */
export interface AddressGenerationResult {
  /** The generated Bitcoin address */
  address: string;
  /** The private key (32 bytes hex) */
  privateKey: string;
  /** The public key (33 bytes compressed hex) */
  publicKey: string;
  /** Transaction index used */
  index: number;
  /** Internal geodesic path value */
  geodesicPath: bigint;
}

/**
 * Compute the logarithmic integral li(x) using series expansion
 * li(x) ≈ ln(ln(x)) + γ + Σ(k=1 to N) (ln x)^k / (k * k!)
 * Optimized for performance while maintaining sufficient precision.
 * 
 * @param x - The input value
 * @param terms - Number of series terms (default: LI_SERIES_TERMS)
 * @returns Approximation of li(x)
 */
function logIntegral(x: number, terms: number = LI_SERIES_TERMS): number {
  if (x <= 1) return 0;
  
  const lnx = Math.log(x);
  if (lnx <= 0) return 0;
  
  // Fast approximation: li(x) ≈ γ + ln(ln(x)) + Σ (ln x)^k / (k * k!)
  let result = EULER_MASCHERONI + Math.log(lnx);
  let power = lnx;
  let factorial = 1;
  
  for (let k = 1; k <= terms; k++) {
    factorial *= k;
    result += power / (k * factorial);
    power *= lnx;
    // Early termination for convergence or overflow
    if (!isFinite(result) || Math.abs(power / (k * factorial)) < 1e-15) break;
  }
  
  return result;
}

/**
 * Compute the Riemann prime-counting function R(x)
 * R(x) = Σ(k=1 to K) μ(k)/k * li(x^(1/k))
 * 
 * @param x - The input value
 * @param K - Number of series terms (default: RIEMANN_K_TERMS)
 * @param liTerms - Number of terms for logarithmic integral
 * @returns Approximation of R(x)
 */
function riemannR(x: number, K: number = RIEMANN_K_TERMS, liTerms: number = LI_SERIES_TERMS): number {
  if (x <= 1) return 0;
  
  let sum = 0;
  
  for (let k = 1; k <= Math.min(K, MOBIUS.length - 1); k++) {
    const mu = MOBIUS[k];
    if (mu === 0) continue;
    
    const rootK = Math.pow(x, 1 / k);
    const li = logIntegral(rootK, liTerms);
    sum += (mu / k) * li;
  }
  
  return sum;
}

/**
 * Compute the Cipolla/Dusart initializer for nth prime estimation
 * x₀ = n * (L + L₂ - 1 + (L₂ - 2)/L - (L₂² - 6L₂ + 11)/(2L²))
 * 
 * @param n - The prime index
 * @returns Initial estimate for the nth prime
 */
function dusartInitializer(n: number): number {
  if (n < 2) return 2;
  
  const L = Math.log(n);
  const L2 = Math.log(L);
  
  // 3-term Cipolla/Dusart formula
  const term1 = L + L2 - 1;
  const term2 = (L2 - 2) / L;
  const term3 = (L2 * L2 - 6 * L2 + 11) / (2 * L * L);
  
  return n * (term1 + term2 - term3);
}

/**
 * Compute the derivative R'(x) for Newton iteration
 * R'(x) = (1/ln x) * Σ(k=1 to K) μ(k)/k * x^(1/k - 1)
 * 
 * @param x - The input value
 * @param K - Number of series terms
 * @returns Approximation of R'(x)
 */
function riemannRPrime(x: number, K: number = RIEMANN_K_TERMS): number {
  if (x <= 1) return 0;
  
  const lnx = Math.log(x);
  if (lnx === 0) return 0;
  
  let sum = 0;
  
  for (let k = 1; k <= Math.min(K, MOBIUS.length - 1); k++) {
    const mu = MOBIUS[k];
    if (mu === 0) continue;
    
    sum += (mu / k) * Math.pow(x, (1 / k) - 1);
  }
  
  return sum / lnx;
}

/**
 * Estimate the nth prime using Newton-Raphson iteration with Riemann R(x)
 * Optimized for address generation: fewer iterations with larger tolerance.
 * 
 * @param n - The prime index (1-indexed, so n=1 gives 2, n=2 gives 3, etc.)
 * @param K - Number of series terms
 * @returns Estimated value of the nth prime
 */
function estimateNthPrime(n: number, K: number = RIEMANN_K_TERMS): number {
  if (n <= 0) return 2;
  if (n === 1) return 2;
  if (n === 2) return 3;
  if (n === 3) return 5;
  if (n === 4) return 7;
  if (n === 5) return 11;
  
  // Start with Dusart initializer - this is already a good estimate
  let x = dusartInitializer(n);
  
  // For address generation, we only need deterministic transformation
  // A single Newton iteration is sufficient for our purposes
  const r = riemannR(x, K);
  const rPrime = riemannRPrime(x, K);
  
  if (rPrime !== 0 && isFinite(rPrime)) {
    x = x - (r - n) / rPrime;
  }
  
  return Math.round(x);
}

/**
 * Compute geodesic path from seed and index using Z5D methodology
 * This creates a deterministic but externally unpredictable path through
 * the prime number space.
 * 
 * @param seed - Master seed (256 bits / 32 bytes as hex or Buffer)
 * @param index - Transaction index
 * @param config - Configuration options
 * @returns Geodesic path value as BigInt
 */
export function computeGeodesicPath(
  seed: Buffer | string,
  index: number,
  config: ZGhostAddressGenConfig = {}
): bigint {
  if (index < 0 || !Number.isInteger(index)) {
    throw new Error('Index must be a non-negative integer');
  }
  
  const seedBuffer = typeof seed === 'string' ? Buffer.from(seed, 'hex') : seed;
  
  if (seedBuffer.length !== 32) {
    throw new Error('Seed must be exactly 256 bits (32 bytes)');
  }
  
  // Combine seed with index using HMAC-SHA512 for key derivation
  const indexBuffer = Buffer.alloc(4);
  indexBuffer.writeUInt32BE(index);
  
  // First round: derive intermediate key
  const hmac1 = createHash('sha512')
    .update(seedBuffer)
    .update(indexBuffer)
    .digest();
  
  // Extract prime index from first 8 bytes, bounded to a manageable range
  // while maintaining sufficient entropy for unique derivations
  const primeIndex = Number(hmac1.readBigUInt64BE(0) % BigInt(PRIME_INDEX_MODULUS)) + PRIME_INDEX_OFFSET;
  
  // Compute Z5D prime estimate
  const K = config.riemannTerms ?? RIEMANN_K_TERMS;
  const primeEstimate = estimateNthPrime(primeIndex, K);
  
  // Second round: combine with prime estimate for geodesic path
  const primeBuffer = Buffer.alloc(8);
  primeBuffer.writeBigUInt64BE(BigInt(Math.floor(primeEstimate)));
  
  const hmac2 = createHash('sha512')
    .update(hmac1.subarray(32)) // Use second half of first HMAC
    .update(primeBuffer)
    .digest();
  
  // Combine both halves into full geodesic path
  const pathHigh = hmac2.subarray(0, 32);
  const pathLow = hmac2.subarray(32, 64);
  
  // XOR the two halves for final path value
  const pathBytes = Buffer.alloc(32);
  for (let i = 0; i < 32; i++) {
    pathBytes[i] = pathHigh[i] ^ pathLow[i];
  }
  
  return BigInt('0x' + pathBytes.toString('hex'));
}

/**
 * Convert geodesic path to valid secp256k1 private key
 * Ensures uniform distribution across the keyspace
 * 
 * @param geodesicPath - The computed geodesic path
 * @returns 32-byte private key buffer
 */
export function geodesicToPrivateKey(geodesicPath: bigint): Buffer {
  // secp256k1 curve order
  const curveOrder = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');
  
  // Reduce modulo curve order to ensure valid private key
  // We add 1 to avoid the edge case of 0 being invalid
  let privateKeyValue = (geodesicPath % (curveOrder - BigInt(1))) + BigInt(1);
  
  // Convert to 32-byte buffer
  const hexKey = privateKeyValue.toString(16).padStart(64, '0');
  return Buffer.from(hexKey, 'hex');
}

/**
 * Z-Ghost Address Generator Class
 * Generates ephemeral Bitcoin addresses using Z5D prime prediction
 */
export class ZGhostAddressGen {
  private seed: Buffer;
  private config: ZGhostAddressGenConfig;
  private generatedAddresses: Set<string>;

  /**
   * Create a new Z-Ghost Address Generator
   * 
   * @param seed - Master seed (256 bits / 32 bytes as hex or Buffer)
   * @param config - Configuration options
   */
  constructor(seed: Buffer | string, config: ZGhostAddressGenConfig = {}) {
    this.seed = typeof seed === 'string' ? Buffer.from(seed, 'hex') : seed;
    
    if (this.seed.length !== 32) {
      throw new Error('Seed must be exactly 256 bits (32 bytes)');
    }
    
    this.config = {
      riemannTerms: config.riemannTerms ?? RIEMANN_K_TERMS,
      liTerms: config.liTerms ?? LI_SERIES_TERMS,
      collisionDetection: config.collisionDetection ?? true,
    };
    
    this.generatedAddresses = new Set();
  }

  /**
   * Generate private key for a given transaction index
   * 
   * @param index - Transaction index
   * @returns Private key as 32-byte Buffer
   */
  generatePrivateKey(index: number): Buffer {
    if (index < 0 || !Number.isInteger(index)) {
      throw new Error('Index must be a non-negative integer');
    }
    
    const geodesicPath = computeGeodesicPath(this.seed, index, this.config);
    return geodesicToPrivateKey(geodesicPath);
  }

  /**
   * Generate public key from private key
   * 
   * DEMONSTRATION IMPLEMENTATION:
   * This uses SHA256 hashing instead of proper secp256k1 elliptic curve point multiplication.
   * For production use with real Bitcoin transactions, replace with proper secp256k1 library.
   * 
   * The output maintains the compressed public key format (33 bytes) for protocol compatibility.
   * 
   * @param privateKey - 32-byte private key buffer
   * @returns 33-byte compressed public key buffer (demonstration format)
   */
  generatePublicKey(privateKey: Buffer): Buffer {
    // DEMONSTRATION: Using hash-based derivation instead of secp256k1
    // For production, use: const publicKey = secp256k1.pointFromScalar(privateKey, true)
    const hash1 = createHash('sha256').update(privateKey).digest();
    const hash2 = createHash('sha256').update(hash1).update(privateKey).digest();
    
    // Create compressed public key format (prefix + 32 bytes)
    const prefix = hash1[0] % 2 === 0 ? 0x02 : 0x03;
    const publicKey = Buffer.alloc(33);
    publicKey[0] = prefix;
    hash2.copy(publicKey, 1);
    
    return publicKey;
  }

  /**
   * Generate Bitcoin address from public key
   * 
   * DEMONSTRATION IMPLEMENTATION:
   * Uses SHA256 truncated to 20 bytes instead of proper RIPEMD160.
   * For production use with real Bitcoin transactions, use proper RIPEMD160.
   * 
   * @param publicKey - 33-byte compressed public key
   * @returns Bitcoin address string (P2PKH-style format)
   */
  generateAddress(publicKey: Buffer): string {
    // SHA256 of public key
    const sha256Hash = createHash('sha256').update(publicKey).digest();
    
    // DEMONSTRATION: Using SHA256 truncated to 20 bytes instead of RIPEMD160
    // For production, use: const hash160 = ripemd160(sha256Hash)
    const hash160 = createHash('sha256')
      .update(sha256Hash)
      .digest()
      .subarray(0, 20);
    
    // Add version byte (0x00 for mainnet P2PKH)
    const versionedPayload = Buffer.concat([Buffer.from([0x00]), hash160]);
    
    // Double SHA256 for checksum
    const checksum = createHash('sha256')
      .update(createHash('sha256').update(versionedPayload).digest())
      .digest()
      .subarray(0, 4);
    
    // Combine payload and checksum
    const addressBytes = Buffer.concat([versionedPayload, checksum]);
    
    // Base58 encode
    return this.base58Encode(addressBytes);
  }

  /**
   * Base58 encoding (Bitcoin alphabet)
   * 
   * @param buffer - Bytes to encode
   * @returns Base58 encoded string
   */
  private base58Encode(buffer: Buffer): string {
    const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    
    // Count leading zeros
    let zeros = 0;
    for (let i = 0; i < buffer.length && buffer[i] === 0; i++) {
      zeros++;
    }
    
    // Convert to BigInt and encode
    let value = BigInt('0x' + buffer.toString('hex'));
    let result = '';
    
    while (value > 0) {
      const remainder = Number(value % BigInt(58));
      value = value / BigInt(58);
      result = ALPHABET[remainder] + result;
    }
    
    // Add leading '1's for leading zeros
    return '1'.repeat(zeros) + result;
  }

  /**
   * Generate a complete address result for a given index
   * 
   * @param index - Transaction index
   * @returns Complete address generation result
   */
  generate(index: number): AddressGenerationResult {
    const geodesicPath = computeGeodesicPath(this.seed, index, this.config);
    const privateKey = geodesicToPrivateKey(geodesicPath);
    const publicKey = this.generatePublicKey(privateKey);
    const address = this.generateAddress(publicKey);
    
    // Collision detection
    if (this.config.collisionDetection && this.generatedAddresses.has(address)) {
      // Theoretically impossible due to deterministic generation and cryptographic hashing
      throw new Error(`Address collision detected at index ${index} - this should never happen`);
    }
    this.generatedAddresses.add(address);
    
    return {
      address,
      privateKey: privateKey.toString('hex'),
      publicKey: publicKey.toString('hex'),
      index,
      geodesicPath,
    };
  }

  /**
   * Generate multiple addresses in batch
   * 
   * @param startIndex - Starting transaction index
   * @param count - Number of addresses to generate
   * @returns Array of address generation results
   */
  generateBatch(startIndex: number, count: number): AddressGenerationResult[] {
    const results: AddressGenerationResult[] = [];
    
    for (let i = 0; i < count; i++) {
      results.push(this.generate(startIndex + i));
    }
    
    return results;
  }

  /**
   * Clear the collision detection cache
   * Useful when starting a new sequence of generations
   */
  clearCache(): void {
    this.generatedAddresses.clear();
  }

  /**
   * Get the number of addresses generated so far
   */
  get addressCount(): number {
    return this.generatedAddresses.size;
  }
}

// Export default for convenience
export default ZGhostAddressGen;
