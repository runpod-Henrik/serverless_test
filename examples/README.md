# Example Flaky Tests - All Languages

This directory contains complete example flaky test projects for all supported languages and frameworks.

## 📁 Directory Structure

```
examples/
├── python/              # Python/pytest examples
├── go/                  # Go test examples
├── typescript-jest/     # TypeScript/Jest examples
├── typescript-vitest/   # TypeScript/Vitest examples
├── javascript-mocha/    # JavaScript/Mocha examples
├── input_go.json        # Go input configuration
├── input_typescript_jest.json    # Jest input configuration
└── input_typescript_vitest.json  # Vitest input configuration
```

## 🚀 Quick Start

Each language directory contains:
- ✅ Complete working example with flaky tests
- ✅ All necessary configuration files
- ✅ Dependency files (requirements.txt, go.mod, package.json)
- ✅ Seed setup for reproducible randomness
- ✅ README with instructions

## 📋 Available Examples

### 1. Python/pytest (`python/`)

**Flaky test patterns:**
- Random failures (~30% flaky)
- Timing-dependent tests
- Order dependencies
- Boundary conditions
- Concurrent access simulation
- Network simulation

**Quick test:**
```bash
cd examples/python
pip install -r requirements.txt
TEST_SEED=12345 pytest test_flaky.py -v
```

**Input config:** Use `input.json` in root directory

---

### 2. Go (`go/`)

**Flaky test patterns:**
- Random failures
- Timing dependencies
- Order dependencies
- Boundary conditions
- Concurrent access (goroutines)
- Network simulation
- Map iteration (Go-specific)
- Channel race conditions

**Quick test:**
```bash
cd examples/go
GO_TEST_SEED=12345 go test -v
```

**Input config:** `examples/input_go.json`

```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "go test ./examples/go/... -v",
  "runs": 100,
  "parallelism": 10,
  "framework": "go"
}
```

---

### 3. TypeScript/Jest (`typescript-jest/`)

**Flaky test patterns:**
- Random failures
- Async timing issues
- Promise race conditions
- Order dependencies
- Mock timing issues
- Array randomization
- Network simulation

**Quick test:**
```bash
cd examples/typescript-jest
npm install
JEST_SEED=12345 npm test
```

**Input config:** `examples/input_typescript_jest.json`

```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "cd examples/typescript-jest && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-jest"
}
```

---

### 4. TypeScript/Vitest (`typescript-vitest/`)

**Flaky test patterns:**
- Random failures
- Async timing issues
- Promise race conditions
- Order dependencies
- Set operations
- Snapshot with randomness

**Quick test:**
```bash
cd examples/typescript-vitest
npm install
VITE_TEST_SEED=12345 npm test
```

**Input config:** `examples/input_typescript_vitest.json`

```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "cd examples/typescript-vitest && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-vitest"
}
```

---

### 5. JavaScript/Mocha (`javascript-mocha/`)

**Flaky test patterns:**
- Random failures
- Callback timing issues
- Promise rejections
- Async/await patterns
- Order dependencies
- Array mutations
- Retry logic

**Quick test:**
```bash
cd examples/javascript-mocha
npm install
MOCHA_SEED=12345 npm test
```

**Input config:**
```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "cd examples/javascript-mocha && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "javascript-mocha"
}
```

---

## 🎯 Testing Locally

### Run all examples:
```bash
# Python
cd python && pip install -r requirements.txt && pytest test_flaky.py -v && cd ..

# Go
cd go && go test -v && cd ..

# TypeScript/Jest
cd typescript-jest && npm install && npm test && cd ..

# TypeScript/Vitest
cd typescript-vitest && npm install && npm test && cd ..

# JavaScript/Mocha
cd javascript-mocha && npm install && npm test && cd ..
```

### Run with random seeds to see flakiness:
```bash
# Python
for i in {1..5}; do TEST_SEED=$RANDOM pytest python/test_flaky.py; done

# Go
for i in {1..5}; do GO_TEST_SEED=$RANDOM go test ./go/...; done

# TypeScript/Jest
cd typescript-jest && for i in {1..5}; do JEST_SEED=$RANDOM npm test; done

# TypeScript/Vitest
cd typescript-vitest && for i in {1..5}; do VITE_TEST_SEED=$RANDOM npm test; done

# JavaScript/Mocha
cd javascript-mocha && for i in {1..5}; do MOCHA_SEED=$RANDOM npm test; done
```

## 🔧 Using with Flaky Test Detector

### Step 1: Fork this repository

### Step 2: Deploy to RunPod
```bash
docker build -t your-username/flaky-test-detector:latest .
docker push your-username/flaky-test-detector:latest
```

### Step 3: Run detection on examples

```python
import runpod
import json

runpod.api_key = "your-api-key"

# Test Python example
with open('input.json') as f:
    config = json.load(f)
    config['test_command'] = 'pytest examples/python/test_flaky.py -v'

job = runpod.Endpoint("your-endpoint-id").run(config)
result = job.output()
print(result)
```

## 📊 Expected Results

When running each example 100 times, you should see results like:

**Python:**
```
test_random_failure: 30/100 failures (30% flaky) - MEDIUM
test_timing_dependent: 20/100 failures (20% flaky) - MEDIUM
test_order_dependency: 50/100 failures (50% flaky) - HIGH
```

**Go:**
```
TestRandomFailure: 28/100 failures (28% flaky) - MEDIUM
TestChannelRace: 52/100 failures (52% flaky) - HIGH
TestMapIteration: 65/100 failures (65% flaky) - HIGH
```

**TypeScript/Jest:**
```
Random Failure: 32/100 failures (32% flaky) - MEDIUM
Promise Race: 49/100 failures (49% flaky) - MEDIUM
Array Randomization: 83/100 failures (83% flaky) - HIGH
```

**TypeScript/Vitest:**
```
Random Failure: 31/100 failures (31% flaky) - MEDIUM
Set Operations: 82/100 failures (82% flaky) - HIGH
```

**JavaScript/Mocha:**
```
Random Failure: 32/100 failures (32% flaky) - MEDIUM
Callback Timing: 52/100 failures (52% flaky) - HIGH
Array Mutation: 73/100 failures (73% flaky) - HIGH
```

## 🌱 Seed Environment Variables

Each framework uses a different environment variable:

| Framework | Environment Variable | Example |
|-----------|---------------------|---------|
| Python/pytest | `TEST_SEED` | `TEST_SEED=12345 pytest` |
| Go | `GO_TEST_SEED` | `GO_TEST_SEED=12345 go test` |
| TypeScript/Jest | `JEST_SEED` | `JEST_SEED=12345 npm test` |
| TypeScript/Vitest | `VITE_TEST_SEED` | `VITE_TEST_SEED=12345 npm test` |
| JavaScript/Mocha | `MOCHA_SEED` | `MOCHA_SEED=12345 npm test` |

## 📚 Learn More

Each example directory contains:
- Detailed README with setup instructions
- Comments explaining each flaky pattern
- Expected failure rates
- Framework-specific considerations

## 🤝 Contributing

To add examples for new frameworks:
1. Create a new directory: `examples/new-framework/`
2. Add flaky test examples
3. Include all configuration files
4. Write a comprehensive README
5. Update this file
6. Submit a pull request

## 🐛 Common Issues

### Tests not flaky enough?
- Increase the number of runs: `"runs": 200`
- Check seed is being read correctly
- Verify Math.random() / rand is seeded

### All tests passing/failing?
- Check seed setup in configuration files
- Verify dependencies are installed
- Review test command path

### Framework not detected?
- Add explicit `"framework": "language-framework"` to input
- Check required files exist (go.mod, package.json, etc.)

## 📖 Documentation

- [MULTI_LANGUAGE.md](../MULTI_LANGUAGE.md) - Multi-language implementation guide
- [README.md](../README.md) - Main project documentation
- [TUTORIAL.md](../TUTORIAL.md) - Step-by-step tutorial
