/**
 * Example flaky tests for TypeScript/Jest
 *
 * These tests demonstrate various flaky patterns that can occur in real applications.
 * They use the JEST_SEED environment variable for reproducible randomness.
 */

describe('Flaky Tests - TypeScript/Jest', () => {

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

      const promise = new Promise<string>((resolve, reject) => {
        const delay = willTimeout ? 150 : 50;
        setTimeout(() => resolve('done'), delay);
      });

      // Fails when operation times out
      await expect(promise).resolves.toBe('done');

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

  describe('Array Randomization', () => {
    test('should fail on random array operations', () => {
      const items = [1, 2, 3, 4, 5];

      // Shuffle array randomly
      for (let i = items.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [items[i], items[j]] = [items[j], items[i]];
      }

      // Flaky: expects specific order after random shuffle
      expect(items[0]).toBe(1);
    });
  });

  describe('Mock Timing', () => {
    test('should fail on mock timing issues', () => {
      const callback = jest.fn();

      // Randomly call callback
      if (Math.random() > 0.5) {
        callback();
      }

      // Fails when callback not called
      expect(callback).toHaveBeenCalled();
    });
  });
});
