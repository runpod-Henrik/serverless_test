/**
 * Jest setup file - runs before all tests
 *
 * This sets up seeded random number generation using the JEST_SEED
 * environment variable, making random tests reproducible.
 */

const seedrandom = require('seedrandom');

// Get seed from environment variable or use default
const seed = parseInt(process.env.JEST_SEED || '42', 10);

console.log(`Using seed: ${seed}`);

// Replace Math.random with seeded version
Math.random = seedrandom(seed.toString());
