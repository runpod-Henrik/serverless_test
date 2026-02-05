# TypeScript/Vitest Flaky Test Example

This example demonstrates flaky tests in TypeScript using Vitest.

## Files

- `flaky.test.ts` - Example flaky tests with various patterns
- `package.json` - Node.js dependencies
- `vitest.config.ts` - Vitest configuration with seed setup
- `vitest.setup.ts` - Additional test setup
- `tsconfig.json` - TypeScript configuration

## Flaky Test Patterns

1. **Random Failure** - Fails ~30% based on random value
2. **Timing Dependent** - Fails when async operation takes too long
3. **Order Dependency** - Fails based on execution order/state
4. **Boundary Condition** - Fails at edge cases
5. **Concurrent Access** - Simulates race conditions
6. **Network Simulation** - Simulates network flakiness
7. **Async Operation** - Demonstrates async timing issues
8. **Promise Race** - Demonstrates promise race conditions
9. **Set Operations** - Demonstrates random set operations
10. **Snapshot with Randomness** - Demonstrates snapshot flakiness

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
VITE_TEST_SEED=12345 npm test
```

### Run in watch mode (for development):
```bash
npm run test:watch
```

### Run multiple times to see flakiness:
```bash
for i in {1..10}; do
    echo "Run $i:"
    VITE_TEST_SEED=$RANDOM npm test
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
- Async Operation: Fails ~30% (3/10 runs)
- Promise Race: Fails ~50% (5/10 runs)
- Set Operations: Fails ~80% (8/10 runs)
- Snapshot with Randomness: Fails ~98% (10/10 runs)

## Using with Flaky Test Detector

### Input configuration:
```json
{
  "repo": "https://github.com/your-fork/testflake",
  "test_command": "cd examples/typescript-vitest && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-vitest"
}
```

The detector will automatically:
1. Detect Vitest framework from package.json
2. Run `npm install` to get dependencies
3. Run tests 100 times with different VITE_TEST_SEED values
4. Report flakiness rates for each test

## Sample Output

```
Random Failure: 31/100 failures (31% flaky) - MEDIUM severity
Timing Dependent: 22/100 failures (22% flaky) - MEDIUM severity
Order Dependency: 49/100 failures (49% flaky) - MEDIUM severity
Boundary Condition: 41/100 failures (41% flaky) - MEDIUM severity
Concurrent Access: 52/100 failures (52% flaky) - HIGH severity
Network Simulation: 18/100 failures (18% flaky) - MEDIUM severity
Async Operation: 28/100 failures (28% flaky) - MEDIUM severity
Promise Race: 48/100 failures (48% flaky) - MEDIUM severity
Set Operations: 82/100 failures (82% flaky) - HIGH severity
Snapshot with Randomness: 100/100 failures (100% flaky) - CRITICAL severity
```

## Seed Configuration

The `vitest.config.ts` file configures seeded randomness:

```typescript
import seedrandom from 'seedrandom';

const seed = parseInt(process.env.VITE_TEST_SEED || '42', 10);
Math.random = seedrandom(seed.toString());

export default defineConfig({
  test: {
    // ... config
  },
});
```

This replaces JavaScript's `Math.random()` with a seeded version before tests run.

## Vitest Specific Considerations

### Fast by Default
Vitest is much faster than Jest due to:
- Native ESM support
- Multi-threaded test execution
- Smart & instant watch mode

### Compatible with Jest
Vitest API is compatible with Jest, making migration easy:
```typescript
import { describe, test, expect } from 'vitest';
// Same API as Jest!
```

### Environment Configuration
Configure test environment in `vitest.config.ts`:
```typescript
export default defineConfig({
  test: {
    environment: 'node', // or 'jsdom', 'happy-dom'
  },
});
```

### Seed from Config
Vitest allows setting seed directly in config:
```typescript
export default defineConfig({
  test: {
    seed: parseInt(process.env.VITE_TEST_SEED || '42'),
  },
});
```

However, for our use case, we seed `Math.random()` instead to make it work across all random operations.

## Differences from Jest

1. **ESM First**: Vitest uses ESM by default
2. **Faster**: Better performance than Jest
3. **Vite Integration**: Works seamlessly with Vite projects
4. **Watch Mode**: Smarter watch mode with HMR-like features
5. **Configuration**: Uses `vitest.config.ts` instead of `jest.config.js`
