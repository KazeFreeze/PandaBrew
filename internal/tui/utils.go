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

// CollectExpandedPaths traverses the visual tree and returns a list of all
// paths that are currently expanded (open) in the TUI.
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

func getFileIcon(node *TreeNode) string {
	if node.IsDir {
		if node.Expanded {
			return lipgloss.NewStyle().Foreground(colorYellow).Render(iconFolderOpen)
		}
		return lipgloss.NewStyle().Foreground(colorBlue).Render(iconFolder)
	}

	ext := strings.ToLower(filepath.Ext(node.Name))
	name := strings.ToLower(node.Name)

	// Special files
	switch name {
	case "dockerfile", ".dockerignore":
		return lipgloss.NewStyle().Foreground(colorBlue).Render(iconDocker)
	case ".gitignore", ".gitattributes":
		return lipgloss.NewStyle().Foreground(colorOrange).Render(iconGit)
	case "readme.md", "readme":
		return lipgloss.NewStyle().Foreground(colorGreen).Render(iconMarkdown)
	case "package.json", "tsconfig.json":
		return lipgloss.NewStyle().Foreground(colorYellow).Render(iconJSON)
	}

	// By extension
	iconStyle := lipgloss.NewStyle()
	var icon string

	switch ext {
	case ".go":
		icon = iconGo
		iconStyle = iconStyle.Foreground(colorCyan)
	case ".md", ".markdown":
		icon = iconMarkdown
		iconStyle = iconStyle.Foreground(colorGreen)
	case ".json":
		icon = iconJSON
		iconStyle = iconStyle.Foreground(colorYellow)
	case ".yaml", ".yml":
		icon = iconYAML
		iconStyle = iconStyle.Foreground(colorPurple)
	case ".js", ".jsx":
		icon = iconJS
		iconStyle = iconStyle.Foreground(colorYellow)
	case ".ts", ".tsx":
		icon = iconTS
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".py":
		icon = iconPython
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".rs":
		icon = iconRust
		iconStyle = iconStyle.Foreground(colorOrange)
	case ".html", ".htm":
		icon = iconHTML
		iconStyle = iconStyle.Foreground(colorOrange)
	case ".css", ".scss", ".sass":
		icon = iconCSS
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp":
		icon = iconImage
		iconStyle = iconStyle.Foreground(colorPurple)
	case ".zip", ".tar", ".gz", ".rar", ".7z":
		icon = iconArchive
		iconStyle = iconStyle.Foreground(colorRed)
	case ".toml", ".ini", ".conf", ".config":
		icon = iconConfig
		iconStyle = iconStyle.Foreground(colorGray)
	case ".txt", ".log":
		icon = iconText
		iconStyle = iconStyle.Foreground(colorGray)
	default:
		if isCodeFile(ext) {
			icon = iconCode
			iconStyle = iconStyle.Foreground(colorGrayLight)
		} else {
			icon = iconFile
			iconStyle = iconStyle.Foreground(colorGray)
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

func getSelectionIcon(node *TreeNode, space *core.DirectorySpace) (string, lipgloss.Style) {
	style := lipgloss.NewStyle()

	// 1. Exact match
	isExact := slices.Contains(space.Config.ManualSelections, node.FullPath)
	if isExact {
		return iconCheckSquare, style.Foreground(colorGreen).Bold(true)
	}

	// 2. Implicit/Ancestor match (this file/folder is under a selected parent)
	for _, s := range space.Config.ManualSelections {
		if strings.HasPrefix(node.FullPath, s+string(filepath.Separator)) {
			return iconDot, style.Foreground(colorGreen)
		}
	}

	// 3. Partial/Descendant match (some children are selected)
	if node.IsDir {
		prefix := node.FullPath + string(filepath.Separator)
		for _, s := range space.Config.ManualSelections {
			if strings.HasPrefix(s, prefix) {
				return iconCircle, style.Foreground(colorYellow)
			}
		}
	}

	return iconSquare, style.Foreground(colorGray)
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

func enhancedCheckbox(label string, checked bool, hotkey string) string {
	icon := iconSquare
	style := lipgloss.NewStyle().Foreground(colorGray)

	if checked {
		icon = iconCheckSquare
		style = lipgloss.NewStyle().Foreground(colorGreen).Bold(true)
	}

	labelWithKey := fmt.Sprintf("%s %s (%s)", icon, label, hotkey)
	return style.Render(labelWithKey)
}

// populateChildren updates the children of a node based on filesystem scan.
// It preserves the 'Expanded' state and 'Children' (grandchildren) of existing nodes.
func (m *AppModel) populateChildren(state *TabState, parentPath string, entries []core.DirEntry) {
	var targetNode *TreeNode
	var find func(*TreeNode) *TreeNode

	// Recursive finder
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

	// 1. Snapshot existing state to preserve expansions
	existingState := make(map[string]*TreeNode)
	for _, child := range targetNode.Children {
		existingState[child.FullPath] = child
	}

	// 2. Build new children list merging old state
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
			// If it was expanded, it likely had children loaded. Preserve them.
			// Ideally, we might want to refresh them too if this was a recursive refresh,
			// but for a single level scan, we keep what we had unless specifically refreshed.
			newNode.Children = old.Children

			// Fix parent pointers for adopted grandchildren
			for _, gc := range newNode.Children {
				gc.Parent = newNode
			}
		}

		children = append(children, newNode)
	}
	targetNode.Children = children
}
