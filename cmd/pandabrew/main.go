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
	output := flag.String("output", "output.txt", "Output file for headless mode")
	flag.Parse()

	absRoot, err := filepath.Abs(*root)
	if err != nil {
		fmt.Printf("Error resolving root path: %v\n", err)
		os.Exit(1)
	}

	// Headless Mode
	if *headless {
		fmt.Printf("Starting headless extraction of %s...\n", absRoot)
		config := core.ExtractionConfig{
			RootPath:       absRoot,
			OutputFilePath: *output,
			IncludeMode:    true,
			// Note: In real headless mode, you'd load selections from a JSON file arg
		}
		meta, err := core.RunExtraction(config)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Done! Processed %d files.\n", meta.TotalFiles)
		return
	}

	// TUI Mode
	p := tea.NewProgram(tui.InitialModel(absRoot))
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error: %v", err)
		os.Exit(1)
	}
}
