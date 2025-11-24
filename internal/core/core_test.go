package core

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func setupTestDir(t testing.TB) string {
	t.Helper()
	root := t.TempDir()

	files := map[string]string{
		"src/main.go":               "package main",
		"src/utils.go":              "package main",
		"src/data.txt":              "some data",
		"src/lib/helper.go":         "package lib",
		"node_modules/pkg/index.js": "console.log",
		"README.md":                 "# Readme",
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

func TestExtractionScenarios(t *testing.T) {
	root := setupTestDir(t)
	outputDir := t.TempDir()

	tests := []struct {
		name            string
		config          ExtractionConfig
		wantFiles       int
		wantContains    []string
		wantNotContains []string
	}{
		{
			name: "Include Mode - Recursive Folder",
			config: ExtractionConfig{
				IncludeMode: true,
				ManualSelections: []string{
					filepath.Join(root, "src"),
				},
			},
			wantFiles:       4, // main.go, utils.go, data.txt, lib/helper.go
			wantContains:    []string{"src/main.go", "src/utils.go"},
			wantNotContains: []string{"README.md", "node_modules"},
		},
		{
			name: "Include Mode - Single File",
			config: ExtractionConfig{
				IncludeMode: true,
				ManualSelections: []string{
					filepath.Join(root, "README.md"),
				},
			},
			wantFiles:       1,
			wantContains:    []string{"README.md"},
			wantNotContains: []string{"src/main.go"},
		},
		{
			name: "View Structure Mode - Expanded Folders",
			config: ExtractionConfig{
				IncludeMode: true,
				ManualSelections: []string{
					filepath.Join(root, "src", "main.go"), // Only Content for main.go
				},
				AlwaysShowStructure: []string{
					root,
					filepath.Join(root, "src"), // src is expanded
					// src/lib is NOT expanded
				},
			},
			wantFiles: 1, // Only content for src/main.go
			wantContains: []string{
				"src/main.go",
				// Adjusted expectations: The structure tree prints indented names, not full paths.
				// utils.go is a sibling of main.go, inside src/. src/ is expanded.
				"utils.go [EXCLUDED]",
				// lib/ is a child of src/. src/ is expanded.
				"lib/ [EXCLUDED]",
			},
			wantNotContains: []string{
				"src/lib/helper.go", // Child of collapsed folder, should NOT be visible
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			space := &DirectorySpace{
				ID:             "test-space",
				RootPath:       root,
				OutputFilePath: filepath.Join(outputDir, "output_"+strings.ReplaceAll(tt.name, " ", "_")+".txt"),
				Config:         tt.config,
			}

			meta, err := RunExtraction(space)
			if err != nil {
				t.Fatalf("Extraction failed: %v", err)
			}

			if !tt.config.FilenamesOnly && meta.TotalFiles != tt.wantFiles {
				t.Errorf("File count: got %d, want %d", meta.TotalFiles, tt.wantFiles)
			}

			content, _ := os.ReadFile(space.OutputFilePath)
			strContent := string(content)

			for _, s := range tt.wantContains {
				s = filepath.ToSlash(s)
				if !strings.Contains(strContent, s) {
					t.Errorf("Missing expected string: %s", s)
				}
			}

			for _, s := range tt.wantNotContains {
				s = filepath.ToSlash(s)
				if strings.Contains(strContent, s) {
					t.Errorf("Unexpected string found: %s", s)
				}
			}
		})
	}
}

func TestSessionManager(t *testing.T) {
	tmpDir := t.TempDir()
	sm := NewSessionManager(filepath.Join(tmpDir, "session.json"))

	session, err := sm.Load()
	if err != nil {
		t.Fatal(err)
	}

	root := setupTestDir(t)
	space, err := sm.AddSpaceFromPath(session, root)
	if err != nil {
		t.Fatal(err)
	}

	if session.ActiveSpaceID != space.ID {
		t.Error("Active space not updated")
	}

	if err := sm.Save(session); err != nil {
		t.Fatal(err)
	}

	session2, _ := sm.Load()
	if len(session2.Spaces) != 1 {
		t.Error("Session persistence failed")
	}
}
