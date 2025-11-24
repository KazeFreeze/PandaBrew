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
	// 0. Parse Flags
	root := flag.String("root", "", "Root directory to scan (default: current directory if positional arg provided)")
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

	// 2. Determine Initial Workspace
	var targetPath string

	// Priority 1: Flag
	if *root != "" {
		targetPath = *root
	} else if flag.NArg() > 0 {
		// Priority 2: Positional Argument
		targetPath = flag.Arg(0)
	}

	var space *core.DirectorySpace

	if targetPath != "" {
		// User provided a path -> Open/Add it
		absRoot, _ := filepath.Abs(targetPath)
		space, err = sm.AddSpaceFromPath(session, absRoot)
		if err != nil {
			fmt.Printf("Error initializing workspace: %v\n", err)
			os.Exit(1)
		}
	} else {
		// No path provided -> Just open session
		// If session is empty, we might want to default to current dir OR just open empty (TUI handles empty)
		// But headless mode requires a space.

		space = session.GetActiveSpace()
		if space == nil && *headless {
			fmt.Println("Error: Headless mode requires a root directory (via -root or argument) or an active session.")
			os.Exit(1)
		}

		// If TUI mode and no space, we just proceed. TUI handles empty session.
	}

	// Override default output if flag provided (only if space exists)
	if space != nil && *output != "" {
		space.OutputFilePath = *output
	}

	// 3. Headless Mode
	if *headless {
		if space == nil {
			fmt.Println("Error: Headless mode requires a root directory.")
			os.Exit(1)
		}
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
