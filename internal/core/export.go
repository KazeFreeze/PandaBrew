// Package core implements the report generation logic.
package core

import (
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/bmatcuk/doublestar/v4"
)

// RunExtraction executes the headless export logic.
func RunExtraction(config ExtractionConfig) (meta ReportMetadata, err error) {
	meta = ReportMetadata{
		Timestamp:     time.Now(),
		SelectionMode: "INCLUDE checked items",
	}
	if !config.IncludeMode {
		meta.SelectionMode = "EXCLUDE checked items"
	}

	// Create output file
	outFile, err := os.Create(config.OutputFilePath)
	if err != nil {
		return meta, fmt.Errorf("failed to create output file: %w", err)
	}

	defer func() {
		if closeErr := outFile.Close(); closeErr != nil && err == nil {
			err = closeErr
		}
	}()

	if err := writeHeader(outFile, meta); err != nil {
		return meta, err
	}

	// Get absolute path of output file to prevent self-inclusion
	absOutPath, _ := filepath.Abs(config.OutputFilePath)

	// Pass 1: Structure Tree
	if _, err := fmt.Fprintln(outFile, "### Project Structure"); err != nil {
		return meta, err
	}
	if _, err := fmt.Fprintln(outFile); err != nil {
		return meta, err
	}

	if err := walkAndProcess(config, outFile, true, &meta, absOutPath); err != nil {
		return meta, err
	}
	if _, err := fmt.Fprintln(outFile); err != nil {
		return meta, err
	}

	// Pass 2: Content
	if !config.FilenamesOnly {
		if _, err := fmt.Fprintln(outFile, "### File Contents"); err != nil {
			return meta, err
		}
		if _, err := fmt.Fprintln(outFile); err != nil {
			return meta, err
		}
		if err := walkAndProcess(config, outFile, false, &meta, absOutPath); err != nil {
			return meta, err
		}
	}

	return meta, nil
}

func walkAndProcess(cfg ExtractionConfig, w io.Writer, structOnly bool, meta *ReportMetadata, absOutPath string) error {
	selectionMap := make(map[string]bool, len(cfg.ManualSelections))
	for _, p := range cfg.ManualSelections {
		selectionMap[p] = true
	}

	return filepath.WalkDir(cfg.RootPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil // Skip inaccessible files
		}

		// Prevent self-inclusion (reading the report being written)
		if path == absOutPath {
			return nil
		}

		relPath, _ := filepath.Rel(cfg.RootPath, path)
		if relPath == "." {
			if structOnly {
				if _, err := fmt.Fprintln(w, filepath.Base(cfg.RootPath)); err != nil {
					return err
				}
			}
			return nil
		}

		// 1. Global Excludes
		if isExcluded(relPath, cfg.ExcludePatterns) {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		// 2. Selection Check
		// Check if this path (or parent) matches the manual list
		matchesSelection := isPathSelected(path, cfg.RootPath, selectionMap)

		// Determine if we should KEEP this file based on mode
		shouldKeep := false
		if cfg.IncludeMode {
			shouldKeep = matchesSelection
		} else {
			// Exclude Mode: Keep if it DOES NOT match selection
			shouldKeep = !matchesSelection
		}

		// 3. Handling Skipped Items
		if !shouldKeep {
			// Optimization: In Include Mode, if a directory has no selected children, skip it.
			if cfg.IncludeMode && d.IsDir() {
				if !isRelevantDirectory(path, cfg.RootPath, selectionMap) {
					return filepath.SkipDir
				}
			}

			// Show [EXCLUDED] in tree if requested
			if structOnly && cfg.ShowExcluded {
				if err := printTreeNode(w, relPath, d.IsDir(), false); err != nil {
					return err
				}
			}
			return nil
		}

		// 4. Output (File is kept)
		if structOnly {
			if err := printTreeNode(w, relPath, d.IsDir(), true); err != nil {
				return err
			}
		} else if !d.IsDir() {
			meta.TotalFiles++
			if err := printFileContent(w, path, relPath); err != nil {
				if _, writeErr := fmt.Fprintf(w, "--- file: %s ---\n[Error reading file: %v]\n---\n\n", relPath, err); writeErr != nil {
					return writeErr
				}
			}
		}

		return nil
	})
}

// Reuse existing helper functions...
func isRelevantDirectory(currentPath, root string, selections map[string]bool) bool {
	if isPathSelected(currentPath, root, selections) {
		return true
	}
	prefix := currentPath + string(os.PathSeparator)
	for sel := range selections {
		if strings.HasPrefix(sel, prefix) {
			return true
		}
	}
	return false
}

func isPathSelected(path, root string, selections map[string]bool) bool {
	if selections[path] {
		return true
	}
	current := filepath.Dir(path)
	for strings.HasPrefix(current, root) {
		if selections[current] {
			return true
		}
		if current == root || current == "." || current == "/" {
			break
		}
		current = filepath.Dir(current)
	}
	return false
}

func isExcluded(relPath string, patterns []string) bool {
	for _, p := range patterns {
		if matched, _ := doublestar.Match(p, relPath); matched {
			return true
		}
		if strings.HasPrefix(relPath, p+"/") || relPath == p {
			return true
		}
		if !strings.Contains(p, "/") {
			if matched, _ := doublestar.Match(p, filepath.Base(relPath)); matched {
				return true
			}
		}
	}
	return false
}

func writeHeader(w io.Writer, meta ReportMetadata) error {
	if _, err := fmt.Fprintln(w, "--- Project Extraction Report ---"); err != nil {
		return err
	}
	if _, err := fmt.Fprintf(w, "Timestamp: %s\n", meta.Timestamp.Format(time.RFC3339)); err != nil {
		return err
	}
	if _, err := fmt.Fprintf(w, "Selection Mode: %s\n", meta.SelectionMode); err != nil {
		return err
	}
	if _, err := fmt.Fprintln(w, "---"); err != nil {
		return err
	}
	if _, err := fmt.Fprintln(w); err != nil {
		return err
	}
	return nil
}

func printTreeNode(w io.Writer, relPath string, isDir, isSelected bool) error {
	depth := strings.Count(relPath, string(os.PathSeparator))
	indent := strings.Repeat("│   ", depth)
	marker := ""
	if !isSelected {
		marker = " [EXCLUDED]"
	}
	name := filepath.Base(relPath)
	if isDir {
		name += "/"
	}
	_, err := fmt.Fprintf(w, "%s├── %s%s\n", indent, name, marker)
	return err
}

func printFileContent(w io.Writer, fullPath, relPath string) error {
	content, err := os.ReadFile(fullPath)
	if err != nil {
		return err
	}
	displayPath := filepath.ToSlash(relPath)
	if _, err := fmt.Fprintf(w, "--- file: %s ---\n", displayPath); err != nil {
		return err
	}
	if _, err := w.Write(content); err != nil {
		return err
	}
	if _, err := fmt.Fprintln(w, "\n---"); err != nil {
		return err
	}
	if _, err := fmt.Fprintln(w); err != nil {
		return err
	}
	return nil
}
