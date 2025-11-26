// Package main is the entry point for the PandaBrew application.
package main

import (
	"fmt"
	"os"

	"pandabrew/cmd/cmd"
)

// version is the application version. It is set at build time using ldflags.
var version = "dev" // default value

func main() {
	rootCmd := cmd.NewRootCmd(version)
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
