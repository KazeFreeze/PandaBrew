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

// RunExtraction executes the headless export logic for a specific space.
func RunExtraction(space *DirectorySpace) (meta ReportMetadata, err error) {
	// 0. Validate Space (Prune missing selections)
	sm := NewSessionManager("")
	sm.ValidateSpace(space)

	config := space.Config
	meta = ReportMetadata{
		Timestamp:     time.Now(),
		SelectionMode: "INCLUDE checked items",
	}
	if !config.IncludeMode {
		meta.SelectionMode = "EXCLUDE checked items"
	}

	if err := os.MkdirAll(filepath.Dir(space.OutputFilePath), 0o755); err != nil {
		return meta, fmt.Errorf("failed to create output dir: %w", err)
	}

	outFile, err := os.Create(space.OutputFilePath)
	if err != nil {
		return meta, fmt.Errorf("failed to create output file: %w", err)
	}

	// We wrap the file writer to count bytes automatically
	countingWriter := &TokenCountingWriter{Writer: outFile}

	defer func() {
		if closeErr := outFile.Close(); closeErr != nil && err == nil {
			err = closeErr
		}
	}()

	if err := writeHeader(countingWriter, meta); err != nil {
		return meta, err
	}

	absOutPath, _ := filepath.Abs(space.OutputFilePath)

	if _, err := fmt.Fprintln(countingWriter, "### Project Structure"); err != nil {
		return meta, err
	}
	if _, err := fmt.Fprintln(countingWriter); err != nil {
		return meta, err
	}

	if err := walkAndProcess(space.RootPath, config, countingWriter, true, &meta, absOutPath); err != nil {
		return meta, err
	}
	if _, err := fmt.Fprintln(countingWriter); err != nil {
		return meta, err
	}

	if !config.FilenamesOnly {
		if _, err := fmt.Fprintln(countingWriter, "### File Contents"); err != nil {
			return meta, err
		}
		if _, err := fmt.Fprintln(countingWriter); err != nil {
			return meta, err
		}
		if err := walkAndProcess(space.RootPath, config, countingWriter, false, &meta, absOutPath); err != nil {
			return meta, err
		}
	}

	// Finalize token count from our tracking writer
	meta.TotalTokens = countingWriter.EstimatedTokens
	return meta, nil
}

// TokenCountingWriter is a wrapper that estimates tokens (chars / 4)
type TokenCountingWriter struct {
	Writer          io.Writer
	EstimatedTokens int
}

func (w *TokenCountingWriter) Write(p []byte) (n int, err error) {
	n, err = w.Writer.Write(p)
	// Standard heuristic: ~4 characters per token
	w.EstimatedTokens += n / 4
	return n, err
}

func walkAndProcess(root string, cfg ExtractionConfig, w io.Writer, structOnly bool, meta *ReportMetadata, absOutPath string) error {
	selectionMap := make(map[string]bool, len(cfg.ManualSelections))
	for _, p := range cfg.ManualSelections {
		selectionMap[p] = true
	}

	// Map for expanded folders (Always Show Structure)
	expandedMap := make(map[string]bool, len(cfg.AlwaysShowStructure))
	for _, p := range cfg.AlwaysShowStructure {
		expandedMap[p] = true
	}

	return filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if path == absOutPath {
			return nil
		}

		relPath, _ := filepath.Rel(root, path)
		if relPath == "." {
			if structOnly {
				if _, err := fmt.Fprintln(w, filepath.Base(root)); err != nil {
					return err
				}
			}
			return nil
		}

		// Check exclusion early, BUT we must respect AlwaysShowStructure
		// If the parent is expanded, we show it in structure even if it matches exclude pattern (optionally)
		// For now, we stick to strict exclude unless ShowExcluded is on.
		if isExcluded(relPath, cfg.ExcludePatterns) {
			if cfg.ShowExcluded && structOnly {
				// Continue to print, but mark as excluded
			} else {
				if d.IsDir() {
					return filepath.SkipDir
				}
				return nil
			}
		}

		// 1. Content Selection Logic (Manual + Include/Exclude Mode)
		isSelected := isPathSelected(path, root, selectionMap)
		shouldKeepContent := false
		if cfg.IncludeMode {
			shouldKeepContent = isSelected
		} else {
			shouldKeepContent = !isSelected
		}

		// 2. Context Logic
		isContext := false
		if !shouldKeepContent && cfg.ShowContext {
			parent := filepath.Dir(path)
			if isRelevantDirectory(parent, root, selectionMap) {
				isContext = true
			}
		}

		// 3. Structure Visibility Logic (Expanded Folders)
		// A file/folder is visible in structure if its parent is in the expanded list.
		// The root's immediate children have parent == root.
		isStructureVisible := false
		parent := filepath.Dir(path)

		// If the parent is in the list of "Always Show Structure" (Expanded folders), we show this node.
		if expandedMap[parent] {
			isStructureVisible = true
		}

		// If it's a directory and it IS in the expanded map, it implies it's open, so we render it.
		// If it's a directory and NOT in the map (collapsed), we still render the directory line itself
		// if its parent is expanded.

		// --- DECISION TIME ---

		// Case A: Printing Structure
		if structOnly {
			// We print if:
			// 1. It is selected for content
			// 2. It is context
			// 3. It is visible in the view (StructureVisible)
			// 4. ShowExcluded is on (already handled partially above)

			if shouldKeepContent || isContext || isStructureVisible || cfg.ShowExcluded {
				return printTreeNode(w, relPath, d.IsDir(), shouldKeepContent)
			}
		}

		// Case B: Printing Content
		if !structOnly && !d.IsDir() {
			if shouldKeepContent {
				meta.TotalFiles++
				if err := printFileContent(w, path, relPath); err != nil {
					if _, writeErr := fmt.Fprintf(w, "--- file: %s ---\n[Error reading file: %v]\n---\n\n", relPath, err); writeErr != nil {
						return writeErr
					}
				}
			}
		}

		// Pruning for efficiency
		// If directory is NOT selected, NOT context, NOT expanded, and we are in IncludeMode, we can skip it.
		// However, we must be careful: if a child IS selected deep down, isRelevantDirectory handles that.
		if d.IsDir() {
			// If this folder is not relevant (no selected children), and not expanded, we can skip
			if cfg.IncludeMode && !isRelevantDirectory(path, root, selectionMap) && !expandedMap[path] {
				return filepath.SkipDir
			}
		}

		return nil
	})
}

// Helper functions (Reuse previous implementations)
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
