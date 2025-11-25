/**
 * Z-Ghost Protocol
 * 
 * Client-Side Ephemeral Address Generation using Z5D Prime Prediction
 * 
 * Z-Ghost replaces traditional BIP32/44 HD wallet derivation with geodesic
 * prime prediction paths that are deterministic for the user but computationally
 * infeasible to link externally.
 * 
 * Key Features:
 * - Pure client-side computation (zero network calls)
 * - High performance (1000+ addresses/second on mobile hardware)
 * - Deterministic derivation from seed
 * - No observable link between sequential addresses
 * - No xpub support (by design - prevents derivation analysis)
 * 
 * Mathematical Foundation:
 * Based on the Z5D Prime Predictor framework, which uses the Riemann
 * prime-counting function R(x) for geodesic path computation. This creates
 * a deterministic sequence through the prime number space that is
 * computationally infeasible to reverse-engineer without the master seed.
 * 
 * In memory of Bill and Keonne. Math is not a crime.
 * 
 * MIT Licensed - No patent claims
 * 
 * @packageDocumentation
 */

// Core address generation
export {
  ZGhostAddressGen,
  ZGhostAddressGenConfig,
  AddressGenerationResult,
  computeGeodesicPath,
  geodesicToPrivateKey,
} from './core/zGhostAddressGen';

// Privacy metrics
export {
  PrivacyScore,
  PrivacyScoreResult,
  PrivacyScoreDetails,
  calculateShannonEntropy,
  calculateHammingDistance,
  analyzeBitDistribution,
} from './metrics/privacyScore';

// Wallet interface
export {
  ZGhostWallet,
  ZGhostWalletConfig,
  AddressInfo,
  WalletState,
} from './wallet/zGhostWallet';

// Default export is the wallet for convenience
export { ZGhostWallet as default } from './wallet/zGhostWallet';
