# Z-Ghost Protocol

Client-Side Ephemeral Address Generation using Z5D Prime Prediction

## Overview

Z-Ghost replaces traditional BIP32/44 HD wallet derivation with geodesic prime prediction paths that are deterministic for the user but computationally infeasible to link externally. This provides enhanced privacy for Bitcoin transactions.

## Mathematical Foundation

The Z-Ghost Protocol uses the Z5D Prime Predictor framework, which is based on the Riemann prime-counting function R(x):

```
R(x) = Σ(k=1 to K) μ(k)/k * li(x^(1/k))
```

Where:
- μ(k) is the Möbius function
- li(x) is the logarithmic integral

This creates deterministic but externally unpredictable geodesic paths through the prime number space, which are then used to derive Bitcoin addresses.

## Key Features

- **Pure client-side computation** - Zero network calls required
- **High performance** - 38,000+ addresses per second
- **Deterministic** - Same seed always produces same addresses
- **No xpub support** - By design, preventing derivation analysis
- **No statistical correlation** - Between sequential addresses

## Installation

```bash
cd src/ts
npm install
npm run build
```

## Usage

### Basic Address Generation

```typescript
import { ZGhostAddressGen } from './src/core/zGhostAddressGen';

// Create generator with 32-byte seed (hex string or Buffer)
const seed = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
const gen = new ZGhostAddressGen(seed);

// Generate address at index 0
const result = gen.generate(0);
console.log(result.address);      // Bitcoin address (P2PKH format)
console.log(result.privateKey);   // 64-char hex private key
console.log(result.publicKey);    // 66-char hex compressed public key

// Generate batch of addresses
const batch = gen.generateBatch(0, 100);
```

### Wallet Interface

```typescript
import { ZGhostWallet } from './src/wallet/zGhostWallet';

// Create wallet from seed
const wallet = new ZGhostWallet(seed);

// Or create with random seed
const { wallet: newWallet, seed: newSeed } = ZGhostWallet.create();

// Or from mnemonic
const mnemonicWallet = ZGhostWallet.fromMnemonic('abandon abandon ...');

// Get new addresses
const addr1 = wallet.getNewAddress();
const addr2 = wallet.getNewAddress();

// Get private key for an address
const privateKey = wallet.getPrivateKey(addr1.address);

// Note: exportXPub() will throw - this is by design
try {
  wallet.exportXPub(); // Throws error
} catch (e) {
  console.log('Z-Ghost does not support xpub');
}
```

### Privacy Scoring

```typescript
import { PrivacyScore } from './src/metrics/privacyScore';

const addresses = [...]; // Array of address strings
const privateKeys = [...]; // Array of 32-byte Buffers

const score = PrivacyScore.calculate(addresses, privateKeys);
console.log(score.totalScore);        // 0-100
console.log(score.entropyScore);      // Shannon entropy component
console.log(score.distanceScore);     // Hamming distance component
console.log(score.distributionScore); // Bit distribution component

// Generate human-readable report
const report = PrivacyScore.generateReport(score);
console.log(report);
```

## Running Tests

```bash
npm test
```

## Running Benchmarks

```bash
npm run bench
```

## Performance

The Z-Ghost Protocol significantly exceeds the performance requirements:

| Metric | Target | Actual |
|--------|--------|--------|
| Addresses/second | > 1,000 | ~38,000 |
| 10,000 addresses | < 10s | ~0.23s |

## API Reference

### ZGhostAddressGen

- `constructor(seed: Buffer | string, config?: ZGhostAddressGenConfig)`
- `generate(index: number): AddressGenerationResult`
- `generateBatch(startIndex: number, count: number): AddressGenerationResult[]`
- `generatePrivateKey(index: number): Buffer`
- `clearCache(): void`

### ZGhostWallet

- `constructor(seed: Buffer | string, config?: ZGhostWalletConfig)`
- `static create(config?): { wallet: ZGhostWallet; seed: Buffer }`
- `static fromMnemonic(mnemonic: string, passphrase?: string, config?): ZGhostWallet`
- `getNewAddress(): AddressInfo`
- `getNewAddresses(count: number): AddressInfo[]`
- `getAddressAtIndex(index: number): AddressInfo`
- `getPrivateKey(address: string): string | null`
- `getPrivateKeyAtIndex(index: number): string`
- `exportXPub(): never` (throws by design)
- `exportXPrv(): never` (throws by design)
- `isOwnAddress(address: string): boolean`
- `calculatePrivacyScore(): PrivacyScoreResult`
- `generatePrivacyReport(): string`

### PrivacyScore

- `static calculate(addresses: string[], privateKeys: Buffer[]): PrivacyScoreResult`
- `static quickScore(addresses: string[], privateKeys: Buffer[]): number`
- `static generateReport(result: PrivacyScoreResult): string`
- `static get bip32Baseline(): { entropyScore, distanceScore, distributionScore, totalScore }`

## License

MIT Licensed - No patent claims

## References

- Z5D Prime Predictor: [../README.md](../README.md)
- Riemann Prime-Counting Function: [SPEC.md](../c/z5d-predictor-c/SPEC.md)
- Dusart, P. (1999). "The kth prime is greater than k(ln k + ln ln k − 1)"

---

*In memory of Bill and Keonne. Math is not a crime.*
