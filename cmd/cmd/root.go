// Package cmd contains the shared Cobra command definition for the application.
package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	"pandabrew/internal/core"
	"pandabrew/internal/tui"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
)

// NewRootCmd creates and returns the root command for the application.
func NewRootCmd(version string) *cobra.Command {
	var root string
	var headless bool
	var output string

	rootCmd := &cobra.Command{
		Use:   "pandabrew [path]",
		Short: "A TUI tool for selective file extraction and project documentation",
		Long: `PandaBrew 🐼☕

A high-performance, headless-first tool to extract codebases into a single
text file for LLM context. Features an interactive TUI with workspace
management and smart file filtering.`,
		Version: version, // This will enable the --version flag
		Run: func(cmd *cobra.Command, args []string) {
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
			if root != "" {
				targetPath = root
			} else if len(args) > 0 {
				// Priority 2: Positional Argument
				targetPath = args[0]
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
				space = session.GetActiveSpace()
				if space == nil && headless {
					fmt.Println("Error: Headless mode requires a root directory (via --root or argument) or an active session.")
					os.Exit(1)
				}
			}

			// Override default output if flag provided (only if space exists)
			if space != nil && output != "" {
				space.OutputFilePath = output
			}

			// 3. Headless Mode
			if headless {
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
		},
	}

	rootCmd.PersistentFlags().StringVar(&root, "root", ".", "Project root directory")
	rootCmd.PersistentFlags().StringVar(&output, "output", "project_extraction.txt", "Output file path")
	rootCmd.PersistentFlags().BoolVar(&headless, "headless", false, "Run in headless mode without TUI")

	return rootCmd
}
