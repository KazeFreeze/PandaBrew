// Package core handles application state persistence.
package core

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const (
	DefaultSessionFile = "pandabrew_session.json"
)

// SessionManager handles loading, saving, and modifying the global session.
type SessionManager struct {
	FilePath string
}

// NewSessionManager creates a manager pointing to a specific file.
func NewSessionManager(path string) *SessionManager {
	if path == "" {
		path = DefaultSessionFile
	}
	return &SessionManager{FilePath: path}
}

// Load reads the session from disk. If not found, returns a fresh session.
func (sm *SessionManager) Load() (*Session, error) {
	data, err := os.ReadFile(sm.FilePath)
	if os.IsNotExist(err) {
		return &Session{
			ID:        "default",
			Spaces:    []*DirectorySpace{},
			CreatedAt: time.Now(),
		}, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to read session file: %w", err)
	}

	var session Session
	if err := json.Unmarshal(data, &session); err != nil {
		return nil, fmt.Errorf("corrupt session file: %w", err)
	}
	return &session, nil
}

// Save persists the session to disk.
func (sm *SessionManager) Save(s *Session) error {
	s.UpdatedAt = time.Now()
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(sm.FilePath, data, 0o644)
}

// AddSpaceFromPath creates a new DirectorySpace for the given path.
func (sm *SessionManager) AddSpaceFromPath(s *Session, rawPath string) (*DirectorySpace, error) {
	absPath, err := filepath.Abs(rawPath)
	if err != nil {
		return nil, err
	}

	// 1. Check existence
	info, err := os.Stat(absPath)
	if os.IsNotExist(err) {
		return nil, fmt.Errorf("directory does not exist: %s", absPath)
	}
	if !info.IsDir() {
		return nil, fmt.Errorf("path is not a directory: %s", absPath)
	}

	// 2. Check for duplicates (update active if exists)
	id := generateID(absPath)
	for _, space := range s.Spaces {
		if space.ID == id {
			s.ActiveSpaceID = id
			return space, nil
		}
	}

	// 3. Create Smart Default Output Path
	parentDir := filepath.Dir(absPath)
	dirName := filepath.Base(absPath)
	defaultOutput := filepath.Join(parentDir, dirName+".txt")

	newSpace := &DirectorySpace{
		ID:             id,
		RootPath:       absPath,
		OutputFilePath: defaultOutput,
		Config: ExtractionConfig{
			IncludeMode:      true,
			IncludePatterns:  []string{},
			ExcludePatterns:  []string{".git", "node_modules", "__pycache__", "vendor"},
			ManualSelections: []string{},
		},
	}

	s.Spaces = append(s.Spaces, newSpace)
	s.ActiveSpaceID = newSpace.ID
	return newSpace, nil
}

// ValidateSpace checks if the RootPath and Selections still exist.
func (sm *SessionManager) ValidateSpace(space *DirectorySpace) []string {
	var warnings []string

	// 1. Validate Root
	if _, err := os.Stat(space.RootPath); os.IsNotExist(err) {
		return []string{fmt.Sprintf("CRITICAL: Root path missing: %s", space.RootPath)}
	}

	// 2. Validate Selections (prune missing ones)
	var validSelections []string
	for _, sel := range space.Config.ManualSelections {
		if _, err := os.Stat(sel); err == nil {
			validSelections = append(validSelections, sel)
		} else {
			warnings = append(warnings, fmt.Sprintf("Removed missing selection: %s", filepath.Base(sel)))
		}
	}

	space.Config.ManualSelections = validSelections
	return warnings
}

// GetActiveSpace returns the currently selected workspace.
func (s *Session) GetActiveSpace() *DirectorySpace {
	if len(s.Spaces) == 0 {
		return nil
	}
	for _, space := range s.Spaces {
		if space.ID == s.ActiveSpaceID {
			return space
		}
	}
	return s.Spaces[0]
}

func generateID(path string) string {
	h := sha256.New()
	h.Write([]byte(path))
	return hex.EncodeToString(h.Sum(nil))[:12]
}
