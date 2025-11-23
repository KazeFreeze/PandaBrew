// Package core implements the headless logic for file traversal,
// filtering, and report generation.
package core

import (
	"time"
)

// Session represents the global application state.
type Session struct {
	ID            string            `json:"id"`
	ActiveSpaceID string            `json:"active_space_id"`
	Spaces        []*DirectorySpace `json:"spaces"`
	CreatedAt     time.Time         `json:"created_at"`
	UpdatedAt     time.Time         `json:"updated_at"`
}

// DirectorySpace represents a single project workspace (a "Tab").
type DirectorySpace struct {
	ID             string           `json:"id"`
	RootPath       string           `json:"root_path"`
	OutputFilePath string           `json:"output_path"`
	Config         ExtractionConfig `json:"config"`
}

// ExtractionConfig controls how the walker and generator behave.
type ExtractionConfig struct {
	IncludePatterns  []string `json:"include_patterns"`
	ExcludePatterns  []string `json:"exclude_patterns"`
	ManualSelections []string `json:"manual_selections"`

	// Options
	IncludeMode   bool `json:"include_mode"`
	FilenamesOnly bool `json:"filenames_only"`
	MinifyContent bool `json:"minify_content"`

	// Visibility Options
	ShowExcluded bool `json:"show_excluded"` // Show EVERYTHING (even node_modules)
	ShowContext  bool `json:"show_context"`  // Show SIBLINGS of selected items
}

// ReportMetadata holds data for the final report header.
type ReportMetadata struct {
	Timestamp     time.Time
	TotalFiles    int
	TotalTokens   int
	SelectionMode string
}

// DirEntry represents a single file/folder for lazy loading.
type DirEntry struct {
	Name     string
	FullPath string
	IsDir    bool
	Size     int64
}
