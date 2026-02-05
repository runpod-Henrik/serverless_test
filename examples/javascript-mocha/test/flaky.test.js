/**
 * Example flaky tests for JavaScript/Mocha
 *
 * These tests demonstrate various flaky patterns that can occur in real applications.
 * They use the MOCHA_SEED environment variable for reproducible randomness.
 */

const { expect } = require('chai');

describe('Flaky Tests - JavaScript/Mocha', function() {

  describe('Random Failure', function() {
    it('should fail randomly ~30% of the time', function() {
      const value = Math.random();

      // Fails when value > 0.7
      expect(value).to.be.at.most(0.7);
    });
  });

  describe('Timing Dependent', function() {
    it('should fail when operation takes too long', function(done) {
      // Simulate variable processing time
      const delay = Math.floor(Math.random() * 5) + 1;

      setTimeout(() => {
        // Fails if processing takes "too long" (> 4ms)
        try {
          expect(delay).to.be.below(4);
          done();
        } catch (error) {
          done(error);
        }
      }, delay);
    });
  });

  describe('Order Dependency', function() {
    it('should fail based on execution order', function() {
      const items = [];

      // Simulate checking a cache that may or may not have items
      if (Math.random() > 0.5) {
        items.push('existing_item');
      }

      // Fails when cache is unexpectedly populated
      expect(items).to.have.lengthOf(0);
    });
  });

  describe('Boundary Condition', function() {
    it('should fail at edge cases', function() {
      // Simulate calculating a threshold
      const calculatedValue = Math.floor(Math.random() * 5) + 98; // Range: 98-102
      const threshold = 100;

      // Fails when value exceeds threshold
      expect(calculatedValue).to.be.at.most(threshold);
    });
  });

  describe('Concurrent Access', function() {
    it('should fail on simulated race condition', function() {
      // Simulate checking if resource is locked
      const isLocked = Math.random() > 0.5;

      // Fails when resource is locked
      expect(isLocked).to.be.false;
    });
  });

  describe('Network Simulation', function() {
    it('should fail on simulated network issue', function() {
      // Simulate network response success rate
      const successRate = Math.random();

      // Fails 20% of the time (simulating network issues)
      expect(successRate).to.be.above(0.2);
    });
  });

  describe('Promise Rejection', function() {
    it('should fail on random promise rejection', function() {
      const shouldReject = Math.random() > 0.5;

      const promise = new Promise((resolve, reject) => {
        if (shouldReject) {
          reject(new Error('Random rejection'));
        } else {
          resolve('success');
        }
      });

      // Flaky: depends on random rejection
      return promise;
    });
  });

  describe('Async/Await Pattern', function() {
    it('should fail on async timing issues', async function() {
      // Simulate async operation that may or may not complete in time
      const willTimeout = Math.random() > 0.7;

      const promise = new Promise((resolve) => {
        const delay = willTimeout ? 150 : 50;
        setTimeout(() => resolve('done'), delay);
      });

      const result = await promise;
      expect(result).to.equal('done');

      // Additional assertion that makes it flaky
      expect(willTimeout).to.be.false;
    });
  });

  describe('Callback Timing', function() {
    it('should fail on callback timing issues', function(done) {
      const shouldCall = Math.random() > 0.5;
      let callbackCalled = false;

      const callback = () => {
        callbackCalled = true;
      };

      // Randomly call callback
      if (shouldCall) {
        setTimeout(callback, 10);
      }

      // Check after delay
      setTimeout(() => {
        try {
          // Flaky: depends on random callback invocation
          expect(callbackCalled).to.be.true;
          done();
        } catch (error) {
          done(error);
        }
      }, 20);
    });
  });

  describe('Array Mutation', function() {
    it('should fail on random array mutation', function() {
      const items = [1, 2, 3, 4, 5];

      // Randomly remove items
      if (Math.random() > 0.5) {
        items.pop();
      }
      if (Math.random() > 0.5) {
        items.shift();
      }

      // Flaky: depends on random mutations
      expect(items).to.have.lengthOf(5);
    });
  });

  describe('Object Property', function() {
    it('should fail on random object property', function() {
      const obj = {};

      // Randomly add property
      if (Math.random() > 0.5) {
        obj.added = true;
      }

      // Flaky: depends on random property addition
      expect(obj).to.not.have.property('added');
    });
  });

  describe('Retry Logic', function() {
    it('should fail on retry logic', function() {
      const maxRetries = 3;
      let attempts = 0;

      // Simulate operation that may succeed after retries
      while (attempts < maxRetries) {
        attempts++;
        if (Math.random() > 0.6) {
          // Success
          break;
        }
      }

      // Flaky: depends on random success
      expect(attempts).to.be.below(maxRetries);
    });
  });
});
