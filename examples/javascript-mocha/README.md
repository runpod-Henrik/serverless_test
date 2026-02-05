# JavaScript/Mocha Flaky Test Example

This example demonstrates flaky tests in JavaScript using Mocha and Chai.

## Files

- `test/flaky.test.js` - Example flaky tests with various patterns
- `test/setup.js` - Seed setup for reproducible randomness
- `package.json` - Node.js dependencies
- `.mocharc.json` - Mocha configuration

## Flaky Test Patterns

1. **Random Failure** - Fails ~30% based on random value
2. **Timing Dependent** - Fails when operation takes too long
3. **Order Dependency** - Fails based on execution order/state
4. **Boundary Condition** - Fails at edge cases
5. **Concurrent Access** - Simulates race conditions
6. **Network Simulation** - Simulates network flakiness
7. **Promise Rejection** - Demonstrates random promise rejections
8. **Async/Await Pattern** - Demonstrates async timing issues
9. **Callback Timing** - Demonstrates callback timing issues
10. **Array Mutation** - Demonstrates random array mutations
11. **Object Property** - Demonstrates random object properties
12. **Retry Logic** - Demonstrates retry logic flakiness

## Local Testing

### Install dependencies:
```bash
npm install
```

### Run tests normally:
```bash
npm test
```

### Run with specific seed:
```bash
MOCHA_SEED=12345 npm test
```

### Run in watch mode (for development):
```bash
npm run test:watch
```

### Run multiple times to see flakiness:
```bash
for i in {1..10}; do
    echo "Run $i:"
    MOCHA_SEED=$RANDOM npm test
done
```

## Expected Results

When running 10 times, you should see some tests fail intermittently:
- Random Failure: Fails ~30% (3/10 runs)
- Timing Dependent: Fails ~20% (2/10 runs)
- Order Dependency: Fails ~50% (5/10 runs)
- Boundary Condition: Fails ~40% (4/10 runs)
- Concurrent Access: Fails ~50% (5/10 runs)
- Network Simulation: Fails ~20% (2/10 runs)
- Promise Rejection: Fails ~50% (5/10 runs)
- Async/Await Pattern: Fails ~30% (3/10 runs)
- Callback Timing: Fails ~50% (5/10 runs)
- Array Mutation: Fails ~75% (7-8/10 runs)
- Object Property: Fails ~50% (5/10 runs)
- Retry Logic: Fails ~40% (4/10 runs)

## Using with Flaky Test Detector

### Input configuration:
```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "cd examples/javascript-mocha && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "javascript-mocha"
}
```

The detector will automatically:
1. Detect Mocha framework from package.json
2. Run `npm install` to get dependencies
3. Run tests 100 times with different MOCHA_SEED values
4. Report flakiness rates for each test

## Sample Output

```
Random Failure: 32/100 failures (32% flaky) - MEDIUM severity
Timing Dependent: 21/100 failures (21% flaky) - MEDIUM severity
Order Dependency: 49/100 failures (49% flaky) - MEDIUM severity
Boundary Condition: 42/100 failures (42% flaky) - MEDIUM severity
Concurrent Access: 51/100 failures (51% flaky) - HIGH severity
Network Simulation: 19/100 failures (19% flaky) - MEDIUM severity
Promise Rejection: 48/100 failures (48% flaky) - MEDIUM severity
Async/Await Pattern: 31/100 failures (31% flaky) - MEDIUM severity
Callback Timing: 52/100 failures (52% flaky) - HIGH severity
Array Mutation: 73/100 failures (73% flaky) - HIGH severity
Object Property: 50/100 failures (50% flaky) - HIGH severity
Retry Logic: 41/100 failures (41% flaky) - MEDIUM severity
```

## Seed Configuration

The `test/setup.js` file configures seeded randomness:

```javascript
const seedrandom = require('seedrandom');
const seed = parseInt(process.env.MOCHA_SEED || '42', 10);
Math.random = seedrandom(seed.toString());
```

This replaces JavaScript's `Math.random()` with a seeded version before tests run.

## Mocha Specific Considerations

### Test Structure
Mocha uses `describe()` and `it()`:
```javascript
describe('Feature', function() {
  it('should work', function() {
    // test code
  });
});
```

### Async Testing
Three ways to handle async tests:

**1. Callbacks (done parameter):**
```javascript
it('async test', function(done) {
  setTimeout(() => {
    expect(value).to.equal('expected');
    done();
  }, 100);
});
```

**2. Promises (return promise):**
```javascript
it('async test', function() {
  return asyncOperation().then(result => {
    expect(result).to.equal('expected');
  });
});
```

**3. Async/Await:**
```javascript
it('async test', async function() {
  const result = await asyncOperation();
  expect(result).to.equal('expected');
});
```

### Timeout Configuration
Set timeout in `.mocharc.json`:
```json
{
  "timeout": 5000
}
```

Or per-test:
```javascript
it('slow test', function() {
  this.timeout(10000);
  // test code
});
```

### Chai Assertions
Using Chai's expect syntax:
```javascript
const { expect } = require('chai');

expect(value).to.equal('expected');
expect(array).to.have.lengthOf(5);
expect(obj).to.have.property('key');
expect(value).to.be.true;
expect(number).to.be.above(10);
```

### Hooks
Mocha provides hooks for setup/teardown:
```javascript
describe('Feature', function() {
  before(function() {
    // runs once before all tests
  });

  beforeEach(function() {
    // runs before each test
  });

  afterEach(function() {
    // runs after each test
  });

  after(function() {
    // runs once after all tests
  });
});
```

## Differences from Jest/Vitest

1. **Assertion Library**: Mocha doesn't include assertions (uses Chai)
2. **Configuration**: Uses `.mocharc.json` instead of `jest.config.js`
3. **Test Syntax**: Uses `it()` instead of `test()`
4. **No Built-in Mocking**: Need separate library (sinon) for mocks
5. **More Flexible**: Can mix different assertion and mocking libraries
