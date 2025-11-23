package core

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// setupTestDir creates a temporary directory with a dummy project structure.
// Returns the root path and a cleanup function.
func setupTestDir(t *testing.T) string {
	t.Helper()
	root := t.TempDir()

	// Define file structure
	files := map[string]string{
		"src/main.go":               "package main\nfunc main() {}",
		"src/utils.go":              "package main\nfunc help() {}",
		"src/data.txt":              "some data",
		"node_modules/pkg/index.js": "console.log('hello')",
		"README.md":                 "# Demo Project",
		".env":                      "SECRET=123",
	}

	for path, content := range files {
		fullPath := filepath.Join(root, path)
		if err := os.MkdirAll(filepath.Dir(fullPath), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(fullPath, []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	return root
}

func TestRunExtraction_RecursiveInclude(t *testing.T) {
	root := setupTestDir(t)
	outputFile := filepath.Join(root, "output.txt")

	// Scenario: User selects 'src' folder. Expects recursive inclusion.
	config := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: outputFile,
		IncludeMode:    true,
		ManualSelections: []string{
			filepath.Join(root, "src"), // Select the folder
		},
	}

	meta, err := RunExtraction(config)
	if err != nil {
		t.Fatalf("RunExtraction failed: %v", err)
	}

	// Verify Metadata
	if meta.TotalFiles != 3 { // main.go, utils.go, data.txt
		t.Errorf("Expected 3 files, got %d", meta.TotalFiles)
	}

	// Verify Content
	contentBytes, err := os.ReadFile(outputFile)
	if err != nil {
		t.Fatal(err)
	}
	content := string(contentBytes)

	// Assertions
	shouldContain := []string{
		"src/main.go",
		"src/utils.go",
		"src/data.txt",
		"package main", // Content check
	}
	shouldNotContain := []string{
		"node_modules",
		"README.md",
		".env",
	}

	for _, s := range shouldContain {
		if !strings.Contains(content, s) {
			t.Errorf("Report missing expected string: %s", s)
		}
	}
	for _, s := range shouldNotContain {
		if strings.Contains(content, s) {
			t.Errorf("Report contained unexpected string: %s", s)
		}
	}
}

func TestRunExtraction_PatternExclusion(t *testing.T) {
	root := setupTestDir(t)
	outputFile := filepath.Join(root, "output.txt")

	// Scenario: Select 'src', but exclude .txt files
	config := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: outputFile,
		IncludeMode:    true,
		ManualSelections: []string{
			filepath.Join(root, "src"),
		},
		ExcludePatterns: []string{"*.txt"},
	}

	meta, _ := RunExtraction(config)

	if meta.TotalFiles != 2 { // main.go, utils.go (data.txt excluded)
		t.Errorf("Expected 2 files, got %d", meta.TotalFiles)
	}

	contentBytes, _ := os.ReadFile(outputFile)
	content := string(contentBytes)

	if strings.Contains(content, "data.txt") {
		t.Error("Pattern exclusion failed: found data.txt")
	}
}

func TestRunExtraction_MixedSelections(t *testing.T) {
	root := setupTestDir(t)
	outputFile := filepath.Join(root, "output.txt")

	// Scenario: Select README.md explicitly, and src/main.go explicitly
	config := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: outputFile,
		IncludeMode:    true,
		ManualSelections: []string{
			filepath.Join(root, "README.md"),
			filepath.Join(root, "src", "main.go"),
		},
	}

	meta, _ := RunExtraction(config)

	if meta.TotalFiles != 2 {
		t.Errorf("Expected 2 files, got %d", meta.TotalFiles)
	}

	contentBytes, _ := os.ReadFile(outputFile)
	content := string(contentBytes)

	// Should include main.go but NOT utils.go (since we selected specific file, not folder)
	if !strings.Contains(content, "src/main.go") {
		t.Error("Missing src/main.go")
	}
	if strings.Contains(content, "src/utils.go") {
		t.Error("Unexpectedly included src/utils.go")
	}
}

func TestSessionSaveLoad(t *testing.T) {
	root := setupTestDir(t)
	sessionFile := filepath.Join(root, "session.json")

	originalConfig := ExtractionConfig{
		RootPath: root,
		ManualSelections: []string{
			filepath.Join(root, "src"),
		},
		IncludePatterns: []string{"*.go"},
	}

	// 1. Save
	if err := SaveSession(originalConfig, sessionFile); err != nil {
		t.Fatalf("SaveSession failed: %v", err)
	}

	// 2. Load
	loadedState, warnings, err := LoadSession(sessionFile)
	if err != nil {
		t.Fatalf("LoadSession failed: %v", err)
	}

	if len(warnings) > 0 {
		t.Errorf("Unexpected warnings during load: %v", warnings)
	}

	if loadedState.LastRootPath != root {
		t.Errorf("Root path mismatch. Got %s, want %s", loadedState.LastRootPath, root)
	}
	if len(loadedState.ManualSelections) != 1 {
		t.Errorf("Selection count mismatch")
	}
}
