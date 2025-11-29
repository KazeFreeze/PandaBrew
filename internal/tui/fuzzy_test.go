package tui

import (
	"reflect"
	"testing"
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
