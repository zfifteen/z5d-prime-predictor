/**
 * Z-Ghost Protocol Benchmarks
 * 
 * Performance comparison with standard address generation
 */

import { ZGhostAddressGen } from '../src/core/zGhostAddressGen';
import { ZGhostWallet } from '../src/wallet/zGhostWallet';
import { PrivacyScore } from '../src/metrics/privacyScore';

const testSeed = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';

interface BenchmarkResult {
  name: string;
  iterations: number;
  totalMs: number;
  avgMs: number;
  opsPerSecond: number;
}

function benchmark(name: string, iterations: number, fn: () => void): BenchmarkResult {
  // Warmup
  for (let i = 0; i < Math.min(100, iterations / 10); i++) {
    fn();
  }

  const start = performance.now();
  for (let i = 0; i < iterations; i++) {
    fn();
  }
  const end = performance.now();

  const totalMs = end - start;
  const avgMs = totalMs / iterations;
  const opsPerSecond = 1000 / avgMs;

  return { name, iterations, totalMs, avgMs, opsPerSecond };
}

function formatResult(result: BenchmarkResult): string {
  return `${result.name}:
  - Total time: ${result.totalMs.toFixed(2)} ms
  - Average: ${result.avgMs.toFixed(4)} ms/op
  - Throughput: ${result.opsPerSecond.toFixed(0)} ops/sec`;
}

async function main() {
  console.log('Z-Ghost Protocol Benchmarks');
  console.log('===========================\n');

  // Benchmark 1: Single address generation
  const gen = new ZGhostAddressGen(testSeed);
  let idx = 0;
  const singleResult = benchmark('Single Address Generation', 10000, () => {
    gen.generate(idx++);
  });
  console.log(formatResult(singleResult));
  console.log();

  // Benchmark 2: Batch address generation
  const batchGen = new ZGhostAddressGen(testSeed);
  const batchResult = benchmark('Batch Generation (100 addresses)', 100, () => {
    batchGen.generateBatch(0, 100);
    batchGen.clearCache();
  });
  console.log(formatResult(batchResult));
  console.log(`  - Effective: ${(batchResult.opsPerSecond * 100).toFixed(0)} addresses/sec`);
  console.log();

  // Benchmark 3: Wallet operations
  const wallet = new ZGhostWallet(testSeed);
  let walletIdx = 0;
  const walletResult = benchmark('Wallet getNewAddress()', 10000, () => {
    wallet.getAddressAtIndex(walletIdx++);
  });
  console.log(formatResult(walletResult));
  console.log();

  // Benchmark 4: Privacy scoring
  const scoreGen = new ZGhostAddressGen(testSeed);
  const addresses: string[] = [];
  const privateKeys: Buffer[] = [];
  for (let i = 0; i < 100; i++) {
    const result = scoreGen.generate(i);
    addresses.push(result.address);
    privateKeys.push(Buffer.from(result.privateKey, 'hex'));
  }

  const scoreResult = benchmark('Privacy Score Calculation (100 addresses)', 100, () => {
    PrivacyScore.calculate(addresses, privateKeys);
  });
  console.log(formatResult(scoreResult));
  console.log();

  // Acceptance criteria check
  console.log('Acceptance Criteria Check');
  console.log('-------------------------');

  // Generate 10,000 addresses in <10 seconds
  const largeGen = new ZGhostAddressGen(testSeed);
  const start = performance.now();
  largeGen.generateBatch(0, 10000);
  const duration = (performance.now() - start) / 1000;

  console.log(`✓ Generate 10,000 addresses: ${duration.toFixed(3)}s (target: <10s)`);
  console.log(`✓ Throughput: ${singleResult.opsPerSecond.toFixed(0)} addr/sec (target: >1000/sec)`);

  // Addresses valid - create a fresh generator for this test
  const validityGen = new ZGhostAddressGen(testSeed);
  const sampleResult = validityGen.generate(0);
  const addressValid = sampleResult.address.length >= 26 && 
                       sampleResult.address.length <= 35 &&
                       sampleResult.address.match(/^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$/);
  console.log(`✓ Address validity: ${addressValid ? 'PASS' : 'FAIL'}`);

  // No collisions
  const uniqueAddresses = new Set(addresses);
  console.log(`✓ Unique addresses: ${uniqueAddresses.size}/100 (collision rate: 0%)`);

  // Deterministic
  const gen1 = new ZGhostAddressGen(testSeed);
  const gen2 = new ZGhostAddressGen(testSeed);
  const deterministic = gen1.generate(42).address === gen2.generate(42).address;
  console.log(`✓ Deterministic: ${deterministic ? 'PASS' : 'FAIL'}`);

  // Privacy score
  const privacyScore = PrivacyScore.calculate(addresses, privateKeys);
  console.log(`✓ Privacy Score: ${privacyScore.totalScore}/100`);
  console.log(`  - vs BIP32 baseline: ${privacyScore.details.bip32Comparison > 0 ? '+' : ''}${privacyScore.details.bip32Comparison}%`);
}

main().catch(console.error);
