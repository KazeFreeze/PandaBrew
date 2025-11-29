package tui

import (
	"reflect"
	"testing"

	"pandabrew/internal/core"
)

func TestSimpleFuzzyMatch(t *testing.T) {
	tests := []struct {
		name     string
		pattern  string
		str      string
		expected bool
	}{
		{"Exact match", "foo", "foo", true},
		{"Case insensitive", "FOO", "foo", true},
		{"Subsequence start", "f", "foo", true},
		{"Subsequence end", "o", "foo", true},
		{"Subsequence scattered", "fo", "foo", true},
		{"No match", "bar", "foo", false},
		{"Empty pattern", "", "foo", true},
		{"Empty string", "foo", "", false},
		{"Empty both", "", "", true},
		{"Path match", "tui/view", "internal/tui/view.go", true},
		{"Path match scattered", "tui/v", "internal/tui/view.go", true},
		{"Path mismatch", "tui/x", "internal/tui/view.go", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, indices := SimpleFuzzyMatch(tt.pattern, tt.str)
			if got != tt.expected {
				t.Errorf("SimpleFuzzyMatch(%q, %q) = %v, want %v", tt.pattern, tt.str, got, tt.expected)
			}

			// If we expected a match, ensure indices are valid and sorted
			if tt.expected && len(indices) != len(tt.pattern) {
				t.Errorf("Expected %d indices for pattern length %d, got %d", len(tt.pattern), len(tt.pattern), len(indices))
			}
			if tt.expected && len(indices) > 0 {
				if !sortCheck(indices) {
					t.Errorf("Indices are not sorted: %v", indices)
				}
			}
		})
	}
}

func TestToggleSelection(t *testing.T) {
	// Setup a dummy space without referencing undefined types
	space := &core.DirectorySpace{}
	// Initialize the map/slice directly on the struct field
	space.Config.ManualSelections = []string{}

	// 1. Test adding selection
	path1 := "/path/to/file1.go"
	toggleSelection(space, path1)
	if len(space.Config.ManualSelections) != 1 {
		t.Errorf("Expected 1 selection, got %d", len(space.Config.ManualSelections))
	}
	if space.Config.ManualSelections[0] != path1 {
		t.Errorf("Expected selection %s, got %s", path1, space.Config.ManualSelections[0])
	}

	// 2. Test removing selection (toggling off)
	toggleSelection(space, path1)
	if len(space.Config.ManualSelections) != 0 {
		t.Errorf("Expected 0 selections after toggle off, got %d", len(space.Config.ManualSelections))
	}

	// 3. Test adding multiple unique
	path2 := "/path/to/file2.go"
	toggleSelection(space, path1)
	toggleSelection(space, path2)
	if len(space.Config.ManualSelections) != 2 {
		t.Errorf("Expected 2 selections, got %d", len(space.Config.ManualSelections))
	}
}

func TestBatchSelectionLogic(t *testing.T) {
	// Setup dummy space
	space := &core.DirectorySpace{}
	space.Config.ManualSelections = []string{"/file/c", "/file/d"}

	// Simulate the GlobalSearchSelected map from the model
	batchSelections := map[string]bool{
		"/file/a": true,
		"/file/b": true,
		"/file/c": true,
	}

	// Run batch logic as implemented in Update
	for path := range batchSelections {
		toggleSelection(space, path)
	}

	// Verify Results
	// Expected: /file/d (touched), /file/a (added), /file/b (added), /file/c (removed)
	expectedMap := map[string]bool{
		"/file/d": true,
		"/file/a": true,
		"/file/b": true,
	}

	if len(space.Config.ManualSelections) != 3 {
		t.Errorf("Expected 3 final selections, got %d: %v", len(space.Config.ManualSelections), space.Config.ManualSelections)
	}

	for _, s := range space.Config.ManualSelections {
		if !expectedMap[s] {
			t.Errorf("Unexpected selection found: %s", s)
		}
	}
}

func sortCheck(s []int) bool {
	return reflect.DeepEqual(s, sortIntsCopy(s))
}

func sortIntsCopy(s []int) []int {
	c := make([]int, len(s))
	copy(c, s)
	// Simple bubble sort for test utility
	for i := 0; i < len(c)-1; i++ {
		for j := 0; j < len(c)-i-1; j++ {
			if c[j] > c[j+1] {
				c[j], c[j+1] = c[j+1], c[j]
			}
		}
	}
	return c
}
