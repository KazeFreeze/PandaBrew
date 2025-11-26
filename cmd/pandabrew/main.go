// Package main is the entry point for the PandaBrew application.
package main

import (
	"fmt"
	"os"

	"pandabrew/cmd/cmd"
)

func main() {
	rootCmd := cmd.NewRootCmd()
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
