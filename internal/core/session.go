// Package core handles application state persistence.
package core

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const (
	// DefaultSessionFilename is just the name, path determines where it lives
	DefaultSessionFilename = "pandabrew_session.json"
)

// SessionManager handles loading, saving, and modifying the global session.
type SessionManager struct {
	FilePath string
}

// NewSessionManager creates a manager pointing to the system-wide config.
// If path is provided, it overrides the default logic.
func NewSessionManager(path string) *SessionManager {
	if path == "" {
		configDir, err := os.UserConfigDir()
		if err != nil {
			// Fallback to local file if user config dir is unavailable
			path = DefaultSessionFilename
		} else {
			// e.g. ~/.config/pandabrew/session.json
			appDir := filepath.Join(configDir, "pandabrew")
			// Ensure directory exists (best effort)
			_ = os.MkdirAll(appDir, 0o755)
			path = filepath.Join(appDir, DefaultSessionFilename)
		}
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
			Theme:     "mocha", // Default theme
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

	// Validate and clean loaded spaces
	for _, space := range session.Spaces {
		sm.ValidateSpace(space)
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

	// 2. Create New Space (Always unique)
	id := generateRandomID()

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
			StructureView:    false, // Default off
			ShowExcluded:     false, // Default off (explicit)
		},
	}

	s.Spaces = append(s.Spaces, newSpace)
	s.ActiveSpaceID = newSpace.ID

	// Auto-save
	_ = sm.Save(s)

	return newSpace, nil
}

// RemoveSpace removes a space by ID and adjusts the active space if needed.
func (sm *SessionManager) RemoveSpace(s *Session, spaceID string) error {
	if len(s.Spaces) <= 1 {
		return fmt.Errorf("cannot close the last tab")
	}

	idx := -1
	for i, space := range s.Spaces {
		if space.ID == spaceID {
			idx = i
			break
		}
	}

	if idx == -1 {
		return fmt.Errorf("space not found")
	}

	s.Spaces = append(s.Spaces[:idx], s.Spaces[idx+1:]...)

	if s.ActiveSpaceID == spaceID {
		if idx > 0 {
			s.ActiveSpaceID = s.Spaces[idx-1].ID
		} else {
			s.ActiveSpaceID = s.Spaces[0].ID
		}
	}

	_ = sm.Save(s)
	return nil
}

// ValidateSpace checks if the RootPath exists and cleans selections.
func (sm *SessionManager) ValidateSpace(space *DirectorySpace) []string {
	var warnings []string

	// 1. Validate Root
	if _, err := os.Stat(space.RootPath); os.IsNotExist(err) {
		warnings = append(warnings, fmt.Sprintf("CRITICAL: Root path missing: %s", space.RootPath))
	}

	// 2. Validate & Clean Selections
	var validSelections []string
	seen := make(map[string]bool)

	for _, sel := range space.Config.ManualSelections {
		if sel == "" {
			continue
		}
		if seen[sel] {
			continue
		}
		if _, err := os.Stat(sel); os.IsNotExist(err) {
			continue
		}

		validSelections = append(validSelections, sel)
		seen[sel] = true
	}
	space.Config.ManualSelections = validSelections

	// 3. Validate Expanded Paths
	var validExpanded []string
	seenExpanded := make(map[string]bool)
	for _, p := range space.ExpandedPaths {
		if p == "" || seenExpanded[p] {
			continue
		}
		if _, err := os.Stat(p); err == nil {
			validExpanded = append(validExpanded, p)
			seenExpanded[p] = true
		}
	}
	space.ExpandedPaths = validExpanded

	// 4. Validate Cursor Path
	if space.CursorPath != "" {
		if _, err := os.Stat(space.CursorPath); os.IsNotExist(err) {
			space.CursorPath = ""
		}
	}

	return warnings
}

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

func generateRandomID() string {
	bytes := make([]byte, 6)
	if _, err := rand.Read(bytes); err != nil {
		return fmt.Sprintf("%x", time.Now().UnixNano())
	}
	return hex.EncodeToString(bytes)
}
