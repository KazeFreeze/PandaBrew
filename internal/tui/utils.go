// Package tui implements the terminal user interface logic.
package tui

import (
	"fmt"
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

// getFileIcon returns the rendered icon using the provided Styles
func getFileIcon(node *TreeNode, s Styles) string {
	if node.IsDir {
		if node.Expanded {
			return lipgloss.NewStyle().Foreground(s.ColorYellow).Render(iconFolderOpen)
		}
		return lipgloss.NewStyle().Foreground(s.ColorBlue).Render(iconFolder)
	}

	ext := strings.ToLower(filepath.Ext(node.Name))
	name := strings.ToLower(node.Name)

	switch name {
	case "dockerfile", ".dockerignore":
		return lipgloss.NewStyle().Foreground(s.ColorBlue).Render(iconDocker)
	case ".gitignore", ".gitattributes":
		return lipgloss.NewStyle().Foreground(s.ColorPeach).Render(iconGit)
	case "readme.md", "readme":
		return lipgloss.NewStyle().Foreground(s.ColorGreen).Render(iconMarkdown)
	case "package.json", "tsconfig.json":
		return lipgloss.NewStyle().Foreground(s.ColorYellow).Render(iconJSON)
	}

	iconStyle := lipgloss.NewStyle()
	var icon string

	switch ext {
	case ".go":
		icon = iconGo
		iconStyle = iconStyle.Foreground(s.ColorBlue)
	case ".md", ".markdown":
		icon = iconMarkdown
		iconStyle = iconStyle.Foreground(s.ColorGreen)
	case ".json":
		icon = iconJSON
		iconStyle = iconStyle.Foreground(s.ColorYellow)
	case ".yaml", ".yml":
		icon = iconYAML
		iconStyle = iconStyle.Foreground(s.ColorMauve)
	case ".js", ".jsx":
		icon = iconJS
		iconStyle = iconStyle.Foreground(s.ColorYellow)
	case ".ts", ".tsx":
		icon = iconTS
		iconStyle = iconStyle.Foreground(s.ColorBlue)
	case ".py":
		icon = iconPython
		iconStyle = iconStyle.Foreground(s.ColorBlue)
	case ".rs":
		icon = iconRust
		iconStyle = iconStyle.Foreground(s.ColorPeach)
	case ".html", ".htm":
		icon = iconHTML
		iconStyle = iconStyle.Foreground(s.ColorPeach)
	case ".css", ".scss", ".sass":
		icon = iconCSS
		iconStyle = iconStyle.Foreground(s.ColorBlue)
	case ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp":
		icon = iconImage
		iconStyle = iconStyle.Foreground(s.ColorMauve)
	case ".zip", ".tar", ".gz", ".rar", ".7z":
		icon = iconArchive
		iconStyle = iconStyle.Foreground(s.ColorRed)
	case ".toml", ".ini", ".conf", ".config":
		icon = iconConfig
		iconStyle = iconStyle.Foreground(s.ColorSubtext)
	case ".txt", ".log":
		icon = iconText
		iconStyle = iconStyle.Foreground(s.ColorSubtext)
	default:
		if isCodeFile(ext) {
			icon = iconCode
			iconStyle = iconStyle.Foreground(s.ColorSubtext)
		} else {
			icon = iconFile
			iconStyle = iconStyle.Foreground(s.ColorSubtext)
		}
	}

	return iconStyle.Render(icon)
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

func enhancedCheckbox(label string, checked bool, hotkey string, s Styles) string {
	icon := iconSquare
	style := lipgloss.NewStyle().Foreground(s.ColorSubtext)

	if checked {
		icon = iconCheckSquare
		style = lipgloss.NewStyle().Foreground(s.ColorGreen).Bold(true)
	}

	labelWithKey := fmt.Sprintf("%s %s (%s)", icon, label, hotkey)
	return style.Render(labelWithKey)
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
