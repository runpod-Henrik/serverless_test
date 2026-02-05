package flaky

import (
	"math/rand"
	"os"
	"strconv"
	"testing"
	"time"
)

// Initialize random seed from GO_TEST_SEED environment variable
func init() {
	seed := int64(42) // default seed
	if seedStr := os.Getenv("GO_TEST_SEED"); seedStr != "" {
		if parsedSeed, err := strconv.ParseInt(seedStr, 10, 64); err == nil {
			seed = parsedSeed
		}
	}
	rand.Seed(seed)
}

// TestRandomFailure demonstrates a test that fails randomly (~30% of the time)
// This simulates race conditions or non-deterministic behavior
func TestRandomFailure(t *testing.T) {
	value := rand.Float64()

	// Fails when value > 0.7
	if value > 0.7 {
		t.Errorf("Random failure: got %.3f, expected <= 0.7", value)
	}
}

// TestTimingDependent demonstrates a test that depends on timing
// This simulates timeout issues or performance-dependent tests
func TestTimingDependent(t *testing.T) {
	// Simulate variable processing time
	delay := time.Duration(rand.Intn(5)+1) * time.Millisecond
	time.Sleep(delay)

	// Fails if processing takes "too long" (> 4ms)
	if delay > 4*time.Millisecond {
		t.Errorf("Operation too slow: %v", delay)
	}
}

// TestOrderDependency demonstrates a test that depends on execution order
// This simulates shared state issues
func TestOrderDependency(t *testing.T) {
	var items []string

	// Simulate checking a cache that may or may not have items
	if rand.Float64() > 0.5 {
		items = append(items, "existing_item")
	}

	// Fails when cache is unexpectedly populated
	if len(items) != 0 {
		t.Errorf("Expected empty cache, found %d items", len(items))
	}
}

// TestBoundaryCondition demonstrates a test at boundary conditions
// This simulates off-by-one errors
func TestBoundaryCondition(t *testing.T) {
	// Simulate calculating a threshold
	calculatedValue := rand.Intn(5) + 98 // Range: 98-102
	threshold := 100

	// Fails when value exceeds threshold
	if calculatedValue > threshold {
		t.Errorf("Value %d exceeds threshold %d", calculatedValue, threshold)
	}
}

// TestConcurrentAccess demonstrates concurrent access patterns
// This simulates race conditions with shared resources
func TestConcurrentAccess(t *testing.T) {
	// Simulate checking if resource is locked
	isLocked := rand.Float64() > 0.5

	// Fails when resource is locked
	if isLocked {
		t.Error("Resource is locked by another process")
	}
}

// TestNetworkSimulation demonstrates network flakiness
// This simulates unreliable network conditions
func TestNetworkSimulation(t *testing.T) {
	// Simulate network response success rate
	successRate := rand.Float64()

	// Fails 20% of the time (simulating network issues)
	if successRate <= 0.2 {
		t.Errorf("Network request failed: %.3f", successRate)
	}
}

// TestMapIteration demonstrates non-deterministic map iteration
// Go maps have random iteration order
func TestMapIteration(t *testing.T) {
	m := map[string]int{
		"a": 1,
		"b": 2,
		"c": 3,
	}

	// Get first key (non-deterministic in Go)
	var firstKey string
	for k := range m {
		firstKey = k
		break
	}

	// This test is intentionally flaky - map iteration order is random
	// But with seeded random, we can make it more predictable
	expectedKeys := []string{"a", "b", "c"}
	expected := expectedKeys[rand.Intn(len(expectedKeys))]

	if firstKey != expected {
		t.Errorf("Expected first key to be %s, got %s", expected, firstKey)
	}
}

// TestChannelRace demonstrates channel race conditions
// This simulates timing issues with goroutines
func TestChannelRace(t *testing.T) {
	ch := make(chan int, 1)

	// Randomly decide to send or not
	if rand.Float64() > 0.5 {
		ch <- 1
	}

	// Try to receive (may block or succeed)
	select {
	case val := <-ch:
		if val != 1 {
			t.Errorf("Unexpected value: %d", val)
		}
	case <-time.After(1 * time.Millisecond):
		t.Error("Channel receive timeout - no value sent")
	}
}
