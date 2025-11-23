// Package main is the entry point for the PandaBrew application.
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"pandabrew/internal/core"
	"pandabrew/internal/tui"

	tea "github.com/charmbracelet/bubbletea"
)

func main() {
	root := flag.String("root", ".", "Root directory to scan")
	headless := flag.Bool("headless", false, "Run in headless mode without TUI")
	output := flag.String("output", "", "Output file for headless mode")
	flag.Parse()

	// 1. Initialize Session Manager
	sm := core.NewSessionManager("")
	session, err := sm.Load()
	if err != nil {
		// Reset on corruption
		session = &core.Session{Spaces: []*core.DirectorySpace{}}
	}

	// 2. Handle "pandabrew ." argument to create/update space
	absRoot, _ := filepath.Abs(*root)
	space, err := sm.AddSpaceFromPath(session, absRoot)
	if err != nil {
		fmt.Printf("Error initializing workspace: %v\n", err)
		os.Exit(1)
	}

	// Override default output if flag provided
	if *output != "" {
		space.OutputFilePath = *output
	}

	// 3. Headless Mode
	if *headless {
		fmt.Printf("Starting headless extraction of %s...\n", space.RootPath)
		meta, err := core.RunExtraction(space)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Done! Processed %d files.\n", meta.TotalFiles)
		return
	}

	// 4. TUI Mode
	p := tea.NewProgram(tui.InitialModel(session), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error: %v", err)
		os.Exit(1)
	}
}
