/**
 * Tests for Z-Ghost Address Generator
 */

import {
  ZGhostAddressGen,
  computeGeodesicPath,
  geodesicToPrivateKey,
} from './zGhostAddressGen';

describe('ZGhostAddressGen', () => {
  const testSeed = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
  const testSeedBuffer = Buffer.from(testSeed, 'hex');

  describe('constructor', () => {
    it('should create instance with valid hex seed', () => {
      const gen = new ZGhostAddressGen(testSeed);
      expect(gen).toBeInstanceOf(ZGhostAddressGen);
    });

    it('should create instance with valid buffer seed', () => {
      const gen = new ZGhostAddressGen(testSeedBuffer);
      expect(gen).toBeInstanceOf(ZGhostAddressGen);
    });

    it('should throw error for invalid seed length', () => {
      expect(() => new ZGhostAddressGen('abcd')).toThrow('Seed must be exactly 256 bits');
      expect(() => new ZGhostAddressGen(Buffer.alloc(16))).toThrow('Seed must be exactly 256 bits');
    });
  });

  describe('generate', () => {
    it('should generate valid address for index 0', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const result = gen.generate(0);

      expect(result.address).toBeDefined();
      expect(result.address.length).toBeGreaterThan(25);
      expect(result.address.length).toBeLessThan(40);
      expect(result.privateKey).toHaveLength(64);
      expect(result.publicKey).toHaveLength(66);
      expect(result.index).toBe(0);
      expect(result.geodesicPath).toBeDefined();
    });

    it('should generate deterministic addresses', () => {
      const gen1 = new ZGhostAddressGen(testSeed);
      const gen2 = new ZGhostAddressGen(testSeed);

      const result1 = gen1.generate(5);
      const result2 = gen2.generate(5);

      expect(result1.address).toBe(result2.address);
      expect(result1.privateKey).toBe(result2.privateKey);
      expect(result1.geodesicPath).toBe(result2.geodesicPath);
    });

    it('should generate different addresses for different indices', () => {
      const gen = new ZGhostAddressGen(testSeed);
      
      const result1 = gen.generate(0);
      const result2 = gen.generate(1);
      const result3 = gen.generate(2);

      expect(result1.address).not.toBe(result2.address);
      expect(result2.address).not.toBe(result3.address);
      expect(result1.privateKey).not.toBe(result2.privateKey);
    });

    it('should generate different addresses for different seeds', () => {
      const seed1 = '0000000000000000000000000000000000000000000000000000000000000001';
      const seed2 = '0000000000000000000000000000000000000000000000000000000000000002';

      const gen1 = new ZGhostAddressGen(seed1);
      const gen2 = new ZGhostAddressGen(seed2);

      const result1 = gen1.generate(0);
      const result2 = gen2.generate(0);

      expect(result1.address).not.toBe(result2.address);
    });

    it('should throw error for negative index', () => {
      const gen = new ZGhostAddressGen(testSeed);
      expect(() => gen.generate(-1)).toThrow('Index must be a non-negative integer');
    });

    it('should throw error for non-integer index', () => {
      const gen = new ZGhostAddressGen(testSeed);
      expect(() => gen.generate(1.5)).toThrow('Index must be a non-negative integer');
    });
  });

  describe('generateBatch', () => {
    it('should generate multiple addresses', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 10);

      expect(results).toHaveLength(10);
      results.forEach((result, i) => {
        expect(result.index).toBe(i);
        expect(result.address).toBeDefined();
      });
    });

    it('should generate unique addresses in batch', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const results = gen.generateBatch(0, 100);

      const addresses = results.map(r => r.address);
      const uniqueAddresses = new Set(addresses);

      expect(uniqueAddresses.size).toBe(100);
    });
  });

  describe('performance', () => {
    it('should generate 1000+ addresses per second', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const count = 1000;

      const startTime = performance.now();
      for (let i = 0; i < count; i++) {
        gen.generate(i);
      }
      const endTime = performance.now();

      const duration = (endTime - startTime) / 1000; // seconds
      const rate = count / duration;

      console.log(`Generated ${count} addresses in ${duration.toFixed(3)}s (${rate.toFixed(0)} addr/sec)`);
      expect(rate).toBeGreaterThan(1000);
    });

    it('should generate 10000 addresses in less than 10 seconds', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const count = 10000;

      const startTime = performance.now();
      gen.generateBatch(0, count);
      const endTime = performance.now();

      const duration = (endTime - startTime) / 1000;
      console.log(`Generated ${count} addresses in ${duration.toFixed(3)}s`);
      expect(duration).toBeLessThan(10);
    });
  });

  describe('address format', () => {
    it('should generate addresses starting with 1 (P2PKH mainnet)', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const result = gen.generate(0);

      // Bitcoin P2PKH addresses start with '1'
      expect(result.address[0]).toBe('1');
    });

    it('should generate valid Base58 addresses', () => {
      const gen = new ZGhostAddressGen(testSeed);
      const result = gen.generate(0);

      // Base58 alphabet: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
      // No 0, O, I, l
      expect(result.address).not.toMatch(/[0OIl]/);
      expect(result.address).toMatch(/^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$/);
    });
  });

  describe('computeGeodesicPath', () => {
    it('should compute deterministic path from seed and index', () => {
      const path1 = computeGeodesicPath(testSeedBuffer, 0);
      const path2 = computeGeodesicPath(testSeedBuffer, 0);

      expect(path1).toBe(path2);
    });

    it('should produce different paths for different indices', () => {
      const path1 = computeGeodesicPath(testSeedBuffer, 0);
      const path2 = computeGeodesicPath(testSeedBuffer, 1);

      expect(path1).not.toBe(path2);
    });

    it('should throw error for invalid seed length', () => {
      expect(() => computeGeodesicPath(Buffer.alloc(16), 0)).toThrow('Seed must be exactly 256 bits');
    });
  });

  describe('geodesicToPrivateKey', () => {
    it('should produce valid 32-byte private key', () => {
      const path = computeGeodesicPath(testSeedBuffer, 0);
      const privateKey = geodesicToPrivateKey(path);

      expect(privateKey).toBeInstanceOf(Buffer);
      expect(privateKey.length).toBe(32);
    });

    it('should produce non-zero private key', () => {
      const path = computeGeodesicPath(testSeedBuffer, 0);
      const privateKey = geodesicToPrivateKey(path);

      const isAllZeros = privateKey.every(b => b === 0);
      expect(isAllZeros).toBe(false);
    });

    it('should produce private key within secp256k1 range', () => {
      const curveOrder = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');
      
      for (let i = 0; i < 100; i++) {
        const path = computeGeodesicPath(testSeedBuffer, i);
        const privateKey = geodesicToPrivateKey(path);
        const keyValue = BigInt('0x' + privateKey.toString('hex'));

        expect(keyValue).toBeGreaterThan(BigInt(0));
        expect(keyValue).toBeLessThan(curveOrder);
      }
    });
  });

  describe('collision detection', () => {
    it('should track generated addresses', () => {
      const gen = new ZGhostAddressGen(testSeed);
      
      gen.generate(0);
      gen.generate(1);
      gen.generate(2);

      expect(gen.addressCount).toBe(3);
    });

    it('should clear cache when requested', () => {
      const gen = new ZGhostAddressGen(testSeed);
      
      gen.generateBatch(0, 100);
      expect(gen.addressCount).toBe(100);

      gen.clearCache();
      expect(gen.addressCount).toBe(0);
    });
  });
});
