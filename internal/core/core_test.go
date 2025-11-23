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
			wantFiles:       3, // main.go, utils.go, data.txt
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
			name: "Exclude Mode - Inverse Selection",
			config: ExtractionConfig{
				IncludeMode: false, // EXCLUDE MODE
				ManualSelections: []string{
					filepath.Join(root, "src"),
					filepath.Join(root, "node_modules"),
				},
			},
			wantFiles:       2, // README.md, .env
			wantContains:    []string{"README.md", ".env"},
			wantNotContains: []string{"src/main.go", "node_modules"},
		},
		{
			name: "Show Context - Siblings of Selected",
			config: ExtractionConfig{
				IncludeMode: true,
				ShowContext: true,
				// CRITICAL: We must explicitly exclude node_modules, otherwise it
				// appears as a valid sibling context of 'src'.
				ExcludePatterns: []string{"node_modules"},
				ManualSelections: []string{
					filepath.Join(root, "src", "main.go"),
				},
			},
			wantFiles: 1, // Only main.go content
			wantContains: []string{
				"src/main.go",
				"utils.go [EXCLUDED]",  // Sibling of main.go
				"README.md [EXCLUDED]", // Sibling of src folder
			},
			wantNotContains: []string{
				"node_modules", // Should be gone due to ExcludePatterns
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

func TestCrossCheck_IncludeVsExclude(t *testing.T) {
	root := setupTestDir(t)
	outputDir := t.TempDir()

	// 1. Include Mode
	includeSpace := &DirectorySpace{
		RootPath:       root,
		OutputFilePath: filepath.Join(outputDir, "out_include.txt"),
		Config: ExtractionConfig{
			IncludeMode: true,
			ManualSelections: []string{
				filepath.Join(root, "README.md"),
				filepath.Join(root, ".env"),
			},
		},
	}

	// 2. Exclude Mode
	excludeSpace := &DirectorySpace{
		RootPath:       root,
		OutputFilePath: filepath.Join(outputDir, "out_exclude.txt"),
		Config: ExtractionConfig{
			IncludeMode: false,
			ManualSelections: []string{
				filepath.Join(root, "src"),
				filepath.Join(root, "node_modules"),
			},
		},
	}

	if _, err := RunExtraction(includeSpace); err != nil {
		t.Fatal(err)
	}
	if _, err := RunExtraction(excludeSpace); err != nil {
		t.Fatal(err)
	}

	out1, _ := os.ReadFile(includeSpace.OutputFilePath)
	out2, _ := os.ReadFile(excludeSpace.OutputFilePath)

	body1 := extractBody(string(out1))
	body2 := extractBody(string(out2))

	if body1 != body2 {
		t.Errorf("Crosscheck Failed!\nInclude Output:\n%s\n\nExclude Output:\n%s", body1, body2)
	}
}

func extractBody(full string) string {
	parts := strings.SplitAfterN(full, "---\n\n", 2)
	if len(parts) > 1 {
		return parts[1]
	}
	return full
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
