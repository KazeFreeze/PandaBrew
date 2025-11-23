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
				RootPath:    root,
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
				RootPath:    root,
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
				RootPath:    root,
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
			name: "Filenames Only Mode",
			config: ExtractionConfig{
				RootPath:      root,
				IncludeMode:   true,
				FilenamesOnly: true,
				ManualSelections: []string{
					filepath.Join(root, "src"),
				},
			},
			wantFiles: 0,
			// FIX: In FilenamesOnly mode, we only see the tree structure.
			// "src/main.go" doesn't appear as a single string, but "main.go" does.
			wantContains:    []string{"main.go"},
			wantNotContains: []string{"package main"},
		},
		{
			name: "Show Excluded in Structure",
			config: ExtractionConfig{
				RootPath:     root,
				IncludeMode:  true,
				ShowExcluded: true,
				ManualSelections: []string{
					filepath.Join(root, "src"),
				},
			},
			wantFiles: 3,
			wantContains: []string{
				"README.md [EXCLUDED]",
				"src/main.go",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.config.OutputFilePath = filepath.Join(outputDir, "output.txt")

			meta, err := RunExtraction(tt.config)
			if err != nil {
				t.Fatalf("Extraction failed: %v", err)
			}

			if !tt.config.FilenamesOnly && meta.TotalFiles != tt.wantFiles {
				t.Errorf("File count: got %d, want %d", meta.TotalFiles, tt.wantFiles)
			}

			content, _ := os.ReadFile(tt.config.OutputFilePath)
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
	includeConfig := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: filepath.Join(outputDir, "out_include.txt"),
		IncludeMode:    true,
		ManualSelections: []string{
			filepath.Join(root, "README.md"),
			filepath.Join(root, ".env"),
		},
	}

	// 2. Exclude Mode
	excludeConfig := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: filepath.Join(outputDir, "out_exclude.txt"),
		IncludeMode:    false,
		ManualSelections: []string{
			filepath.Join(root, "src"),
			filepath.Join(root, "node_modules"),
		},
	}

	RunExtraction(includeConfig)
	RunExtraction(excludeConfig)

	out1, _ := os.ReadFile(includeConfig.OutputFilePath)
	out2, _ := os.ReadFile(excludeConfig.OutputFilePath)

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

func BenchmarkExtraction(b *testing.B) {
	root := setupTestDir(b)
	outputDir := b.TempDir()

	config := ExtractionConfig{
		RootPath:       root,
		OutputFilePath: filepath.Join(outputDir, "bench.txt"),
		IncludeMode:    true,
		ManualSelections: []string{
			filepath.Join(root, "src"),
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		if _, err := RunExtraction(config); err != nil {
			b.Fatal(err)
		}
	}
}
