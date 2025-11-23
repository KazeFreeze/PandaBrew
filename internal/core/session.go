// Package core handles application state persistence.
package core

import (
	"encoding/json"
	"os"
	"path/filepath"
)

// SessionState represents the saved state of the application.
type SessionState struct {
	LastRootPath     string   `json:"last_root_path"`
	ManualSelections []string `json:"manual_selections"`
	IncludePatterns  []string `json:"include_patterns"`
}

// SaveSession writes the current config to a JSON file.
func SaveSession(config ExtractionConfig, filename string) error {
	state := SessionState{
		LastRootPath:     config.RootPath,
		ManualSelections: config.ManualSelections,
		IncludePatterns:  config.IncludePatterns,
	}
	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filename, data, 0o644)
}

// LoadSession reads the state and VERIFIES that paths still exist.
func LoadSession(filename string) (SessionState, []string, error) {
	var state SessionState
	var warnings []string

	data, err := os.ReadFile(filename)
	if err != nil {
		return state, nil, err
	}

	if err := json.Unmarshal(data, &state); err != nil {
		return state, nil, err
	}

	// Verify Root exists
	if _, err := os.Stat(state.LastRootPath); os.IsNotExist(err) {
		return state, []string{"Root path missing: " + state.LastRootPath}, nil
	}

	// Verify Selections exist
	var validSelections []string
	for _, path := range state.ManualSelections {
		if _, err := os.Stat(path); err == nil {
			validSelections = append(validSelections, path)
		} else {
			warnings = append(warnings, "Skipped missing selection: "+filepath.Base(path))
		}
	}
	state.ManualSelections = validSelections

	return state, warnings, nil
}
