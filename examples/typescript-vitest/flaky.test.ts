/**
 * Example flaky tests for TypeScript/Vitest
 *
 * These tests demonstrate various flaky patterns that can occur in real applications.
 * They use the VITE_TEST_SEED environment variable for reproducible randomness.
 */

import { describe, test, expect } from 'vitest';

describe('Flaky Tests - TypeScript/Vitest', () => {

  describe('Random Failure', () => {
    test('should fail randomly ~30% of the time', () => {
      const value = Math.random();

      // Fails when value > 0.7
      expect(value).toBeLessThanOrEqual(0.7);
    });
  });

  describe('Timing Dependent', () => {
    test('should fail when operation takes too long', async () => {
      // Simulate variable processing time
      const delay = Math.floor(Math.random() * 5) + 1;
      await new Promise(resolve => setTimeout(resolve, delay));

      // Fails if processing takes "too long" (> 4ms)
      expect(delay).toBeLessThan(4);
    });
  });

  describe('Order Dependency', () => {
    test('should fail based on execution order', () => {
      const items: string[] = [];

      // Simulate checking a cache that may or may not have items
      if (Math.random() > 0.5) {
        items.push('existing_item');
      }

      // Fails when cache is unexpectedly populated
      expect(items).toHaveLength(0);
    });
  });

  describe('Boundary Condition', () => {
    test('should fail at edge cases', () => {
      // Simulate calculating a threshold
      const calculatedValue = Math.floor(Math.random() * 5) + 98; // Range: 98-102
      const threshold = 100;

      // Fails when value exceeds threshold
      expect(calculatedValue).toBeLessThanOrEqual(threshold);
    });
  });

  describe('Concurrent Access', () => {
    test('should fail on simulated race condition', () => {
      // Simulate checking if resource is locked
      const isLocked = Math.random() > 0.5;

      // Fails when resource is locked
      expect(isLocked).toBe(false);
    });
  });

  describe('Network Simulation', () => {
    test('should fail on simulated network issue', () => {
      // Simulate network response success rate
      const successRate = Math.random();

      // Fails 20% of the time (simulating network issues)
      expect(successRate).toBeGreaterThan(0.2);
    });
  });

  describe('Async Operation', () => {
    test('should fail on async timing issues', async () => {
      // Simulate async operation that may or may not complete in time
      const willTimeout = Math.random() > 0.7;

      const promise = new Promise<string>((resolve) => {
        const delay = willTimeout ? 150 : 50;
        setTimeout(() => resolve('done'), delay);
      });

      const result = await promise;
      expect(result).toBe('done');

      // Additional assertion that makes it flaky
      expect(willTimeout).toBe(false);
    });
  });

  describe('Promise Race', () => {
    test('should fail on promise race condition', async () => {
      const delay1 = Math.random() * 100;
      const delay2 = Math.random() * 100;

      const promise1 = new Promise(resolve =>
        setTimeout(() => resolve('first'), delay1)
      );
      const promise2 = new Promise(resolve =>
        setTimeout(() => resolve('second'), delay2)
      );

      const winner = await Promise.race([promise1, promise2]);

      // Flaky: depends on which promise resolves first
      expect(winner).toBe('first');
    });
  });

  describe('Set Operations', () => {
    test('should fail on random set operations', () => {
      const items = new Set([1, 2, 3, 4, 5]);

      // Get random item from set
      const randomIndex = Math.floor(Math.random() * items.size);
      const randomItem = Array.from(items)[randomIndex];

      // Flaky: expects specific random item
      expect(randomItem).toBe(1);
    });
  });

  describe('Snapshot with Randomness', () => {
    test('should fail on snapshot with random data', () => {
      const data = {
        id: Math.floor(Math.random() * 1000),
        timestamp: Date.now(),
        value: Math.random()
      };

      // Flaky: snapshot will differ each run
      // This is intentionally simplified - normally you'd use toMatchSnapshot()
      expect(data.id).toBe(42);
    });
  });
});
