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

	outFile, err := os.Create(config.OutputFilePath)
	if err != nil {
		return meta, fmt.Errorf("failed to create output file: %w", err)
	}

	// Robust error checking on Close
	defer func() {
		if closeErr := outFile.Close(); closeErr != nil && err == nil {
			err = closeErr
		}
	}()

	if err := writeHeader(outFile, meta); err != nil {
		return meta, err
	}

	// Pass 1: Structure Tree
	if _, err := fmt.Fprintln(outFile, "### Project Structure"); err != nil {
		return meta, err
	}
	if _, err := fmt.Fprintln(outFile); err != nil {
		return meta, err
	}

	if err := walkAndProcess(config, outFile, true, &meta); err != nil {
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
		if err := walkAndProcess(config, outFile, false, &meta); err != nil {
			return meta, err
		}
	}

	return meta, nil
}

func walkAndProcess(cfg ExtractionConfig, w io.Writer, structOnly bool, meta *ReportMetadata) error {
	selectionMap := make(map[string]bool, len(cfg.ManualSelections))
	for _, p := range cfg.ManualSelections {
		selectionMap[p] = true
	}

	return filepath.WalkDir(cfg.RootPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil // Skip inaccessible files
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

		// 2. SMART SKIP: If directory has no selected children, skip it entirely.
		if cfg.IncludeMode && d.IsDir() {
			if !isRelevantDirectory(path, cfg.RootPath, selectionMap) {
				return filepath.SkipDir
			}
		}

		// 3. Selection Check
		isSelected := isPathSelected(path, cfg.RootPath, selectionMap)

		if !isSelected {
			if cfg.IncludeMode && !cfg.ShowExcluded {
				return nil
			}
			if structOnly && cfg.ShowExcluded {
				if err := printTreeNode(w, relPath, d.IsDir(), false); err != nil {
					return err
				}
			}
			return nil
		}

		// 4. Output
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

// isRelevantDirectory checks if directory is selected OR contains selected items
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

// isPathSelected checks if path or any parent is selected
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
		// 1. Check if pattern matches the full relative path (standard glob)
		// e.g. "src/*.txt" or "**/*.txt"
		if matched, _ := doublestar.Match(p, relPath); matched {
			return true
		}

		// 2. Check if pattern matches the directory prefix (e.g. "node_modules")
		// This handles "node_modules" matching "node_modules/foo/bar.js"
		if strings.HasPrefix(relPath, p+"/") || relPath == p {
			return true
		}

		// 3. Filename Match (GitIgnore Style)
		// If pattern has NO slashes (e.g. "*.txt"), match against the filename only.
		// This allows "*.txt" to match "src/foo.txt" without needing "**/*.txt"
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

	// Use forward slashes for output consistency
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
