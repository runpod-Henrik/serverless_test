import { defineConfig } from 'vitest/config';
import seedrandom from 'seedrandom';

// Get seed from environment variable
const seed = parseInt(process.env.VITE_TEST_SEED || '42', 10);

console.log(`Using seed: ${seed}`);

// Replace Math.random with seeded version
Math.random = seedrandom(seed.toString());

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./vitest.setup.ts'],
  },
});
