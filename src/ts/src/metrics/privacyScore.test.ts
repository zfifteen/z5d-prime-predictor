/**
 * Tests for Privacy Score Calculator
 */

import {
  PrivacyScore,
  calculateShannonEntropy,
  calculateHammingDistance,
  analyzeBitDistribution,
} from './privacyScore';
import { ZGhostAddressGen } from '../core/zGhostAddressGen';

describe('PrivacyScore', () => {
  const testSeed = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';

  describe('calculateShannonEntropy', () => {
    it('should return 0 for empty array', () => {
      expect(calculateShannonEntropy([])).toBe(0);
    });

    it('should return 0 for single value', () => {
      expect(calculateShannonEntropy([42])).toBe(0);
    });

    it('should return 1 for perfectly balanced binary distribution', () => {
      const values = [0, 1, 0, 1, 0, 1, 0, 1];
      const entropy = calculateShannonEntropy(values);
      expect(entropy).toBeCloseTo(1, 5);
    });

    it('should return higher entropy for more uniform distributions', () => {
      const biased = [0, 0, 0, 0, 0, 0, 0, 1];
      const uniform = [0, 1, 2, 3, 4, 5, 6, 7];

      const biasedEntropy = calculateShannonEntropy(biased);
      const uniformEntropy = calculateShannonEntropy(uniform);

      expect(uniformEntropy).toBeGreaterThan(biasedEntropy);
    });
  });

  describe('calculateHammingDistance', () => {
    it('should return 0 for identical buffers', () => {
      const buf = Buffer.from([0xff, 0x00, 0xaa]);
      expect(calculateHammingDistance(buf, buf)).toBe(0);
    });

    it('should count differing bits correctly', () => {
      const buf1 = Buffer.from([0b00000000]);
      const buf2 = Buffer.from([0b00001111]);
      expect(calculateHammingDistance(buf1, buf2)).toBe(4);
    });

    it('should handle completely different bytes', () => {
      const buf1 = Buffer.from([0x00]);
      const buf2 = Buffer.from([0xff]);
      expect(calculateHammingDistance(buf1, buf2)).toBe(8);
    });

    it('should handle multiple bytes', () => {
      const buf1 = Buffer.from([0x00, 0x00]);
      const buf2 = Buffer.from([0xff, 0xff]);
      expect(calculateHammingDistance(buf1, buf2)).toBe(16);
    });
  });

  describe('analyzeBitDistribution', () => {
    it('should return empty results for empty input', () => {
      const result = analyzeBitDistribution([]);
      expect(result.bitCounts).toEqual([]);
      expect(result.stdDev).toBe(0);
      expect(result.chiSquared).toBe(0);
    });

    it('should count bit positions correctly', () => {
      const key = Buffer.alloc(32, 0xff); // All bits set
      const result = analyzeBitDistribution([key]);

      expect(result.bitCounts.length).toBe(256);
      result.bitCounts.forEach(count => {
        expect(count).toBe(1);
      });
    });

    it('should detect non-uniform distribution', () => {
      const keys = [
        Buffer.alloc(32, 0x00), // All zeros
        Buffer.alloc(32, 0x00), // All zeros
      ];
      const result = analyzeBitDistribution(keys);

      // With all zeros, each bit position has 0 ones
      // Expected is 50% (1 per position for 2 keys)
      // So chi-squared should be high
      expect(result.chiSquared).toBeGreaterThan(0);
    });
  });

  describe('calculate', () => {
    it('should throw error for empty addresses', () => {
      expect(() => PrivacyScore.calculate([], [])).toThrow('At least one address');
    });

    it('should throw error for mismatched lengths', () => {
      expect(() => PrivacyScore.calculate(['addr1', 'addr2'], [Buffer.alloc(32)])).toThrow('must match');
    });

    it('should calculate valid score for Z-Ghost addresses', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 100);

      const addresses = results.map(r => r.address);
      const privateKeys = results.map(r => Buffer.from(r.privateKey, 'hex'));

      const score = PrivacyScore.calculate(addresses, privateKeys);

      expect(score.totalScore).toBeGreaterThanOrEqual(0);
      expect(score.totalScore).toBeLessThanOrEqual(100);
      expect(score.entropyScore).toBeGreaterThanOrEqual(0);
      expect(score.entropyScore).toBeLessThanOrEqual(50);
      expect(score.distanceScore).toBeGreaterThanOrEqual(0);
      expect(score.distanceScore).toBeLessThanOrEqual(30);
      expect(score.distributionScore).toBeGreaterThanOrEqual(0);
      expect(score.distributionScore).toBeLessThanOrEqual(20);
    });

    it('should report zero collision rate for unique addresses', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 50);

      const addresses = results.map(r => r.address);
      const privateKeys = results.map(r => Buffer.from(r.privateKey, 'hex'));

      const score = PrivacyScore.calculate(addresses, privateKeys);

      expect(score.details.collisionRate).toBe(0);
      expect(score.details.uniqueAddresses).toBe(50);
    });

    it('should achieve reasonable privacy score', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 200);

      const addresses = results.map(r => r.address);
      const privateKeys = results.map(r => Buffer.from(r.privateKey, 'hex'));

      const score = PrivacyScore.calculate(addresses, privateKeys);

      // Z-Ghost should achieve at least a reasonable score
      // The exact score depends on the hash function's randomness properties
      expect(score.totalScore).toBeGreaterThanOrEqual(30);
      
      console.log('Privacy Score:', score.totalScore);
      console.log('- Entropy:', score.entropyScore);
      console.log('- Distance:', score.distanceScore);
      console.log('- Distribution:', score.distributionScore);
    });
  });

  describe('quickScore', () => {
    it('should return just the total score', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 20);

      const addresses = results.map(r => r.address);
      const privateKeys = results.map(r => Buffer.from(r.privateKey, 'hex'));

      const quickScore = PrivacyScore.quickScore(addresses, privateKeys);
      const fullScore = PrivacyScore.calculate(addresses, privateKeys);

      expect(quickScore).toBe(fullScore.totalScore);
    });
  });

  describe('bip32Baseline', () => {
    it('should return baseline values', () => {
      const baseline = PrivacyScore.bip32Baseline;

      expect(baseline.entropyScore).toBeDefined();
      expect(baseline.distanceScore).toBeDefined();
      expect(baseline.distributionScore).toBeDefined();
      expect(baseline.totalScore).toBeDefined();
    });
  });

  describe('generateReport', () => {
    it('should generate readable report', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 50);

      const addresses = results.map(r => r.address);
      const privateKeys = results.map(r => Buffer.from(r.privateKey, 'hex'));

      const score = PrivacyScore.calculate(addresses, privateKeys);
      const report = PrivacyScore.generateReport(score);

      expect(report).toContain('Z-Ghost Privacy Analysis Report');
      expect(report).toContain('Overall Score:');
      expect(report).toContain('Shannon Entropy');
      expect(report).toContain('Hamming Distance');
    });
  });
});
