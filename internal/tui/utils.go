// Package tui implements the terminal user interface logic.
package tui

import (
	"path/filepath"
	"slices"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/lipgloss"
)

func calculateDepth(node *TreeNode, rootPath string) int {
	rootDepth := strings.Count(rootPath, string(filepath.Separator))
	nodeDepth := strings.Count(node.FullPath, string(filepath.Separator))
	depth := nodeDepth - rootDepth
	if depth < 0 {
		return 0
	}
	return depth
}

func CollectExpandedPaths(node *TreeNode) []string {
	var paths []string
	if node == nil {
		return paths
	}

	if node.IsDir && node.Expanded {
		paths = append(paths, node.FullPath)
		for _, child := range node.Children {
			paths = append(paths, CollectExpandedPaths(child)...)
		}
	}
	return paths
}

// getRawFileIcon returns the icon character without any styling
func getRawFileIcon(node *TreeNode) string {
	if node.IsDir {
		if node.Expanded {
			return iconFolderOpen
		}
		return iconFolder
	}

	ext := strings.ToLower(filepath.Ext(node.Name))
	name := strings.ToLower(node.Name)

	switch name {
	case "dockerfile", ".dockerignore":
		return iconDocker
	case ".gitignore", ".gitattributes":
		return iconGit
	case "readme.md", "readme":
		return iconMarkdown
	case "package.json", "tsconfig.json":
		return iconJSON
	}

	switch ext {
	case ".go":
		return iconGo
	case ".md", ".markdown":
		return iconMarkdown
	case ".json":
		return iconJSON
	case ".yaml", ".yml":
		return iconYAML
	case ".js", ".jsx":
		return iconJS
	case ".ts", ".tsx":
		return iconTS
	case ".py":
		return iconPython
	case ".rs":
		return iconRust
	case ".html", ".htm":
		return iconHTML
	case ".css", ".scss", ".sass":
		return iconCSS
	case ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp":
		return iconImage
	case ".zip", ".tar", ".gz", ".rar", ".7z":
		return iconArchive
	case ".toml", ".ini", ".conf", ".config":
		return iconConfig
	case ".txt", ".log":
		return iconText
	default:
		if isCodeFile(ext) {
			return iconCode
		}
		return iconFile
	}
}

// getFileIcon returns the icon character and its style.
// It returns (iconChar, style). The style contains the foreground color.
// The caller is responsible for applying the background color to match the row.
func getFileIcon(node *TreeNode, s Styles) (string, lipgloss.Style) {
	style := lipgloss.NewStyle()

	if node.IsDir {
		if node.Expanded {
			return iconFolderOpen, style.Foreground(s.ColorYellow)
		}
		return iconFolder, style.Foreground(s.ColorBlue)
	}

	ext := strings.ToLower(filepath.Ext(node.Name))
	name := strings.ToLower(node.Name)

	switch name {
	case "dockerfile", ".dockerignore":
		return iconDocker, style.Foreground(s.ColorBlue)
	case ".gitignore", ".gitattributes":
		return iconGit, style.Foreground(s.ColorPeach)
	case "readme.md", "readme":
		return iconMarkdown, style.Foreground(s.ColorGreen)
	case "package.json", "tsconfig.json":
		return iconJSON, style.Foreground(s.ColorYellow)
	}

	switch ext {
	case ".go":
		return iconGo, style.Foreground(s.ColorBlue)
	case ".md", ".markdown":
		return iconMarkdown, style.Foreground(s.ColorGreen)
	case ".json":
		return iconJSON, style.Foreground(s.ColorYellow)
	case ".yaml", ".yml":
		return iconYAML, style.Foreground(s.ColorMauve)
	case ".js", ".jsx":
		return iconJS, style.Foreground(s.ColorYellow)
	case ".ts", ".tsx":
		return iconTS, style.Foreground(s.ColorBlue)
	case ".py":
		return iconPython, style.Foreground(s.ColorBlue)
	case ".rs":
		return iconRust, style.Foreground(s.ColorPeach)
	case ".html", ".htm":
		return iconHTML, style.Foreground(s.ColorPeach)
	case ".css", ".scss", ".sass":
		return iconCSS, style.Foreground(s.ColorBlue)
	case ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp":
		return iconImage, style.Foreground(s.ColorMauve)
	case ".zip", ".tar", ".gz", ".rar", ".7z":
		return iconArchive, style.Foreground(s.ColorRed)
	case ".toml", ".ini", ".conf", ".config":
		return iconConfig, style.Foreground(s.ColorSubtext)
	case ".txt", ".log":
		return iconText, style.Foreground(s.ColorSubtext)
	default:
		if isCodeFile(ext) {
			return iconCode, style.Foreground(s.ColorSubtext)
		}
		return iconFile, style.Foreground(s.ColorSubtext)
	}
}

func isCodeFile(ext string) bool {
	codeExts := []string{
		".c", ".cpp", ".cc", ".h", ".hpp",
		".java", ".kt", ".scala",
		".rb", ".php", ".swift",
		".sh", ".bash", ".zsh",
		".vim", ".lua", ".r",
	}
	return slices.Contains(codeExts, ext)
}

func getSelectionIcon(node *TreeNode, space *core.DirectorySpace, s Styles) (string, lipgloss.Style) {
	style := lipgloss.NewStyle()

	isExact := slices.Contains(space.Config.ManualSelections, node.FullPath)
	if isExact {
		return iconCheckSquare, style.Foreground(s.ColorGreen).Bold(true)
	}

	for _, sVal := range space.Config.ManualSelections {
		if strings.HasPrefix(node.FullPath, sVal+string(filepath.Separator)) {
			return iconDot, style.Foreground(s.ColorGreen)
		}
	}

	if node.IsDir {
		prefix := node.FullPath + string(filepath.Separator)
		for _, sVal := range space.Config.ManualSelections {
			if strings.HasPrefix(sVal, prefix) {
				return iconCircle, style.Foreground(s.ColorYellow)
			}
		}
	}

	return iconSquare, style.Foreground(s.ColorSubtext)
}

func toggleSelection(space *core.DirectorySpace, path string) {
	if path == "" {
		return
	}
	found := false
	for i, existing := range space.Config.ManualSelections {
		if existing == path {
			space.Config.ManualSelections = append(space.Config.ManualSelections[:i], space.Config.ManualSelections[i+1:]...)
			found = true
			break
		}
	}
	if !found {
		space.Config.ManualSelections = append(space.Config.ManualSelections, path)
	}
}

func focusInput(state *TabState, idx int) {
	state.ActiveInput = idx
	blurAll(state)
	switch idx {
	case 1:
		state.InputRoot.Focus()
	case 2:
		state.InputOutput.Focus()
	case 3:
		state.InputInclude.Focus()
	case 4:
		state.InputExclude.Focus()
	}
}

func blurAll(state *TabState) {
	state.InputRoot.Blur()
	state.InputOutput.Blur()
	state.InputInclude.Blur()
	state.InputExclude.Blur()
}

func splitClean(s string) []string {
	if s == "" {
		return []string{}
	}
	parts := strings.Split(s, ",")
	var res []string
	for _, p := range parts {
		t := strings.TrimSpace(p)
		if t != "" {
			res = append(res, t)
		}
	}
	return res
}

func (m *AppModel) populateChildren(state *TabState, parentPath string, entries []core.DirEntry) {
	var targetNode *TreeNode
	var find func(*TreeNode) *TreeNode

	find = func(n *TreeNode) *TreeNode {
		if n.FullPath == parentPath {
			return n
		}
		for _, c := range n.Children {
			if res := find(c); res != nil {
				return res
			}
		}
		return nil
	}

	if state.TreeRoot != nil {
		targetNode = find(state.TreeRoot)
	}
	if targetNode == nil {
		return
	}

	existingState := make(map[string]*TreeNode)
	for _, child := range targetNode.Children {
		existingState[child.FullPath] = child
	}

	var children []*TreeNode
	for _, e := range entries {
		newNode := &TreeNode{
			Name:     e.Name,
			FullPath: e.FullPath,
			IsDir:    e.IsDir,
			Parent:   targetNode,
		}

		if old, ok := existingState[e.FullPath]; ok {
			newNode.Expanded = old.Expanded
			newNode.Children = old.Children
			for _, gc := range newNode.Children {
				gc.Parent = newNode
			}
		}

		children = append(children, newNode)
	}
	targetNode.Children = children
}

func selectAll(space *core.DirectorySpace) {
	space.Config.ManualSelections = []string{space.RootPath}
}

func deselectAll(space *core.DirectorySpace) {
	space.Config.ManualSelections = []string{}
}
