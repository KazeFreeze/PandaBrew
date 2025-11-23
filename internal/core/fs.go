// Package core implements the headless logic for file traversal.
package core

import (
	"os"
	"path/filepath"
	"sort"
)

// ListDir returns the immediate children of a directory.
// Used by the TUI to lazily load folder contents on expansion.
func ListDir(path string) ([]DirEntry, error) {
	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, err
	}

	var results []DirEntry
	for _, e := range entries {
		info, err := e.Info()
		if err != nil {
			continue // Skip inaccessible files
		}
		results = append(results, DirEntry{
			Name:     e.Name(),
			FullPath: filepath.Join(path, e.Name()),
			IsDir:    e.IsDir(),
			Size:     info.Size(),
		})
	}

	// Sort: Directories first, then files. Both alphabetical.
	sort.Slice(results, func(i, j int) bool {
		if results[i].IsDir != results[j].IsDir {
			return results[i].IsDir // Dirs true > Files false
		}
		return results[i].Name < results[j].Name
	})

	return results, nil
}
