// Package core implements the headless logic for file traversal,
// filtering, and report generation.
package core

import (
	"time"
)

// ExtractionConfig controls how the walker and generator behave.
type ExtractionConfig struct {
	RootPath         string
	OutputFilePath   string
	IncludePatterns  []string // Glob patterns to include (e.g., "*.py")
	ExcludePatterns  []string // Glob patterns to exclude (e.g., ".git", "__pycache__")
	ManualSelections []string // Specific paths selected by the user

	// Options
	IncludeMode   bool // If true, only explicit selections/patterns are included
	FilenamesOnly bool // If true, do not dump file content
	MinifyContent bool // If true, strips comments/whitespace to save tokens
	ShowExcluded  bool // If true, shows [EXCLUDED] in the tree
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
