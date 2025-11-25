/**
 * Tests for Z-Ghost Wallet
 */

import { ZGhostWallet } from './zGhostWallet';
import { randomBytes } from 'crypto';

describe('ZGhostWallet', () => {
  const testSeed = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef';
  const testSeedBuffer = Buffer.from(testSeed, 'hex');

  describe('constructor', () => {
    it('should create wallet with valid hex seed', () => {
      const wallet = new ZGhostWallet(testSeed);
      expect(wallet).toBeInstanceOf(ZGhostWallet);
    });

    it('should create wallet with valid buffer seed', () => {
      const wallet = new ZGhostWallet(testSeedBuffer);
      expect(wallet).toBeInstanceOf(ZGhostWallet);
    });

    it('should throw error for invalid seed length', () => {
      expect(() => new ZGhostWallet('abcd')).toThrow('Seed must be exactly 256 bits');
    });
  });

  describe('static create', () => {
    it('should create wallet with random seed', () => {
      const { wallet, seed } = ZGhostWallet.create();
      
      expect(wallet).toBeInstanceOf(ZGhostWallet);
      expect(seed).toBeInstanceOf(Buffer);
      expect(seed.length).toBe(32);
    });

    it('should create unique wallets each time', () => {
      const { wallet: wallet1, seed: seed1 } = ZGhostWallet.create();
      const { wallet: wallet2, seed: seed2 } = ZGhostWallet.create();

      expect(seed1.toString('hex')).not.toBe(seed2.toString('hex'));
      
      const addr1 = wallet1.getNewAddress();
      const addr2 = wallet2.getNewAddress();
      
      expect(addr1.address).not.toBe(addr2.address);
    });
  });

  describe('static fromMnemonic', () => {
    it('should create wallet from mnemonic', () => {
      const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';
      const wallet = ZGhostWallet.fromMnemonic(mnemonic);
      
      expect(wallet).toBeInstanceOf(ZGhostWallet);
    });

    it('should create deterministic wallet from same mnemonic', () => {
      const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';
      
      const wallet1 = ZGhostWallet.fromMnemonic(mnemonic);
      const wallet2 = ZGhostWallet.fromMnemonic(mnemonic);

      const addr1 = wallet1.getNewAddress();
      const addr2 = wallet2.getNewAddress();

      expect(addr1.address).toBe(addr2.address);
    });

    it('should create different wallet with passphrase', () => {
      const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';
      
      const wallet1 = ZGhostWallet.fromMnemonic(mnemonic);
      const wallet2 = ZGhostWallet.fromMnemonic(mnemonic, 'secret');

      const addr1 = wallet1.getNewAddress();
      const addr2 = wallet2.getNewAddress();

      expect(addr1.address).not.toBe(addr2.address);
    });
  });

  describe('getNewAddress', () => {
    it('should return new address info', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addr = wallet.getNewAddress();

      expect(addr.address).toBeDefined();
      expect(addr.index).toBe(0);
      expect(addr.isNew).toBe(true);
    });

    it('should increment index for each call', () => {
      const wallet = new ZGhostWallet(testSeed);

      const addr1 = wallet.getNewAddress();
      const addr2 = wallet.getNewAddress();
      const addr3 = wallet.getNewAddress();

      expect(addr1.index).toBe(0);
      expect(addr2.index).toBe(1);
      expect(addr3.index).toBe(2);
    });

    it('should generate unique addresses', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addresses: string[] = [];

      for (let i = 0; i < 100; i++) {
        addresses.push(wallet.getNewAddress().address);
      }

      const unique = new Set(addresses);
      expect(unique.size).toBe(100);
    });
  });

  describe('getNewAddresses', () => {
    it('should return multiple addresses', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addresses = wallet.getNewAddresses(5);

      expect(addresses).toHaveLength(5);
      addresses.forEach((addr, i) => {
        expect(addr.index).toBe(i);
        expect(addr.isNew).toBe(true);
      });
    });

    it('should throw error for invalid count', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      expect(() => wallet.getNewAddresses(0)).toThrow('must be a positive integer');
      expect(() => wallet.getNewAddresses(-1)).toThrow('must be a positive integer');
      expect(() => wallet.getNewAddresses(1.5)).toThrow('must be a positive integer');
    });
  });

  describe('getAddressAtIndex', () => {
    it('should return address for specific index', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addr = wallet.getAddressAtIndex(5);

      expect(addr.index).toBe(5);
    });

    it('should return cached address if already generated', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      wallet.getNewAddresses(10); // Generate 0-9
      
      const addr = wallet.getAddressAtIndex(5);
      expect(addr.isNew).toBe(false);
    });

    it('should return same address for same index', () => {
      const wallet = new ZGhostWallet(testSeed);

      const addr1 = wallet.getAddressAtIndex(100);
      const addr2 = wallet.getAddressAtIndex(100);

      expect(addr1.address).toBe(addr2.address);
    });

    it('should throw error for invalid index', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      expect(() => wallet.getAddressAtIndex(-1)).toThrow('non-negative integer');
      expect(() => wallet.getAddressAtIndex(1.5)).toThrow('non-negative integer');
    });
  });

  describe('getPrivateKey', () => {
    it('should return private key for cached address', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addr = wallet.getNewAddress();

      const privateKey = wallet.getPrivateKey(addr.address);
      
      expect(privateKey).toBeDefined();
      expect(privateKey).toHaveLength(64);
    });

    it('should return null for unknown address', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      const privateKey = wallet.getPrivateKey('1UnknownAddress123');
      expect(privateKey).toBeNull();
    });
  });

  describe('getPrivateKeyAtIndex', () => {
    it('should return private key for any index', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      const privateKey = wallet.getPrivateKeyAtIndex(1000);
      
      expect(privateKey).toBeDefined();
      expect(privateKey).toHaveLength(64);
    });

    it('should return deterministic private key', () => {
      const wallet1 = new ZGhostWallet(testSeed);
      const wallet2 = new ZGhostWallet(testSeed);

      const key1 = wallet1.getPrivateKeyAtIndex(42);
      const key2 = wallet2.getPrivateKeyAtIndex(42);

      expect(key1).toBe(key2);
    });
  });

  describe('exportXPub', () => {
    it('should throw error - not supported', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      expect(() => wallet.exportXPub()).toThrow('does not support extended public keys');
    });
  });

  describe('exportXPrv', () => {
    it('should throw error - not supported', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      expect(() => wallet.exportXPrv()).toThrow('does not support extended private keys');
    });
  });

  describe('isOwnAddress', () => {
    it('should return true for generated address', () => {
      const wallet = new ZGhostWallet(testSeed);
      const addr = wallet.getNewAddress();

      expect(wallet.isOwnAddress(addr.address)).toBe(true);
    });

    it('should return false for unknown address', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      expect(wallet.isOwnAddress('1UnknownAddress123')).toBe(false);
    });
  });

  describe('findAddressIndex', () => {
    it('should return index for generated address', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(10);
      
      const addr = wallet.getAddressAtIndex(5);
      const index = wallet.findAddressIndex(addr.address);

      expect(index).toBe(5);
    });

    it('should return null for unknown address', () => {
      const wallet = new ZGhostWallet(testSeed);
      
      const index = wallet.findAddressIndex('1UnknownAddress123');
      expect(index).toBeNull();
    });
  });

  describe('getState', () => {
    it('should return wallet state', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(5);

      const state = wallet.getState();

      expect(state.currentIndex).toBe(5);
      expect(state.addressesGenerated).toBe(5);
      expect(state.cachedAddresses).toBe(5);
    });
  });

  describe('getFingerprint', () => {
    it('should return 8-character hex fingerprint', () => {
      const wallet = new ZGhostWallet(testSeed);
      const fingerprint = wallet.getFingerprint();

      expect(fingerprint).toHaveLength(8);
      expect(fingerprint).toMatch(/^[0-9a-f]+$/);
    });

    it('should return same fingerprint for same seed', () => {
      const wallet1 = new ZGhostWallet(testSeed);
      const wallet2 = new ZGhostWallet(testSeed);

      expect(wallet1.getFingerprint()).toBe(wallet2.getFingerprint());
    });

    it('should return different fingerprint for different seed', () => {
      const wallet1 = new ZGhostWallet(testSeed);
      const wallet2 = new ZGhostWallet(randomBytes(32));

      expect(wallet1.getFingerprint()).not.toBe(wallet2.getFingerprint());
    });
  });

  describe('resetIndex', () => {
    it('should reset index to 0 by default', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(10);
      
      wallet.resetIndex();
      
      expect(wallet.getState().currentIndex).toBe(0);
    });

    it('should reset index to specified value', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(10);
      
      wallet.resetIndex(5);
      
      expect(wallet.getState().currentIndex).toBe(5);
    });
  });

  describe('clearCache', () => {
    it('should clear all cached addresses', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(100);

      wallet.clearCache();

      expect(wallet.getState().cachedAddresses).toBe(0);
    });
  });

  describe('calculatePrivacyScore', () => {
    it('should throw error with less than 2 addresses', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddress();

      expect(() => wallet.calculatePrivacyScore()).toThrow('At least 2 addresses');
    });

    it('should calculate privacy score for generated addresses', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(50);

      const score = wallet.calculatePrivacyScore();

      expect(score.totalScore).toBeGreaterThanOrEqual(0);
      expect(score.totalScore).toBeLessThanOrEqual(100);
    });
  });

  describe('generatePrivacyReport', () => {
    it('should generate readable report', () => {
      const wallet = new ZGhostWallet(testSeed);
      wallet.getNewAddresses(50);

      const report = wallet.generatePrivacyReport();

      expect(report).toContain('Z-Ghost Privacy Analysis Report');
      expect(report).toContain('Overall Score');
    });
  });
});
